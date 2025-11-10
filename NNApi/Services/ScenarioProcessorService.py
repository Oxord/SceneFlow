import pika
import json
import requests
import os
import logging
import time
import io
from urllib.parse import urlparse

from NNApi.Configurtaion.ConfigManager import ConfigManager
from NNApi.Services.DocumentProcessor import DocumentProcessor

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScenarioProcessorService:
    """
    Микросервис-consumer для RabbitMQ, который скачивает файлы по URL,
    обрабатывает их на сцены с помощью LLM и логирует результаты.
    """

    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.rabbitmq_host = self.config.get("RabbitMQ", "Host")
        self.rabbitmq_port = self.config.get("RabbitMQ", "Port")
        self.queue_name = self.config.get("RabbitMQ", "QueueName")
        self.rabbitmq_username = self.config.get("RabbitMQ", "Username")
        self.rabbitmq_password = self.config.get("RabbitMQ", "Password")
        self.rabbitmq_vhost = self.config.get("RabbitMQ", "VirtualHost")
        if self.rabbitmq_vhost is None:
            logger.warning("RabbitMQ.VirtualHost not found in config, using default '/'")
            self.rabbitmq_vhost = "/"

        # Параметры Ollama

        ollama_host_from_config = self.config.get("Ollama", "Host")
        self.ollama_host = ollama_host_from_config if ollama_host_from_config is not None else "http://localhost:11434"
        self.ollama_model_name = self.config.get("Ollama", "ModelName")

        # Параметры скачивания
        self.download_timeout = self.config.get("FileDownload", "TimeoutSeconds")
        self.download_chunk_size = self.config.get("FileDownload", "ChunkSizeKB") * 1024  # Конвертируем KB в байты

        if not all([self.rabbitmq_host, self.rabbitmq_port, self.queue_name,
                    self.rabbitmq_username, self.rabbitmq_password, self.rabbitmq_vhost,
                    self.ollama_model_name]):
            raise ValueError(
                "Missing critical configuration parameters. Check appsettings.json for RabbitMQ and Ollama.")

        self.connection = None
        self.channel = None

        # Инициализируем DocumentProcessor
        self.document_processor = DocumentProcessor(self.ollama_model_name, self.ollama_host)

        logger.info(f"ScenarioProcessorService initialized. Queue: '{self.queue_name}'")
        logger.debug(f"Full config: {self.config.get_all()}")

    def _connect_to_rabbitmq(self):
        """Устанавливает соединение с RabbitMQ."""
        while True:
            try:
                logger.info(f"Attempting to connect to RabbitMQ at {self.rabbitmq_host}:{self.rabbitmq_port}...")
                credentials = pika.PlainCredentials(self.rabbitmq_username, self.rabbitmq_password)
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.rabbitmq_host,
                        port=self.rabbitmq_port,
                        credentials=credentials,
                        virtual_host=self.rabbitmq_vhost
                    )
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(
                    queue=self.queue_name,
                    durable=True,
                    arguments={'x-queue-type': 'quorum'}
                )
                logger.info("Successfully connected to RabbitMQ and declared queue.")
                break
            except pika.exceptions.AMQPConnectionError as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}. Retrying in 5 seconds...")
                time.sleep(5)
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred while connecting to RabbitMQ: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    def _fetch_file_content_in_memory(self, url: str, correlation_id: str) -> bytes | None:
        """
        Скачивает файл по заданному URL и возвращает его содержимое в виде байтов.
        Не сохраняет файл на диск.
        """
        try:
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                logger.error(f"Invalid URL '{url}' (CorrelationId: {correlation_id})")
                return None
            logger.info(f"Fetching content from '{url}' (CorrelationId: {correlation_id})")

            # Используем stream=True для обработки больших файлов без загрузки всего в память сразу
            with requests.get(url, stream=True, timeout=self.download_timeout) as r:
                r.raise_for_status()  # Вызовет исключение для ошибок HTTP (4xx, 5xx)

                # Собираем чанки в BytesIO буфер
                buffer = io.BytesIO()
                for chunk in r.iter_content(chunk_size=self.download_chunk_size):
                    if chunk:
                        buffer.write(chunk)

                logger.info(
                    f"Successfully fetched content from '{url}' (CorrelationId: {correlation_id}). Size: {buffer.tell()} bytes.")
                return buffer.getvalue()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching file from '{url}': {e} (CorrelationId: {correlation_id})")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during file fetch: {e} (CorrelationId: {correlation_id})")
            return None

    def _on_message_callback(self, ch, method, properties, body):
        """
        Коллбэк-функция, вызываемая при получении нового сообщения.
        """
        logger.info(f"Received message with delivery tag: {method.delivery_tag}")
        correlation_id = "N/A"
        try:
            message_data = json.loads(body)
            file_name = message_data.get("FileName")
            storage_url = message_data.get("StorageUrl")

            # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
            # Пытаемся получить FileType из сообщения, но если его нет,
            # пытаемся извлечь его из FileName.
            explicit_file_type = message_data.get("FileType")  # Теперь это необязательно

            if explicit_file_type:
                file_type = explicit_file_type.lower()
                logger.debug(f"FileType explicitly provided: {file_type}")
            elif file_name:
                # Извлекаем расширение файла и используем его как file_type
                # Например, "my_scenario.docx" -> "docx"
                # "my_document.pdf" -> "pdf"
                _, ext = os.path.splitext(file_name)
                file_type = ext.lstrip('.').lower()  # Удаляем точку и приводим к нижнему регистру
                logger.debug(f"FileType inferred from FileName: {file_type}")
            else:
                file_type = None  # Не удалось определить тип файла

            correlation_id = message_data.get("CorrelationId", "N/A")

            logger.info(f"Processing CorrelationId: {correlation_id}")

            # Теперь проверка будет только для FileName и StorageUrl
            if not all([file_name, storage_url]):
                logger.error(f"Message missing 'FileName' or 'StorageUrl'. Body: {body.decode()}")
                ch.basic_ack(method.delivery_tag)
                return

            # Проверяем, удалось ли определить поддерживаемый тип файла
            if file_type not in ["docx", "pdf"]:
                logger.error(
                    f"Unsupported or undeterminable FileType '{file_type}' for '{file_name}' (CorrelationId: {correlation_id}). Message will be acknowledged.")
                ch.basic_ack(method.delivery_tag)
                return

            # 1. Скачиваем содержимое файла в память
            file_content_bytes = self._fetch_file_content_in_memory(storage_url, correlation_id)

            if file_content_bytes is None:
                logger.warning(
                    f"Failed to fetch content for '{file_name}' (CorrelationId: {correlation_id}). Message will be re-queued.")
                ch.basic_nack(method.delivery_tag, requeue=True)
                return

            # 2. Обрабатываем документ с помощью DocumentProcessor
            logger.info(
                f"Starting scene processing for '{file_name}' (FileType: {file_type}, CorrelationId: {correlation_id})...")
            processed_scenes = self.document_processor.process_document(file_content_bytes, file_type)

            if processed_scenes:
                logger.info(
                    f"Successfully processed {len(processed_scenes)} scenes for '{file_name}' (CorrelationId: {correlation_id}). Displaying results:")

                for scene in processed_scenes:
                    # Используем INFO, чтобы сообщения всегда были видны
                    logger.info(f"--- Parsed Scene [{scene.scene_id}] ---")

                    # --- Этап 1: Вывод базовой информации ---
                    logger.info("  --- Basic Info ---")
                    metadata = scene.metadata or {}
                    logger.info(f"    Номер сцены: {metadata.get('scene_number', 'N/A')}")
                    logger.info(f"    Место и время: {metadata.get('setting', 'N/A')}")
                    logger.info(f"    Персонажи: {metadata.get('characters_present', [])}")
                    logger.info(f"    Ключевые события: {metadata.get('key_events_summary', 'N/A')}")

                    # --- Этап 2: Вывод производственных деталей ---
                    logger.info("  --- Production Details ---")
                    if scene.production_data:
                        logger.info(f"    Костюм: {scene.production_data.costume}")
                        logger.info(f"    Грим/Прически: {scene.production_data.makeup_and_hair}")
                        logger.info(f"    Реквизит: {scene.production_data.props}")
                        logger.info(f"    Массовка: {scene.production_data.extras}")
                        logger.info(f"    Трюки: {scene.production_data.stunts}")
                        logger.info(f"    Спецэффекты: {scene.production_data.special_effects}")
                    else:
                        logger.info("    (Производственные детали не были сгенерированы)")

                    logger.info("------------------------------------")
            else:
                logger.warning(f"No scenes processed for '{file_name}' (CorrelationId: {correlation_id}).")

                # Подтверждаем обработку сообщения
            ch.basic_ack(method.delivery_tag)

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from message. Body: {body.decode()}")
            ch.basic_ack(method.delivery_tag)
        except ValueError as e:
            logger.error(
                f"Configuration or processing error: {e} (CorrelationId: {correlation_id}). Acknowledging message.")
            ch.basic_ack(method.delivery_tag)
        except Exception as e:
            logger.error(
                f"An unhandled error occurred during message processing for CorrelationId: {correlation_id}: {e}. Re-queueing message.")
            ch.basic_nack(method.delivery_tag, requeue=True)

    def start_consuming(self):
        """
        Запускает процесс прослушивания очереди RabbitMQ.
        Это блокирующая операция.
        """
        self._connect_to_rabbitmq()
        logger.info(f"Starting to consume messages from queue '{self.queue_name}'. To exit, press CTRL+C")
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self._on_message_callback,
            auto_ack=False
        )
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Consumer interrupted. Stopping...")
            self.stop_consuming()
        except Exception as e:
            logger.error(f"An error occurred during consumption: {e}")
            self.stop_consuming()

    def stop_consuming(self):
        """
        Останавливает процесс прослушивания и закрывает соединение.
        """
        if self.channel and self.channel.is_open:
            self.channel.stop_consuming()
            logger.info("Channel consumption stopped.")
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info("RabbitMQ connection closed.")


if __name__ == "__main__":
    try:
        config_manager = ConfigManager(config_file="appsettings.json")

        # Для демонстрации, если ConfigManager еще не создан
        consumer_service = ScenarioProcessorService(config_manager=config_manager)
        consumer_service.start_consuming()
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"Service startup failed due to configuration error: {e}")
    except Exception as e:
        logger.critical(f"An unhandled error occurred during service startup: {e}", exc_info=True)
