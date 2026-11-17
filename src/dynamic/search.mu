#!/usr/bin/env python3
import os
import json
import re
from pathlib import Path
from datetime import datetime

INDEX_PATH = Path(__file__).resolve().parent / 'search_index.json'
MENU_PATH = Path(__file__).resolve().parent / 'menu.mu'
PAGE_URL = '/page/search.mu'
NODE_NAME = os.getenv('NOMADNET_NODE_NAME', 'NomadNode')
LIMIT = 20


def get_query() -> str:
    """NomadNet передает поля формы как field_<имя> или var_<имя>"""
    for key in ('field_query', 'var_query'):
        val = os.environ.get(key)
        if val and val.strip():
            return val.strip()
    return ''


def esc(text) -> str:
    """Экранируем обратные кавычки, чтобы не сломать разметку"""
    return str(text).replace('`', "'")


def print_header():
    """Выводит шапку в стиле page.mu.j2"""
    # Меню (сгенерировано билдером)
    if MENU_PATH.exists():
        print(MENU_PATH.read_text(encoding='utf-8'))
    print('`---')
    # Заголовок в стиле page.mu.j2: `c`!Заголовок`!`a
    print('`c`!Поиск по сайту`!`a')
    print('`---')


def print_footer():
    """Выводит подвал в стиле page.mu.j2"""
    print('`---')
    print(f'Узел: {NODE_NAME}')
    print(f'Обновлено: {datetime.now().strftime("%Y-%m-%d %H:%M")}')


def snippet(text, words, width=140):
    """Извлекает фрагмент текста с совпадением"""
    low = text.lower()
    pos = min((low.find(w) for w in words if w in low), default=0)
    start = max(0, pos - 40)
    frag = text[start:start + width]
    return ('…' if start else '') + frag + ('…' if start + width < len(text) else '')


def main():
    query = get_query()

    # Шапка (меню + заголовок)
    print_header()

    # Если запроса нет — показываем подсказку
    if not query:
        print('Введите запрос в поле выше и нажмите 🔍')
        print_footer()
        return

    # Проверяем наличие индекса
    if not INDEX_PATH.exists():
        print('`Ff00Индекс поиска ещё не построен.`f')
        print_footer()
        return

    # Читаем индекс
    entries = json.loads(INDEX_PATH.read_text(encoding='utf-8'))
    words = [w for w in re.split(r'\W+', query.lower()) if len(w) > 1]

    if not words:
        print('Слишком короткий запрос. Минимальная длина слова — 2 символа.')
        print_footer()
        return

    # Ищем и оцениваем релевантность
    results = []
    for e in entries:
        title = e['title'].lower()
        tags = ' '.join(e.get('tags', [])).lower()
        body = e.get('text', '').lower()
        score = 0
        for w in words:
            if w in title:
                score += 10
            if w in tags:
                score += 3
            if w in body:
                score += 1
        if score:
            results.append((score, e))

    # Сортируем: сначала по убыванию оценки, потом по алфавиту
    results.sort(key=lambda x: (-x[0], x[1]['title']))

    # Выводим результаты
    print(f'Запрос: `*{esc(query)}`*')
    print(f'Найдено страниц: {len(results)}')
    print('`---')

    if not results:
        print('Ничего не найдено.')
    else:
        for _, e in results[:LIMIT]:
            print(f'`[ 📄 {esc(e["title"])}`{e["url"]}]`')
            sn = snippet(e.get('text', ''), words)
            if sn:
                print(f'   {esc(sn)}')
            print()

        if len(results) > LIMIT:
            print(f'`F888Показаны первые {LIMIT} из {len(results)}. Уточните запрос.`f')

    # Подвал
    FOOTER_PATH = Path(__file__).resolve().parent / 'footer.mu'


    def print_footer():
        print('`---')
        if FOOTER_PATH.exists():
            print(FOOTER_PATH.read_text(encoding='utf-8').rstrip())


if __name__ == '__main__':
    main()