from dataclasses import dataclass, field
from typing import List, Union, Dict, Any

@dataclass
class Scene2:
    """
    Класс для хранения текста одной сцены и извлеченных метаданных.
    """
    scene_id: str             # Уникальный идентификатор сцены (например, "Scene_001")
    text: str                 # Полный текст сцены
    metadata: Dict[str, Any] = field(default_factory=dict)  # Извлеченные LLM метаданные
    raw_llm_response: Dict[str, Any] = field(default_factory=dict) # Для хранения необработанного ответа LLM
