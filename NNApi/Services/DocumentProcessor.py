import os
import re
import io
import json
import time
from dataclasses import dataclass, field
from typing import List, Union, Dict, Any

import docx
import fitz  # PyMuPDF

from NNApi.Entities.Scene2 import Scene2
from NNApi.Services.ScenarioProcessorService import OllamaClient


class DocumentProcessor:
    """
    Основной процессор для загрузки документа, разделения его на сцены
    и обработки каждой сцены с помощью Ollama.
    """
    # Паттерн для обнаружения заголовков сцены (INT./EXT. LOCATION - DAY/NIGHT)
    # Этот паттерн может быть улучшен для учета всех возможных вариаций
    SCENE_HEADER_PATTERN = re.compile(
        r"^(?:ИНТ\.|EXT\.|I\.?N\.?T\.?|E\.?X\.?T\.?)\s+.*?(?:[\s-]+(?:DAY|NIGHT|MORNING|EVENING|DAWN|DUSK|UNKNOWN))?\s*$",
        re.IGNORECASE | re.MULTILINE
    )

    def __init__(self, ollama_model: str, file_type: str):
        self.ollama_client = OllamaClient(ollama_model)
        self.file_type = file_type.lower()  # 'docx' или 'pdf'
        if self.file_type not in ["docx", "pdf"]:
            raise ValueError("Поддерживаемые типы файлов: 'docx' или 'pdf'.")

    def _load_document_content(self, file_source: Union[str, bytes]) -> str:
        """
        Загружает содержимое документа (docx или pdf) и извлекает из него текст.
        file_source может быть путем к файлу (str) или бинарными данными (bytes),
        полученными из облака.
        """
        if isinstance(file_source, bytes):
            # Если это бинарные данные, используем BytesIO для имитации файлового объекта
            file_stream = io.BytesIO(file_source)
        elif isinstance(file_source, str):
            # Если это путь к файлу, библиотеки могут работать с ним напрямую
            file_stream = file_source
        else:
            raise ValueError("file_source должен быть путем к файлу (str) или бинарными данными (bytes).")

        print(f"Извлечение текста из {self.file_type}...")
        text_content = ""
        if self.file_type == "docx":
            try:
                doc = docx.Document(file_stream)
                text_content = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            except Exception as e:
                print(f"Ошибка при чтении DOCX: {e}")
                raise
        elif self.file_type == "pdf":
            try:
                doc = fitz.open(file_stream)  # fitz.open может принимать путь или BytesIO
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    text_content += page.get_text("text")  # "text" извлекает сырой текст
                doc.close()
            except Exception as e:
                print(f"Ошибка при чтении PDF: {e}")
                raise
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

    def process_document(self, file_source: Union[str, bytes]) -> List[Scene2]:
        """
        Основной метод для обработки документа.
        """
        # 1. Загрузка и извлечение всего текста
        full_text = self._load_document_content(file_source)
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

if __name__ == "__main__":
    # Название вашей Ollama модели
    OLLAMA_MODEL_NAME = "llama2" # Или "mistral", "gemma:7b", "phi3" и т.д.

    # Создаем фиктивные файлы для демонстрации
    docx_file_path = create_dummy_docx()
    # pdf_file_path = create_dummy_pdf() # Закомментировано, так как reportlab может быть не установлен

    print("\n--- Демонстрация для DOCX (локальный файл) ---")
    try:
        docx_processor = DocumentProcessor(ollama_model=OLLAMA_MODEL_NAME, file_type="docx")
        processed_docx_scenes = docx_processor.process_document(docx_file_path)

        for scene in processed_docx_scenes:
            print(f"\n--- Результаты для {scene.scene_id} ---")
            print(f"Текст сцены (первые 200 символов):\n{scene.text[:200]}...")
            print("Извлеченные метаданные:")
            for key, value in scene.metadata.items():
                print(f"  {key}: {value}")
            # print(f"  Raw LLM Response: {scene.raw_llm_response}") # Для отладки

    except Exception as e:
        print(f"Произошла ошибка при обработке DOCX: {e}")

    # --- Демонстрация для DOCX (бинарные данные из облака) ---
    print("\n--- Демонстрация для DOCX (имитация облачных данных) ---")
    try:
        # Имитируем чтение файла в байты, как это сделал бы облачный клиент
        with open(docx_file_path, 'rb') as f:
            docx_bytes_from_cloud = f.read()

        docx_cloud_processor = DocumentProcessor(ollama_model=OLLAMA_MODEL_NAME, file_type="docx")
        processed_cloud_scenes = docx_cloud_processor.process_document(docx_bytes_from_cloud)

        print("\n--- Результаты для первой сцены из облачных данных (кратко) ---")
        if processed_cloud_scenes:
            first_scene = processed_cloud_scenes[0]
            print(f"Сцена ID: {first_scene.scene_id}")
            print(f"Локация: {first_scene.metadata.get('location_details', 'N/A')}")
            print(f"Персонажи: {first_scene.metadata.get('characters_present', [])}")
        else:
            print("Сцены не были обработаны.")

    except Exception as e:
        print(f"Произошла ошибка при обработке облачных данных DOCX: {e}")