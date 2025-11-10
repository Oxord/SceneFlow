import re
import io
from typing import List, Union, Dict, Any
import docx
import fitz  # PyMuPDF
from NNApi.Entities.Scene2 import Scene2
import logging
from NNApi.Services.OllamaClient import OllamaClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Основной процессор для загрузки документа, разделения его на сцены
    и обработки каждой сцены с помощью Ollama.
    """
    # Паттерн для обнаружения заголовков сцены (INT./EXT. LOCATION - DAY/NIGHT)
    # Этот паттерн может быть улучшен для учета всех возможных вариаций
    SCENE_HEADER_PATTERN = re.compile(
        r"^(?:ИНТ\.|НАТ\.|I\.?N\.?T\.?|E\.?X\.?T\.?)\s+.*?(?:[\s-]+(?:ДЕНЬ|НОЧЬ|УТРО|ВЕЧЕР|DAWN|DUSK|UNKNOWN))?\s*$",
        re.IGNORECASE | re.MULTILINE
    )

    def __init__(self, ollama_model: str, ollama_host: str):
        self.ollama_client = OllamaClient(ollama_model, ollama_host)
        logger.info(f"DocumentProcessor initialized with Ollama model: {ollama_model}")

    def _load_document_content(self, file_content_bytes: bytes, file_type: str) -> str:
        """
        Извлекает текст из бинарного содержимого документа.
        """
        file_stream = io.BytesIO(file_content_bytes)

        logger.info(f"Извлечение текста из {file_type}...")
        text_content = ""
        if file_type == "docx":
            try:
                doc = docx.Document(file_stream)
                text_content = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            except Exception as e:
                logger.error(f"Ошибка при чтении DOCX: {e}")
                raise
        elif file_type == "pdf":
            try:
                doc = fitz.open(file_stream)
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    text_content += page.get_text("text")
                doc.close()
            except Exception as e:
                logger.error(f"Ошибка при чтении PDF: {e}")
                raise
        else:
            raise ValueError(f"Неподдерживаемый тип файла: {file_type}. Поддерживаются 'docx' или 'pdf'.")

        if not text_content.strip():
            logger.warning("Извлеченный текст из документа пуст.")

        return text_content


    def _split_into_scenes(self, full_text: str) -> List[Scene2]:
        """
        Разделяет полный текст сценария на отдельные сцены, используя паттерны заголовков.
        """
        scenes: List[Scene2] = []
        current_scene_lines: List[str] = []
        scene_counter = 0

        # Разделяем текст на строки и обрабатываем каждую
        lines = full_text.splitlines()
        for i, line in enumerate(lines):
            stripped_line = line.strip()

            # Если строка похожа на заголовок сцены
            if self.SCENE_HEADER_PATTERN.match(stripped_line):
                # Если у нас уже есть строки для текущей сцены, сохраняем ее
                if current_scene_lines:
                    scene_counter += 1
                    scenes.append(Scene2(
                        scene_id=f"Scene_{scene_counter:03d}",
                        text="\n".join(current_scene_lines).strip()
                    ))
                    current_scene_lines = []  # Начинаем новую сцену

                # Добавляем заголовок сцены к новой сцене
                current_scene_lines.append(line)
            elif stripped_line:  # Добавляем только непустые строки
                current_scene_lines.append(line)
            # else: # Если строка пустая, можем игнорировать или добавить как разделитель
            #     current_scene_lines.append(line)

        # Добавляем последнюю сцену, если что-то осталось
        if current_scene_lines:
            scene_counter += 1
            scenes.append(Scene2(
                scene_id=f"Scene_{scene_counter:03d}",
                text="\n".join(current_scene_lines).strip()
            ))

        print(f"Документ разделен на {len(scenes)} сцен.")
        return scenes

    def process_document(self, file_source: Union[str, bytes], file_type: str) -> List[Scene2]:
        """
        Основной метод для обработки документа.
        """
        # 1. Загрузка и извлечение всего текста
        full_text = self._load_document_content(file_source, file_type)
        if not full_text:
            print("Не удалось извлечь текст из документа.")
            return []

        # 2. Разделение текста на сцены
        scenes = self._split_into_scenes(full_text)

        processed_scenes: List[Scene2] = []
        for i, scene in enumerate(scenes):
            print(f"Обработка сцены {scene.scene_id} ({i + 1}/{len(scenes)})...")
            # 3. Отправка каждой сцены в LLM
            llm_output = self.ollama_client.extract_scene_info(scene.text)
            scene.metadata = llm_output
            scene.raw_llm_response = llm_output  # Сохраняем полный ответ для отладки
            processed_scenes.append(scene)

            # Опционально: небольшая задержка между запросами к LLM, чтобы не перегружать
            # time.sleep(0.5)

        print("Обработка всех сцен завершена.")
        return processed_scenes