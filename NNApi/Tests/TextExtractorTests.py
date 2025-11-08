from Utils.TextExtractor import TextExtractor
import unittest
from unittest.mock import patch, MagicMock

class TestTextExtractor(unittest.TestCase):
    def test_extract_text_from_docx(self):
        # Mock docx object and paragraphs
        mock_doc = MagicMock()
        mock_paragraphs = [MagicMock(text='Paragraph 1'), MagicMock(text='Paragraph 2')]
        mock_doc.paragraphs = mock_paragraphs
        with patch('docx.Document', return_value=mock_doc):
            extractor = TextExtractor('test.docx')
            text = extractor.extract_text_from_docx()
            self.assertEqual(text, "Paragraph 1\nParagraph 2")

    def test_extract_text_from_pdf(self):
        # Mock PdfReader object and pages
        mock_reader = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = 'Page 1 Text'
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = 'Page 2 Text'
        mock_reader.pages = [mock_page1, mock_page2]

        with patch('PyPDF2.PdfReader', return_value=mock_reader):
            extractor = TextExtractor('test.pdf')
            text = extractor.parse_script()
            self.assertEqual(text, "Page 1 Text\n\nPage 2 Text")

    def test_preprocess_text_utf8(self):
        extractor = TextExtractor('test.txt')
        text = "  Hello\n\nWorld  \t"
        cleaned_text = extractor.preprocess_text(text)
        self.assertEqual(cleaned_text, "Hello\n\nWorld")

    def test_preprocess_text_bytes(self):
        extractor = TextExtractor('test.txt')
        raw_text = b"  Hello\n\nWorld  \t"
        cleaned_text = extractor.preprocess_text(raw_text)
        self.assertEqual(cleaned_text, "Hello\n\nWorld")

    def test_parse_script_docx(self):
        # Mock docx object and paragraphs
        mock_doc = MagicMock()
        mock_paragraphs = [MagicMock(text='Paragraph 1'), MagicMock(text='Paragraph 2')]
        mock_doc.paragraphs = mock_paragraphs
        with patch('docx.Document', return_value=mock_doc):
            extractor = TextExtractor('test.docx')
            text = extractor.parse_script()
            self.assertEqual(text, "Paragraph 1\n\nParagraph 2")

    def test_parse_script_pdf(self):
        # Mock PdfReader object and pages
        mock_reader = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = 'Page 1 Text'
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = 'Page 2 Text'
        mock_reader.pages = [mock_page1, mock_page2]

        with patch('PyPDF2.PdfReader', return_value=mock_reader):
            extractor = TextExtractor('test.pdf')
            text = extractor.parse_script()
            self.assertEqual(text, "Page 1 Text\n\nPage 2 Text")

    def test_parse_script_invalid_extension(self):
        extractor = TextExtractor('test.txt')
        with self.assertRaises(ValueError):
            extractor.parse_script()

if __name__ == '__main__':
    unittest.main()
