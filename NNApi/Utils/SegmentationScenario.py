import re
from Entities.Scene import Scene


class ScenarioSegmenter:
    def __init__(self):
        # Паттерн для заголовка сцены. Может быть сложнее в зависимости от формата.
        # Пример: "СЦЕНА 1. ИНТ. КАБИНЕТ - ДЕНЬ" или "1. ИНТ. КАБИНЕТ - ДЕНЬ"
        self.scene_header_pattern = re.compile(
            r'(?:\n|^)(?:(?:СЦЕНА\s*)?(\d+)\.\s*)?((?:ИНТ\.|НАТ\.|INT\.|EXT\.)\s*[А-ЯЁ\w\s\-]+?)\s*-\s*([А-ЯЁ\w]+)(?=\s*(?:\n|$))',
            re.IGNORECASE
        )

    def segment_script_to_scenes(self, script_text):
        scenes = []
        last_match_end = 0

        # Находим все заголовки сцен
        matches = list(self.scene_header_pattern.finditer(script_text))

        for i, match in enumerate(matches):
            scene_start = match.start()
            scene_end = matches[i + 1].start() if i + 1 < len(matches) else len(script_text)

            # Текст предыдущей сцены заканчивается перед началом текущего заголовка
            if scenes:
                scenes[-1].description += script_text[last_match_end:scene_start]
                scenes[-1].description = scenes[-1].description.strip()  # Очистить пробелы в конце

            groups = match.groups()
            scene_number = groups[0]
            location_type_and_name = groups[1].strip()
            time_of_day = groups[2].strip()

            scenes.append(
                Scene(
                    int(scene_number) if scene_number else (len(scenes) + 1),
                    match.group(0).strip(),
                    "",
                    location_type_and_name,
                    time_of_day
                )
            );
            last_match_end = match.end()

        if scenes:
            scenes[-1].description += script_text[last_match_end:]
            scenes[-1].description = scenes[-1].description.strip()
        elif script_text.strip():  # Если нет заголовков, но есть текст, считаем его одной сценой
            scenes.append(
                Scene(
                    1,
                    "N/A",
                    script_text.strip(),
                    "Неизвестно",
                    "Неизвестно"
                )
            )

        return scenes