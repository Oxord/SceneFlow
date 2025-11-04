import unittest

from Entities.Scene import Scene
from Utils.SegmentationScenario import ScenarioSegmenter

class TestScenarioSegmenter(unittest.TestCase):
    def setUp(self):
        self.segmenter = ScenarioSegmenter()

    def test_single_scene_with_full_header(self):
        script = "\nСЦЕНА 1. ИНТ. КАБИНЕТ - ДЕНЬ\nТекст сцены один."
        result = self.segmenter.segment_script_to_scenes(script)
        expected = [Scene(1, "СЦЕНА 1. ИНТ. КАБИНЕТ - ДЕНЬ", "Текст сцены один.", "ИНТ. КАБИНЕТ", "ДЕНЬ")]
        self.assertEqual(result, expected)

    def test_multiple_scenes_with_different_headers(self):
        script = ("\n1. ИНТ. КОМНАТА - НОЧЬ\nТекст первой сцены.\n\n"
                  "2. НАТ. УЛИЦА - ДЕНЬ\nТекст второй сцены.\n\n"
                  "СЦЕНА 3. INT. OFFICE - EVENING\nТекст третьей сцены.")
        result = self.segmenter.segment_script_to_scenes(script)
        expected = [
            Scene(1, "1. ИНТ. КОМНАТА - НОЧЬ", "Текст первой сцены.", "ИНТ. КОМНАТА", "НОЧЬ"),
            Scene(2, "2. НАТ. УЛИЦА - ДЕНЬ", "Текст второй сцены.", "НАТ. УЛИЦА", "ДЕНЬ"),
            Scene(3, "СЦЕНА 3. INT. OFFICE - EVENING", "Текст третьей сцены.", "INT. OFFICE", "EVENING")
        ]
        self.assertEqual(result, expected)

    def test_no_scene_headers(self):
        script = "Текст без заголовков сцен."
        result = self.segmenter.segment_script_to_scenes(script)
        expected = [Scene(1, "N/A", "Текст без заголовков сцен.", "Неизвестно", "Неизвестно")]

        self.assertEqual(result, expected)

    def test_empty_script(self):
        script = ""
        result = self.segmenter.segment_script_to_scenes(script)
        expected = []
        self.assertEqual(result, expected)

    def test_scene_with_no_number_in_header(self):
        script = "\nИНТ. ЗАЛ - УТРО\nТекст сцены без номера."
        result = self.segmenter.segment_script_to_scenes(script)
        expected = [Scene(1, "ИНТ. ЗАЛ - УТРО", "Текст сцены без номера.", "ИНТ. ЗАЛ", "УТРО")]

        self.assertEqual(result, expected)

    def test_scene_text_accumulation(self):
        script = ("\nСЦЕНА 1. ИНТ. КАБИНЕТ - ДЕНЬ\nНачало текста.\n\n"
                  "Продолжение текста сцены.\n\n"
                  "СЦЕНА 2. НАТ. ПАРК - ВЕЧЕР\nТекст второй сцены.")
        result = self.segmenter.segment_script_to_scenes(script)
        self.assertEqual(result[0].description, "Начало текста.\n\nПродолжение текста сцены.")
        self.assertEqual(result[1].description, "Текст второй сцены.")

if __name__ == '__main__':
    unittest.main()
