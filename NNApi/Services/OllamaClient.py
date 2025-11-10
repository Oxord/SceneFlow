import ollama
import json
import logging
from typing import List, Union, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Клиент для взаимодействия с локальной LLM через Ollama.
    """
    def __init__(self, model_name: str, host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host
        self.client = ollama.Client(host=self.host)
        logger.info(f"OllamaClient initialized with model: {self.model_name}, host: {self.host}")

    def extract_scene_info(self, scene_text: str) -> Dict[str, Any]:
        """
        Отправляет текст сцены в LLM и возвращает извлеченную информацию.
        """
        prompt = f"""
        Выступи в роли эксперта по анализу сценариев. Твоя задача - проанализировать следующую сцену и извлечь из нее ключевую информацию.
        Предоставь информацию в формате JSON со следующими полями:
        - "scene_number": (str, номер сцены, если явно указан в тексте, иначе "N/A")
        - "setting": (str, краткое описание места и времени действия, например, "ВНУТРИ ГОСТИНИЧНОГО НОМЕРА - НОЧЬ")
        - "location_details": (str, более подробное описание локации)
        - "time_of_day": (str, время суток, например, "ДЕНЬ", "НОЧЬ", "УТРО", "ВЕЧЕР")
        - "characters_present": (list[str], список имен персонажей, присутствующих или упоминаемых в сцене)
        - "key_events_summary": (str, краткое описание основных событий, происходящих в сцене, 1-3 предложения)
        - "emotional_tone": (str, основной эмоциональный тон сцены, например, "напряженный", "драматический", "комедийный", "спокойный")
        - "dialogue_summary": (str, краткое описание основной темы диалога, если есть)

        Сцена для анализа:
        ---
        {scene_text}
        ---

        Ответ должен быть ТОЛЬКО в формате JSON, без дополнительного текста.
        """
        try:
            # Используем ollama.chat для лучшего контроля и поддержки 'json' формата
            response = self.client.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                format='json', # Указываем, что ожидаем JSON-ответ
                options={
                    'temperature': 0.1 # Делаем ответы более детерминированными
                },
            )
            llm_content = response['message']['content']
            return json.loads(llm_content)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON от LLM: {e}")
            logger.error(f"Сырой ответ LLM: {llm_content}")
            return {"error": "JSONDecodeError", "message": str(e), "raw_llm_response": llm_content}
        except Exception as e:
            logger.error(f"Ошибка при запросе к Ollama: {e}")
            return {"error": "OllamaRequestError", "message": str(e)}