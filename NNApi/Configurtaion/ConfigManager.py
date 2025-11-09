import json
import os
import logging
from typing import Optional, Dict

# --- Настройка логирования до импорта конфигурации ---
# Временно устанавливаем INFO, потом можем переопределить из конфига
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Класс для загрузки и управления конфигурационными настройками.
    """
    _instance = None
    _config: Optional[Dict] = None

    def __new__(cls, config_file: str = "appsettings.json"):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            full_config_path = os.path.join(script_dir, config_file)
            cls._instance._load_config(config_file)
        return cls._instance

    def _load_config(self, config_file: str):
        if not os.path.exists(config_file):
            logger.error(f"Configuration file '{config_file}' not found. Exiting.")
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info(f"Configuration loaded from '{config_file}'.")
            # Применение уровня логирования из конфига
            log_level_str = self.get("Service", "LoggingLevel", default="INFO").upper()
            numeric_level = getattr(logging, log_level_str, None)
            if not isinstance(numeric_level, int):
                raise ValueError(f"Invalid log level: {log_level_str}")
            logging.getLogger().setLevel(numeric_level)
            logger.info(f"Logging level set to {log_level_str}.")

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from configuration file '{config_file}': {e}. Exiting.")
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading configuration: {e}. Exiting.")
            raise

    def get(self, *keys, default=None):
        """
        Получает значение из конфигурации по иерархии ключей.
        Например: config_manager.get("RabbitMQ", "Host")
        """
        current_config = self._config
        for key in keys:
            if isinstance(current_config, dict) and key in current_config:
                current_config = current_config[key]
            else:
                if default is not None:
                    return default
                else:
                    logger.warning(f"Configuration key path '{'.'.join(keys)}' not found, returning None.")
                    return None  # Или можно вызвать исключение, если значение обязательно

        return current_config

    def get_all(self):
        """Возвращает всю загруженную конфигурацию."""
        return self._config