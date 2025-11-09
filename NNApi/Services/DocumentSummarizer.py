import ollama
import os

class DocumentSummarizer:
    """
    Класс для суммаризации содержимого файла с использованием локальной модели Ollama.
    """
    def __init__(self, model_name: str = "qwen:7b-chat", ollama_host: str = "http://localhost:11434"):
        """
        Инициализирует суммаризатор.

        Args:
            model_name (str): Имя модели Ollama для использования (например, "qwen:7b-chat", "mixtral").
            ollama_host (str): Адрес хоста, на котором запущен Ollama-сервер.
        """
        self.model_name = model_name
        self.client = ollama.Client(host=ollama_host)
        print(f"Инициализирован суммаризатор с моделью: {self.model_name}")

        # Проверка доступности модели и Ollama-сервера
        try:
            self.client.show(self.model_name)
            print(f"Модель '{self.model_name}' доступна на сервере Ollama.")
        except ollama.ResponseError as e:
            if "not found" in str(e):
                print(f"Ошибка: Модель '{self.model_name}' не найдена на сервере Ollama.")
                print(f"Пожалуйста, загрузите её командой: ollama pull {self.model_name}")
            else:
                print(f"Ошибка соединения с Ollama или другой API-ошибкой: {e}")
            raise  # Прерываем выполнение, так как без модели работать не сможем
        except Exception as e:
            print(f"Неожиданная ошибка при проверке модели: {e}")
            print(f"Убедитесь, что Ollama-сервер запущен по адресу {ollama_host}")
            raise

    def _read_file_content(self, file_path: str) -> str:
        """
        Приватный метод для чтения содержимого файла.

        Args:
            file_path (str): Путь к файлу.

        Returns:
            str: Содержимое файла.

        Raises:
            FileNotFoundError: Если файл не найден.
            IOError: Если возникла ошибка при чтении файла.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден по пути: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Ошибка при чтении файла '{file_path}': {e}")

    def summarize_file(self, file_path: str, max_tokens: int = 1000) -> str:
        """
        Отправляет запрос в нейросеть Ollama для составления конспекта по данному файлу.

        Args:
            file_path (str): Путь к файлу, содержимое которого нужно законспектировать.
            max_tokens (int): Максимальное количество токенов в ответе.

        Returns:
            str: Сгенерированный конспект или сообщение об ошибке.
        """
        try:
            file_content = self._read_file_content(file_path)
            if not file_content.strip():
                return "Файл пуст или содержит только пробелы. Конспект не может быть составлен."

            # Формирование запроса к нейросети
            # Важно: чем точнее промпт, тем лучше результат. Используйте разделители.
            prompt = (
                "**Составь подробный и сжатый конспект по следующему тексту. "
                "ОТВЕЧАЙ ИСКЛЮЧИТЕЛЬНО НА РУССКОМ ЯЗЫКЕ, БЕЗ ИСПОЛЬЗОВАНИЯ ДРУГИХ ЯЗЫКОВ ИЛИ СИМВОЛОВ.**\n\n"
                "Представь конспект в виде связного, последовательного текста, "
                "выделяя основные идеи, ключевые моменты и важные детали. "
                "Допускается использование маркированных списков *внутри конспекта* для перечисления пунктов "
                "или лучшей структуризации, но сам конспект должен быть представлен как единый, читаемый текст, "
                "а не только как набор списков.\n\n"
                "--- Начало документа ---\n"
                f"{file_content}\n"
                "--- Конец документа ---"
            )

            print(f"\nОтправка запроса в Ollama с моделью '{self.model_name}' для файла: {file_path}...")

            # Отправка запроса в Ollama
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {'role': 'user', 'content': prompt}
                ],
                options={
                    'num_predict': max_tokens  # Ограничиваем длину ответа
                }
            )

            # Извлечение конспекта из ответа
            summary = response['message']['content']
            return summary
        except FileNotFoundError as e:
            return f"Ошибка: {e}"
        except IOError as e:
            return f"Ошибка при работе с файлом: {e}"
        except ollama.ResponseError as e:
            return f"Ошибка Ollama API: {e}. Убедитесь, что модель '{self.model_name}' запущена и доступна."
        except Exception as e:
            return f"Произошла непредвиденная ошибка: {e}"

# --- Пример использования ---
if __name__ == "__main__":
    # 1. Создайте фиктивный файл для теста
    test_file_name = "test_document.txt"
    test_content = """
    Нанотехнологии представляют собой область науки и техники, занимающуюся манипуляциями с материей на атомном и молекулярном уровне.
    Это включает создание новых материалов и устройств с уникальными свойствами.
    Одним из ключевых применений нанотехнологий является медицина, где они могут быть использованы для целевой доставки лекарств, ранней диагностики заболеваний и регенеративной медицины.
    Например, наночастицы могут быть запрограммированы для распознавания раковых клеток и доставки к ним химиотерапевтических агентов, минимизируя побочные эффекты для здоровых тканей.
    В электронике нанотехнологии позволяют создавать более мелкие, быстрые и энергоэффективные компоненты, открывая путь к новым поколениям компьютеров и мобильных устройств.
    Также они находят применение в энергетике для повышения эффективности солнечных батарей и разработки новых методов хранения энергии.
    Однако существуют и потенциальные риски, связанные с нанотехнологиями, такие как их возможное воздействие на окружающую среду и здоровье человека, что требует тщательного исследования и регулирования.
    """
    with open(test_file_name, 'w', encoding='utf-8') as f:
        f.write(test_content)
    print(f"Создан тестовый файл: {test_file_name}")

    # 2. Выберите модель (не забудьте предварительно её загрузить: ollama pull qwen:7b-chat)
    # Можно попробовать "mixtral", "llama2:7b-chat", "mistral"
    # Рекомендуется "qwen:7b-chat"
    MODEL_TO_USE = "qwen:7b-chat" # ИЛИ "mixtral", "llama2:7b-chat"

    # 3. Инициализируем суммаризатор
    try:
        summarizer = DocumentSummarizer(model_name=MODEL_TO_USE)

        # 4. Запрашиваем конспект
        summary = summarizer.summarize_file(test_file_name, max_tokens=700) # Увеличьте max_tokens для более длинных конспектов

        print("\n--- Сгенерированный конспект ---")
        print(summary)
        print("---------------------------------\n")

    except Exception as e:
        print(f"Произошла фатальная ошибка при инициализации или работе суммаризатора: {e}")
        print("Пожалуйста, убедитесь, что Ollama-сервер запущен, и указанная модель загружена.")

    # 5. Очистка тестового файла
    if os.path.exists(test_file_name):
        os.remove(test_file_name)
        print(f"Удален тестовый файл: {test_file_name}")