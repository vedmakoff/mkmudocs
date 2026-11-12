"""Конвертер Markdown файлов в Micron формат"""
from .micron import MicronGenerator


class MarkdownToMicronConverter:
    """Основной конвертер Markdown → Micron"""

    def __init__(self, builder=None):
        self.generator = MicronGenerator(builder)

    def convert(self, markdown_content: str, source_md_file=None) -> str:
        """Конвертирует Markdown контент в Micron"""
        return self.generator.convert(markdown_content, source_md_file)

    def convert_file(self, input_path: str, output_path: str):
        """Конвертирует файл Markdown в Micron файл"""
        from pathlib import Path
        with open(input_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        micron_content = self.convert(markdown_content, Path(input_path))
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(micron_content)
        return micron_content