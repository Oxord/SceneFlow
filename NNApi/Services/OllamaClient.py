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
            Ты — высокоточный ассистент для анализа киносценариев. Проанализируй предоставленный фрагмент сценария и извлеки из него информацию строго в формате JSON.
    
            Твои задачи:
            1.  Внимательно прочти текст сцены.
            2.  Извлеки данные для ВСЕХ указанных ниже полей.
            3.  Если информация для какого-то поля отсутствует в тексте, используй значение "N/A" для строк или пустой список [] для списков.
            4.  Твой ответ должен быть полностью на русском языке.
    
            Вот поля для извлечения:
            - "scene_number": (string) номер сцены, как он указан в заголовке (например, "1-1", "1-4-А").
            - "setting": (string) полное описание места и времени действия из заголовка (например, "НАТ. ЛЕС.ПОЛЯНА - НОЧЬ").
            - "location_details": (string) краткое описание локации из ремарок, 1-2 предложения.
            - "characters_present": (list[string]) список имен персонажей, которые ДЕЙСТВУЮТ или ГОВОРЯТ в сцене. Включай только имена людей или живых существ, НЕ неодушевленные предметы. Если персонаж указан в заголовке, но не действует, включи его.
            - "key_events_summary": (string) очень краткое (1-3 предложения) описание ключевых действий и событий в сцене.
            - "emotional_tone": (string) основной эмоциональный тон сцены (например, "напряженный", "трагический", "спокойный", "ироничный").
    
            Сцена для анализа:
            ---
            {scene_text}
            ---
    
            ВАЖНО: Твой ответ должен быть ИСКЛЮЧИТЕЛЬНО валидным JSON-объектом на русском языке. Не добавляй никаких пояснений, вступлений или комментариев до или после JSON.
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

    def generate_production_details(self, scene_summary: str, scene_text: str) -> Dict[str, Any]:
        """
        На основе описания сцены генерирует производственные детали.
        """
        prompt = f"""
            Ты — опытный ассистент режиссера. Твоя задача — проанализировать описание сцены и составить список производственных требований.
            Отвечай строго в формате JSON на русском языке. Для полей, по которым нет информации, используй "N/A" для строк или пустой список [] для списков.
        
            Вот описание ключевых событий сцены:
            ---
            {scene_summary}
            ---
        
            Вот полный текст сцены для дополнительного контекста:
            ---
            {scene_text}
            ---
        
            Заполни следующие поля в JSON:
            - "costume": (string) Описание ключевых костюмов для персонажей.
            - "makeup_and_hair": (string) Требования к гриму и прическам (например, "следы крови на лице", "обычный дневной макияж").
            - "props": (list[string]) Список ключевого реквизита, который используется в сцене (например, ["бинокль", "бутылка пива", "телефон"]).
            - "extras": (string) Описание требуемой массовки (например, "прохожие на улице", "посетители кафе").
            - "stunts": (string) Описание необходимых трюков (например, "падение с лестницы", "драка").
            - "special_effects": (string) Описание спецэффектов (например, "эффект дождя", "дым в помещении").
            - "music": (string) Предложения по музыкальному сопровождению, если это следует из текста.
        
            ВАЖНО: Ответ должен быть ТОЛЬКО валидным JSON. Не добавляй никаких комментариев.
            """
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                format='json',
                options={'temperature': 0.2}
            )
            llm_content = response['message']['content']
            return json.loads(llm_content)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON для production_details: {e}")
            return {}
        except Exception as e:
            logger.error(f"Ошибка при запросе к Ollama для production_details: {e}")
            return {}