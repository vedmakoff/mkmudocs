"""Мониторинг изменений в каталоге с Markdown файлами"""

import os
import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .builder import SiteBuilder


class MarkdownHandler(FileSystemEventHandler):
    """Обработчик событий файловой системы"""

    def __init__(self, builder: SiteBuilder):
        self.builder = builder
        self.last_build = 0
        self.debounce_seconds = 2  # Защита от множественных пересборок

    def _should_rebuild(self, event_path: str) -> bool:
        """Проверяет нужно ли пересобирать"""
        # Только markdown файлы
        if not event_path.endswith('.md'):
            return False

        # Debounce
        current_time = time.time()
        if current_time - self.last_build < self.debounce_seconds:
            return False

        self.last_build = current_time
        return True

    def on_modified(self, event):
        if event.is_directory:
            return
        if self._should_rebuild(event.src_path):
            print(f"\n📝 Изменен файл: {Path(event.src_path).name}")
            self.builder.build()

    def on_created(self, event):
        if event.is_directory:
            return
        if self._should_rebuild(event.src_path):
            print(f"\n✨ Создан файл: {Path(event.src_path).name}")
            self.builder.build()

    def on_deleted(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.md'):
            print(f"\n🗑️  Удален файл: {Path(event.src_path).name}")
            self.builder.build()


def start_watcher():
    """Запускает мониторинг файловой системы"""
    pages_dir = os.getenv('PAGES_DIR', '/pages')

    if not os.path.exists(pages_dir):
        print(f"Каталог {pages_dir} не существует, создаем...")
        os.makedirs(pages_dir, exist_ok=True)

    builder = SiteBuilder()
    event_handler = MarkdownHandler(builder)

    observer = Observer()
    observer.schedule(event_handler, pages_dir, recursive=True)
    observer.start()

    print(f"👁️  Мониторинг запущен: {pages_dir}")
    print("Ожидание изменений...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка мониторинга...")
        observer.stop()
    observer.join()


if __name__ == '__main__':
    start_watcher()