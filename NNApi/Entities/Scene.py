from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from NNApi.Entities.ProductionData import ProductionData


@dataclass
class Scene:
    """
    Класс для хранения текста одной сцены и извлеченных метаданных.
    """
    scene_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    production_data: Optional[ProductionData] = None  # Добавляем новое поле
    raw_llm_response: Dict[str, Any] = field(default_factory=dict)