import json
import os

import boto3


class SceneManager:
    def convert_scenes_to_json(self, scenes_list, filename="scenes.json"):
        """
        Принимает список объектов Scene и записывает их в локальный JSON-файл.
        Возвращает имя созданного файла.
        """
        scenes_dicts = [scene.to_dict() for scene in scenes_list]

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(scenes_dicts, f, ensure_ascii=False, indent=4)
            print(f"Данные успешно записаны в локальный файл {filename}")
            return filename  # Возвращаем имя файла для дальнейшей обработки
        except IOError as e:
            print(f"Ошибка при записи в файл {filename}: {e}")
            return None


    def upload_to_cloud(self, local_filename, object_key):  # <-- ИЗМЕНЕНИЕ 1: Добавили object_key в аргументы
        """
        Метод для отправки файла в облачное хранилище Timeweb Cloud.
        """
        endpoint_url = "https://s3.twcstorage.ru"
        access_key = "E3RCGRFP3PKE848H5S58"
        secret_key = "UOK2d1UI5oQ4egpmwjesqBipdbinPdEl1F6dBYG5"
        bucket_name = "be185a38-d8c61f38-cafe-4b90-97cf-54bf209995b6"
        region = "ru-1"

        if not local_filename or not os.path.exists(local_filename):
            print(f"Ошибка: Файл {local_filename} не найден или не был создан.")
            return None  # Возвращаем None при ошибке

        print(f"Начинается загрузка файла {local_filename} в облако как '{object_key}'...")

        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            try:
                # <-- ИЗМЕНЕНИЕ 2: Используем переданный object_key вместо os.path.basename()
                s3_client.upload_file(local_filename, bucket_name, object_key)

                # Формируем полный URL для возврата
                file_url = f"{endpoint_url}/{bucket_name}/{object_key}"
                print(f"Успешно загружено в Timeweb Cloud: {file_url}")

                os.remove(local_filename)
                print(f"Локальный файл {local_filename} удален.")

                # <-- ИЗМЕНЕНИЕ 3: Возвращаем URL, а не True
                return file_url

            except Exception as e:
                print(f"Ошибка загрузки в Timeweb Cloud: {e}")
                import traceback
                traceback.print_exc()  # Добавил вывод полного стека ошибки для диагностики
                return None  # Возвращаем None при ошибке

        except ImportError:
            print("boto3 не установлен.")
            return None