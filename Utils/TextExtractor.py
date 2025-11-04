import docx
from PyPDF2 import PdfReader
import chardet
import re

class TextExtractor:
    def __init__(self, filepath):
        self.filepath = filepath

    def extract_text_from_docx(self):
        doc = docx.Document(self.filepath)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)

    def extract_text_from_pdf(self):
        reader = PdfReader(self.filepath)
        full_text = []
        for page in reader.pages:
            full_text.append(page.extract_text())
        return '\n'.join(full_text)

    def preprocess_text(self, raw_text):
        # Определение кодировки (если текст поступает в байтах)
        if isinstance(raw_text, bytes):
            result = chardet.detect(raw_text)
            encoding = result['encoding'] if result['confidence'] > 0.8 else 'utf-8'
            # Обработка случаев, когда chardet возвращает None
            if encoding is None:
                encoding = 'utf-8'
            try:
                text = raw_text.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                # Если возникает ошибка декодирования, пробуем стандартные кодировки
                for enc in ['utf-8', 'utf-16', 'cp1251', 'koi8-r', 'iso-8859-5', 'macroman']:
                    try:
                        text = raw_text.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # Если все кодировки не подходят, используем utf-8 с игнорированием ошибок
                    text = raw_text.decode('utf-8', errors='ignore')
        else:
            text = raw_text
        # Разделяем текст на абзацы (двойные и более переносов строк)
        paragraphs = re.split(r'\n\s*\n', text)
        # Обрабатываем каждый абзац
        processed_paragraphs = []
        for paragraph in paragraphs:
            # Убираем лишние пробельные символы внутри абзаца, но сохраняем одиночные пробелы
            cleaned_paragraph = re.sub(r'[ \t]+', ' ', paragraph)  # Множественные пробелы -> одиночные
            cleaned_paragraph = cleaned_paragraph.strip()  # Убираем пробелы по краям
            if cleaned_paragraph:
                processed_paragraphs.append(cleaned_paragraph)
        result = '\n\n'.join(processed_paragraphs)
        return result

    def parse_script(self):
        if self.filepath.endswith('.docx'):
            raw_text = self.extract_text_from_docx()
        elif self.filepath.endswith('.pdf'):
            raw_text = self.extract_text_from_pdf()
        else:
            raise ValueError("Поддерживаются только .docx и .pdf файлы.")
        cleaned_text = self.preprocess_text(raw_text)
        return cleaned_text