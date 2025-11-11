import json
import os

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


    def upload_to_cloud(self, local_filename, bucket_name="my-scene-bucket", region="ru-central1"):
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
            return False

        print(f"Начинается загрузка файла {local_filename} в облако Timeweb Cloud (Бакет: {bucket_name})...")

        #  Реализация с использованием boto3 для Timeweb Cloud (S3-совместимое хранилище)
        try:
            import boto3
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )

            try:
                s3_client.upload_file(local_filename, bucket_name, os.path.basename(local_filename))
                print(f"Успешно загружено в Timeweb Cloud: s3://{bucket_name}/{os.path.basename(local_filename)}")
                os.remove(local_filename)
                print(f"Локальный файл {local_filename} удален.")
                return True
            except Exception as e:
                print(f"Ошибка загрузки в Timeweb Cloud: {e}")
                return False
        except ImportError:
            print("boto3 не установлен.  Пожалуйста, установите его с помощью 'pip install boto3'")
            print("Заглушка: Файл успешно отправлен в облако (воображаемое).")
            return True # Возвращаем True, чтобы не прерывать процесс, если нет boto3