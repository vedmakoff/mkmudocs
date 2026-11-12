"""Конвертер HTML в Micron синтаксис NomadNet"""
import re
from urllib.parse import unquote
from markdown_it import MarkdownIt


class MicronGenerator:
    def __init__(self, builder=None):
        # 'table' отключено в пресете commonmark — включаем явно
        self.md = MarkdownIt().enable(['linkify', 'table'])
        self.builder = builder

        # Оформление ссылок: зелёный + подчёркивание
        self.link_prefix = '`F8f0`_`'
        self.link_suffix = '`_`f`'

        # Оформление таблиц
        self.table_tag = '`t'          # открывающий/закрывающий тег таблицы Micron
        self.table_separator = True    # выводить строку | --- | --- | после заголовка
        self.table_pad_cells = True    # выравнивать колонки пробелами в исходнике .mu

    def convert(self, markdown_text: str, source_md_file=None) -> str:
        # Предварительная обработка: конвертируем ==текст== в <mark>текст</mark>
        markdown_text = re.sub(r'==([^=]+)==', r'<mark>\1</mark>', markdown_text)
        html = self.md.render(markdown_text)
        return self._html_to_micron(html, source_md_file)

    def _decode_path(self, path: str) -> str:
        return unquote(path)

    def _unescape_html(self, text: str) -> str:
        """Декодирует HTML-сущности (нужно и для кода, изолированного плейсхолдерами)"""
        return (text.replace('&amp;', '&').replace('&lt;', '<')
                    .replace('&gt;', '>').replace('&quot;', '"')
                    .replace('&#39;', "'").replace('&nbsp;', ' '))

    def _wrap_link(self, text: str, url: str) -> str:
        """Оборачивает ссылку в зелёный цвет + подчёркивание"""
        return f"{self.link_prefix}[{text}`{url}]{self.link_suffix}"

    def _normalize_internal_link(self, url: str, source_md_file) -> str:
        url = self._decode_path(url)
        if url.endswith('.md'):
            url = url[:-3] + '.mu'
            if not url.startswith('/'):
                if self.builder and source_md_file:
                    source_dir = source_md_file.parent
                    target_path = (source_dir / url).resolve()
                    if not target_path.exists():
                        target_path = (self.builder.pages_dir / url).resolve()
                    try:
                        rel_path = target_path.relative_to(self.builder.pages_dir.resolve())
                        url = f"/page/{rel_path}"
                    except ValueError:
                        url = f"/page/{url}"
                else:
                    url = f"/page/{url}"
        return url

    def _html_to_micron(self, html: str, source_md_file=None) -> str:
        # Хранилища для изоляции кода от постобработки (теги, сырые URL и т.д.)
        code_blocks = []
        inline_codes = []

        # 1. Заголовки
        html = re.sub(r'<h4[^>]*>(.*?)</h4>', r'>>> \1', html)
        html = re.sub(r'<h5[^>]*>(.*?)</h5>', r'>>> \1', html)
        html = re.sub(r'<h6[^>]*>(.*?)</h6>', r'>>> \1', html)
        html = re.sub(r'<h3[^>]*>(.*?)</h3>', r'>> \1', html)
        html = re.sub(r'<h2[^>]*>(.*?)</h2>', r'> \1', html)

        # 2. Форматирование текста
        html = re.sub(r'<strong>(.*?)</strong>', r'`!\1`!', html)
        html = re.sub(r'<b>(.*?)</b>', r'`!\1`!', html)
        html = re.sub(r'<em>(.*?)</em>', r'`*\1`*', html)
        html = re.sub(r'<i>(.*?)</i>', r'`*\1`*', html)
        html = re.sub(r'<u>(.*?)</u>', r'`_\1`_', html)

        # 3. ХАЙЛАЙТЕР (жёлтый фон + чёрный текст)
        def process_mark(match):
            content = match.group(1)
            return f"`Bee0`F000{content}`f`b"
        html = re.sub(r'<mark>(.*?)</mark>', process_mark, html)

        # 4. БЛОКИ КОДА -> изолируем плейсхолдером
        def process_code_block(match):
            full_html = match.group(0)
            lang = 'CODE'

            code_match = re.search(r'<code[^>]*>(.*?)</code>', full_html, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                lang_match = re.search(r'class="language-([^"]+)"', full_html)
                if lang_match:
                    lang = lang_match.group(1).upper()
            else:
                code = re.search(r'<pre[^>]*>(.*?)</pre>', full_html, re.DOTALL).group(1).strip()

            clean_code = self._unescape_html(code).replace('`', '')

            # Ведущий пробел у каждой строки: защита от директив Micron
            # в первой колонке ('#' комментарий, '>' заголовок, '-' разделитель)
            safe_code = '\n'.join(' ' + line for line in clean_code.split('\n'))

            header = f" ┌─ {lang}"
            footer = f" └{'─' * (len(lang) + 9)}"
            block = f"\n`B666`F0f0{header}\n{safe_code}\n{footer}`f\n`b\n"

            code_blocks.append(block)
            return f"\x00CB{len(code_blocks) - 1}\x00"

        html = re.sub(r'<pre>.*?</pre>', process_code_block, html, flags=re.DOTALL | re.IGNORECASE)

        # 5. ИНЛАЙН КОД -> тоже изолируем плейсхолдером
        def process_inline_code(match):
            content = self._unescape_html(match.group(1)).replace('`', '')
            inline_codes.append(f"`F0f0`B666{content}`b`f")
            return f"\x00IC{len(inline_codes) - 1}\x00"

        html = re.sub(r'<code>(.*?)</code>', process_inline_code, html)

        # 6. Ссылки
        def process_link(match):
            url = match.group(1)
            text = match.group(2)
            if url.startswith(('http://', 'https://')):
                return self._wrap_link(text, url)
            if url.endswith(('.md', '.mu')):
                return self._wrap_link(text, self._normalize_internal_link(url, source_md_file))
            if self.builder:
                asset_data = self.builder.process_asset(url, source_md_file, is_image=False)
                if asset_data:
                    return self._wrap_link(text, f":{asset_data['url']}")
            return self._wrap_link(text, url)

        html = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', process_link, html)

        # 7. Изображения
        def process_image(match):
            src = match.group(1)
            alt = match.group(2) if len(match.groups()) >= 2 and match.group(2) else 'Изображение'
            alt = self._decode_path(alt)
            src = self._decode_path(src)
            if self.builder:
                img_data = self.builder.process_asset(src, source_md_file, is_image=True)
                if img_data:
                    return f'`({alt}`w=n`a=c`:{img_data["url"]})'
            return f'[Изображение: {alt}] {src}'

        html = re.sub(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?>', process_image, html)
        html = re.sub(
            r'<img[^>]*src="([^"]*)"[^>]*/?>',
            lambda m: process_image(type('obj', (object,), {'group': lambda self, n: m.group(1) if n == 1 else ''})()),
            html
        )

        # 8. ТАБЛИЦЫ -> pipe-разметка, обёрнутая в `t
        # Обрабатываем ПОСЛЕ ссылок/форматирования, чтобы содержимое ячеек
        # уже было в Micron-виде, но ДО удаления HTML-тегов
        def process_table(match):
            table_html = match.group(0)

            rows_html = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, flags=re.DOTALL | re.IGNORECASE)
            rows = []
            for row_html in rows_html:
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row_html, flags=re.DOTALL | re.IGNORECASE)
                clean_cells = []
                for cell in cells:
                    cell = re.sub(r'<br\s*/?>', ' ', cell, flags=re.IGNORECASE)
                    cell = re.sub(r'<[^>]+>', '', cell)      # остатки HTML внутри ячейки
                    cell = self._unescape_html(cell)
                    cell = ' '.join(cell.split())            # ячейка обязана быть однострочной
                    cell = cell.replace('|', r'\|')          # экранируем вертикальные черты
                    clean_cells.append(cell)
                if clean_cells:
                    rows.append(clean_cells)

            if not rows:
                return ''

            # Выравниваем количество колонок по самой длинной строке
            col_count = max(len(r) for r in rows)
            for r in rows:
                r.extend([''] * (col_count - len(r)))

            # Ширины колонок (минимум 3 — под разделитель)
            widths = [max(3, max(len(r[i]) for r in rows)) for i in range(col_count)]

            if self.table_pad_cells:
                rows = [[cell.ljust(widths[i]) for i, cell in enumerate(r)] for r in rows]

            lines = [self.table_tag]
            for idx, r in enumerate(rows):
                lines.append('| ' + ' | '.join(r) + ' |')
                if idx == 0 and self.table_separator:
                    sep = ['-' * widths[i] for i in range(col_count)] if self.table_pad_cells else ['---'] * col_count
                    lines.append('| ' + ' | '.join(sep) + ' |')
            lines.append(self.table_tag)

            return '\n\n' + '\n'.join(lines) + '\n\n'

        html = re.sub(r'<table[^>]*>.*?</table>', process_table, html, flags=re.DOTALL | re.IGNORECASE)

        # 9. Остальная разметка
        html = re.sub(r'<li>(.*?)</li>', r'• \1\n', html)
        html = re.sub(r'</?[uo]l[^>]*>', '', html)
        html = re.sub(r'<p>(.*?)</p>', r'\1\n\n', html)
        html = re.sub(r'<hr[^>]*>', '\n-★\n', html)
        html = re.sub(r'<blockquote>(.*?)</blockquote>', r'| \1', html, flags=re.DOTALL)
        html = re.sub(r'<[^>]+>', '', html)
        html = self._unescape_html(html)
        html = re.sub(r'\n{3,}', '\n\n', html)

        # 10. Теги
        def process_tag(match):
            tag_name = match.group(1)
            return self._wrap_link(f'#{tag_name}', f'/page/tags/{tag_name}.mu')

        html = re.sub(r'#([a-zA-Zа-яА-ЯёЁ0-9_-]+)', process_tag, html)

        # 11. СЕТКА БЕЗОПАСНОСТИ ДЛЯ СЫРЫХ URL
        def process_raw_url(match):
            url = match.group(0)
            return self._wrap_link(url, url)

        html = re.sub(r'(?<!`)(?<!\[)https?://[^\s`\[\]<>\]]+', process_raw_url, html)

        # 12. ВОЗВРАЩАЕМ КОД НА МЕСТО (после всей постобработки)
        for i, block in enumerate(code_blocks):
            html = html.replace(f"\x00CB{i}\x00", block)
        for i, snippet in enumerate(inline_codes):
            html = html.replace(f"\x00IC{i}\x00", snippet)

        return html.strip()