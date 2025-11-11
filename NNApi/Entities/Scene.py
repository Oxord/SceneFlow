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

    def to_dict(self):
        """Преобразует объект Scene в словарь, обрабатывая вложенные объекты."""
        data = {
            "id": self.scene_id,
            "text": self.text,
            "metadata": self.metadata,
            "raw_llm_response": self.raw_llm_response,
        }

        if self.production_data:
            data["production_data"] = self.production_data.to_dict()
        else:
            data["production_data"] = None

        return data