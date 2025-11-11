from dataclasses import dataclass, field, asdict
from typing import List

@dataclass
class ProductionData:
    """Хранит производственные детали, извлеченные из сцены."""
    costume: str = "N/A"
    makeup_and_hair: str = "N/A"  # Грим и прически
    props: List[str] = field(default_factory=list)  # Реквизит
    extras: str = "N/A"  # Массовка
    stunts: str = "N/A"  # Каскадеры/трюки
    special_effects: str = "N/A"
    music: str = "N/A"

    def to_dict(self):
        """Преобразует объект ProductionData в словарь."""
        # Используем asdict для простоты, так как это dataclass
        return asdict(self)