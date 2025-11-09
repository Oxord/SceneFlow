import pika
import json
import requests
import os
import logging
import time
from urllib.parse import urlparse

from NNApi.Configurtaion.ConfigManager import ConfigManager

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FileDownloaderService:
    """
    Микросервис-consumer для RabbitMQ, который скачивает файлы по URL из сообщений.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Инициализирует сервис.
        :param rabbitmq_host: Хост RabbitMQ (например, 'localhost').
        :param queue_name: Имя очереди, которую нужно слушать.
        :param download_directory: Директория для сохранения скачанных файлов.
        """

        self.config = config_manager

        self.rabbitmq_host = self.config.get("RabbitMQ", "Host")
        self.rabbitmq_port = self.config.get("RabbitMQ", "Port")
        self.queue_name = self.config.get("RabbitMQ", "QueueName")

        self.download_directory = self.config.get("Service", "DownloadDirectory")

        self.download_timeout = self.config.get("FileDownload", "TimeoutSeconds")
        self.download_chunkSize = self.config.get("FileDownload", "ChunkSizeKB")

        if not all([self.rabbitmq_host, self.queue_name, self.download_directory]):
            raise ValueError("Missing critical configuration parameters. Check appsettings.json.")

        self.connection = None
        self.channel = None
        self._ensure_download_directory_exists()
        logger.info(f"Service initialized. Queue: '{self.queue_name}', Download dir: '{self.download_directory}'")
        logger.debug(f"Full config: {self.config.get_all()}")  # Для отладки

    def _ensure_download_directory_exists(self):
        """Создает директорию для скачивания файлов, если она не существует."""
        os.makedirs(self.download_directory, exist_ok=True)
        logger.info(f"Download directory '{self.download_directory}' ensured.")

    def _connect_to_rabbitmq(self):
        """Устанавливает соединение с RabbitMQ."""
        while True:
            try:
                logger.info(f"Attempting to connect to RabbitMQ at {self.rabbitmq_host}...")
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host, port=5672))
                self.channel = self.connection.channel()
                # Объявляем очередь. durable=True делает очередь устойчивой к перезапускам брокера.
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                logger.info("Successfully connected to RabbitMQ and declared queue.")
                break
            except pika.exceptions.AMQPConnectionError as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}. Retrying in 5 seconds...")
                time.sleep(5)
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred while connecting to RabbitMQ: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    def _on_message_callback(self, ch, method, properties, body):
        """
        Коллбэк-функция, вызываемая при получении нового сообщения.
        """
        logger.info(f"Received message with delivery tag: {method.delivery_tag}")
        try:
            message_data = json.loads(body)

            file_name = message_data.get("FileName")
            storage_url = message_data.get("StorageUrl")
            correlation_id = message_data.get("CorrelationId", "N/A")  # Добавляем CorrelationId для логирования

            logger.info(f"Processing CorrelationId: {correlation_id}")

            if not file_name or not storage_url:
                logger.error(f"Message missing 'FileName' or 'StorageUrl'. Body: {body.decode()}")
                ch.basic_ack(method.delivery_tag)  # Подтверждаем, чтобы сообщение не обрабатывалось снова
                return

            logger.info(f"Attempting to download '{file_name}' from '{storage_url}'")
            local_path = self._download_file(storage_url, file_name, correlation_id)
            if local_path:
                logger.info(f"Successfully downloaded '{file_name}' to '{local_path}' (CorrelationId: {correlation_id})")
                ch.basic_ack(method.delivery_tag) # Подтверждаем успешную обработку
            else:
                logger.warning(f"Failed to download '{file_name}' (CorrelationId: {correlation_id}). Message will be re-queued.")
                # Nack message, indicating failure, and requeue it for another attempt.
                # In a real-world scenario, you might want to send it to a Dead Letter Queue (DLQ)
                # after a certain number of retries to avoid endless loops.
                ch.basic_nack(method.delivery_tag, requeue=True)

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from message. Body: {body.decode()}")
            ch.basic_ack(method.delivery_tag) # Подтверждаем, так как сообщение повреждено и не может быть обработано
        except Exception as e:
            logger.error(f"An unhandled error occurred: {e}. Body: {body.decode()}. Re-queueing message.")
            ch.basic_nack(method.delivery_tag, requeue=True)

    def _download_file(self, url: str, filename: str, correlation_id: str) -> str | None:
        """
        Скачивает файл по заданному URL и сохраняет его локально.
        :param url: URL файла для скачивания.
        :param filename: Имя файла, под которым его сохранить.
        :param correlation_id: ID корреляции для логирования.
        :return: Локальный путь к скачанному файлу или None в случае ошибки.
        """
        # Безопасное формирование имени файла, чтобы избежать Path Traversal атак
        sanitized_filename = os.path.basename(filename)
        local_filepath = os.path.join(self.download_directory, sanitized_filename)

        try:
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                logger.error(f"Invalid URL '{url}' (CorrelationId: {correlation_id})")
                return None

            logger.info(f"Downloading '{url}' to '{local_filepath}' (CorrelationId: {correlation_id})")
            with requests.get(url, stream=True, timeout=self.download_timeout) as r:
                r.raise_for_status()
                with open(local_filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=self.download_chunkSize):
                        if chunk:  # Фильтруем пустые чанки
                            f.write(chunk)
            return local_filepath
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading file from '{url}': {e} (CorrelationId: {correlation_id})")
            return None
        except IOError as e:
            logger.error(f"Error saving file to '{local_filepath}': {e} (CorrelationId: {correlation_id})")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during file download: {e} (CorrelationId: {correlation_id})")
            return None

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
        if self.channel:
            self.channel.stop_consuming()
            logger.info("Channel consumption stopped.")
        if self.connection:
            self.connection.close()
            logger.info("RabbitMQ connection closed.")

if __name__ == "__main__":
    try:
        # Имя файла конфигурации. Можно передать через переменную окружения.
        CONFIG_FILE = os.getenv("APP_CONFIG_FILE", "appsettings.json")

        # Инициализируем менеджер конфигурации
        config_manager = ConfigManager(config_file=CONFIG_FILE)

        # Создаем и запускаем сервис, передавая ему менеджер конфигурации
        consumer_service = FileDownloaderService(config_manager=config_manager)
        consumer_service.start_consuming()
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"Service startup failed due to configuration error: {e}")
    except Exception as e:
        logger.critical(f"An unhandled error occurred during service startup: {e}")