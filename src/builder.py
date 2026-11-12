"""Основной билдер сайта с универсальной обработкой ассетов"""
import os
import re
import hashlib
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from urllib.parse import unquote, urlparse
import yaml
import requests
from PIL import Image
from jinja2 import Environment, FileSystemLoader
from .converter import MarkdownToMicronConverter

class SiteBuilder:
    def __init__(self):
        self.pages_dir = Path(os.getenv('PAGES_DIR', '/pages'))
        self.site_dir = Path(os.getenv('SITE_DIR', '/data/output'))
        self.templates_dir = Path(os.getenv('TEMPLATES_DIR', '/app/templates'))
        self.site_name = os.getenv('SITE_NAME', 'My NomadNet Site')
        self.site_description = os.getenv('SITE_DESCRIPTION', '')
        self.date_format = os.getenv('DATE_FORMAT', '%Y-%m-%d %H:%M')
        self.node_name = os.getenv('NOMADNET_NODE_NAME', 'NomadNode')

        # Четкое разделение согласно архитектуре NomadNet:
        self.media_dir = self.site_dir / 'media'  # Для изображений (:/media/...)
        self.files_dir = self.site_dir / 'files'  # Для документов (:/files/...)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)
        
        self.image_max_width = int(os.getenv('IMAGE_MAX_WIDTH', 1200))
        self.image_quality = int(os.getenv('IMAGE_QUALITY', 85))

        self.converter = MarkdownToMicronConverter(self)
        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        self.site_dir.mkdir(parents=True, exist_ok=True)

    def process_asset(self, asset_path: str, source_md_file: Path, is_image: bool = False) -> dict:
        """Универсальная обработка файлов с сохранением оригинальных имён"""
        temp_file = None
        try:
            decoded_path = unquote(asset_path)
            
            # 1. Определяем путь к исходному файлу
            if decoded_path.startswith(('http://', 'https://')):
                print(f"  ⬇️  Загрузка внешней ссылки: {decoded_path}")
                try:
                    response = requests.get(decoded_path, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    url_path = urlparse(decoded_path).path
                    ext = Path(url_path).suffix.lower()
                    original_name = Path(url_path).stem or 'download'
                    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                        ext = '.jpg'

                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    temp_file.close()
                    source_path = Path(temp_file.name)
                except requests.RequestException as e:
                    print(f"  ⚠️  Не удалось загрузить: {e}")
                    return None
            else:
                # Локальный файл
                if decoded_path.startswith('/'):
                    source_path = (self.pages_dir / decoded_path.lstrip('/')).resolve()
                else:
                    source_path = (source_md_file.parent / decoded_path).resolve()
                    if not source_path.exists():
                        source_path = (self.pages_dir / decoded_path).resolve()
                
                if not source_path.exists() or not source_path.is_file():
                    print(f"  ⚠️  Файл не найден: {source_path}")
                    return None
                
                original_name = source_path.stem
            
            # Игнорируем скрытые и .md файлы
            if source_path.name.startswith('.') or source_path.suffix.lower() == '.md':
                return None
            
            # 2. Хеширование содержимого (нужно только для дедупликации)
            with open(source_path, 'rb') as f:
                content = f.read()
                content_hash = hashlib.md5(content).hexdigest()[:12]
            
            ext = source_path.suffix.lower()
            
            # 3. Формируем имя файла: оригинальное_имя.расширение
            # Используем оригинальное имя — как для страниц .mu
            base_filename = f"{original_name}{ext}"
            
            # 4. Если это изображение -> конвертируем в WebP и сохраняем в media/
            if is_image and ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                webp_filename = f"{original_name}.webp"
                webp_path = self.media_dir / webp_filename
                
                # Дедупликация: если файл с таким именем уже есть, проверяем хеш
                # Для WebP хеш считаем от исходного файла (до конвертации)
                hash_marker_path = self.media_dir / f".{content_hash}_{original_name}.marker"
                
                if webp_path.exists() and hash_marker_path.exists():
                    print(f"  ✓ Изображение (кэш): media/{webp_filename}")
                    return {'url': f"/media/media/{webp_filename}", 'original_ext': '.webp'}
                
                # Если файл с таким именем есть, но хеш другой — добавляем хеш к имени
                if webp_path.exists():
                    webp_filename = f"{original_name}_{content_hash}.webp"
                    webp_path = self.media_dir / webp_filename
                    if webp_path.exists():
                        print(f"  ✓ Изображение (кэш): media/{webp_filename}")
                        return {'url': f"/media/media/{webp_filename}", 'original_ext': '.webp'}
                
                try:
                    with Image.open(source_path) as img:
                        if img.width > self.image_max_width:
                            ratio = self.image_max_width / img.width
                            new_size = (self.image_max_width, int(img.height * ratio))
                            img = img.resize(new_size, Image.Resampling.LANCZOS)
                        
                        if img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                        
                        img.save(webp_path, 'WEBP', quality=self.image_quality, method=6)
                        # Создаём маркер дедупликации
                        hash_marker_path.write_text(content_hash)
                        print(f"  ✓ Изображение: {source_path.name} → media/{webp_filename}")
                        return {'url': f"/media/media/{webp_filename}", 'original_ext': '.webp'}
                except Exception as e:
                    print(f"  ⚠️  Ошибка конвертации {source_path.name}: {e}")
            
            # 5. Если это не изображение -> сохраняем в files/ с оригинальным именем
            output_path = self.files_dir / base_filename
            
            # Дедупликация: если файл с таким именем есть, проверяем хеш
            hash_marker_path = self.files_dir / f".{content_hash}_{original_name}.marker"
            
            if output_path.exists() and hash_marker_path.exists():
                print(f"  ✓ Файл (кэш): files/{base_filename}")
                return {'url': f"/file/{base_filename}", 'original_ext': ext}
            
            # Если файл с таким именем есть, но хеш другой — добавляем хеш к имени
            if output_path.exists():
                base_filename = f"{original_name}_{content_hash}{ext}"
                output_path = self.files_dir / base_filename
                if output_path.exists():
                    print(f"  ✓ Файл (кэш): files/{base_filename}")
                    return {'url': f"/file/{base_filename}", 'original_ext': ext}
            
            shutil.copy2(source_path, output_path)
            hash_marker_path.write_text(content_hash)
            print(f"  ✓ Файл: {source_path.name} → files/{base_filename}")
            
            return {'url': f"/file/{base_filename}", 'original_ext': ext}
            
        except Exception as e:
            print(f"  ✗ Ошибка обработки {asset_path}: {e}")
            return None
        finally:
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass


    def _get_top_level_dirs(self):
        dirs = []
        for item in self.pages_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                dirs.append({'name': item.name.capitalize(), 'url': f"/page/{item.name}/index.mu"})
        dirs.sort(key=lambda x: x['name'])
        return dirs

    def _extract_tags(self, content: str) -> list:
        tags = re.findall(r'#([a-zA-Zа-яА-ЯёЁ0-9_-]+)', content)
        return list(set(tags))

    def build(self):
        print(f"Сборка сайта: {self.site_name}")
        menu_items = self._get_top_level_dirs()
        dir_pages = defaultdict(list)
        page_details = {}
        tag_pages = defaultdict(list)

        for md_file in self.pages_dir.rglob('*.md'):
            data = self._read_and_convert(md_file)
            if data:
                rel_dir = str(data['rel_path'].parent)
                if rel_dir == '.': rel_dir = '/'
                dir_pages[rel_dir].append(data)
                page_details[data['url']] = data
                for tag in data['tags']:
                    tag_pages[tag].append(data)

        subdir_indexes = []
        for rel_dir, pages in dir_pages.items():
            pages.sort(key=lambda x: x['title'])
            for i, page in enumerate(pages):
                page['prev'] = pages[i-1] if i > 0 else None
                page['next'] = pages[i+1] if i < len(pages) - 1 else None
            if rel_dir != '/':
                subdir_indexes.append({'name': rel_dir.lstrip('/').capitalize(), 'url': f"/page/{rel_dir.lstrip('/')}/index.mu", 'count': len(pages)})
                self._generate_dir_index(rel_dir, pages, menu_items)

        for url, data in page_details.items():
            self._render_and_save_page(data, menu_items)

        tags_list = []
        for tag, pages in tag_pages.items():
            self._generate_tag_page(tag, pages, menu_items)
            tags_list.append({'name': tag, 'count': len(pages), 'url': f"/page/tags/{tag}.mu"})
        
        tags_list.sort(key=lambda x: x['name'].lower())
        self._generate_tags_index(tags_list, menu_items)

        root_pages = dir_pages.get('/', [])
        all_pages = [p for pages in dir_pages.values() for p in pages]
        all_pages.sort(key=lambda x: x['date'], reverse=True)
        
        self._generate_root_index(root_pages, subdir_indexes, all_pages[:5], tags_list[:10], menu_items)
        self._generate_node_info(list(page_details.values()), menu_items)
        print(f"✅ Сборка завершена. Страниц: {len(page_details)}, Тегов: {len(tags_list)}")

    def _read_and_convert(self, md_file: Path):
        try:
            content = md_file.read_text(encoding='utf-8')
            metadata, markdown_content = self._parse_frontmatter(content)
            h1_match = re.match(r'^\s*#\s+(.+?)\s*\n+', markdown_content)
            if h1_match:
                metadata.setdefault('title', h1_match.group(1))
                markdown_content = markdown_content[h1_match.end():]

            tags = self._extract_tags(content)
            micron_content = self.converter.convert(markdown_content, md_file)
            rel_path = md_file.relative_to(self.pages_dir)
            file_mtime = md_file.stat().st_mtime
            file_date = metadata.pop('date', datetime.fromtimestamp(file_mtime).strftime(self.date_format))

            return {
                'title': metadata.pop('title', md_file.stem),
                'url': f"/page/{rel_path.with_suffix('.mu')}",
                'rel_path': rel_path,
                'content': micron_content,
                'date': file_date,
                'tags': tags,
                'metadata': metadata
            }
        except Exception as e:
            print(f"  ✗ Ошибка чтения {md_file}: {e}")
            return None

    def _render_and_save_page(self, data, menu_items):
        template = self.env.get_template('page.mu.j2')
        rendered = template.render(title=data['title'], content=data['content'], node_name=self.node_name, updated_at=data['date'], prev_page=data['prev'], next_page=data['next'], menu_items=menu_items, **data['metadata'])
        output_path = self.site_dir / data['rel_path'].with_suffix('.mu')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding='utf-8')
        print(f"  ✓ {data['rel_path']} → {output_path.relative_to(self.site_dir)}")

    def _generate_dir_index(self, rel_dir, pages, menu_items):
        template = self.env.get_template('dir_index.mu.j2')
        rendered = template.render(dir_name=rel_dir.lstrip('/').capitalize(), node_name=self.node_name, pages=pages, menu_items=menu_items, updated_at=datetime.now().strftime(self.date_format))
        output_path = self.site_dir / rel_dir.lstrip('/') / 'index.mu'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding='utf-8')

    def _generate_tag_page(self, tag, pages, menu_items):
        template = self.env.get_template('tag.mu.j2')
        pages.sort(key=lambda x: x['date'], reverse=True)
        rendered = template.render(tag=tag, pages=pages, menu_items=menu_items, node_name=self.node_name, updated_at=datetime.now().strftime(self.date_format))
        output_path = self.site_dir / 'tags' / f"{tag}.mu"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding='utf-8')

    def _generate_tags_index(self, tags_list, menu_items):
        template = self.env.get_template('tags_index.mu.j2')
        rendered = template.render(tags=tags_list, menu_items=menu_items, node_name=self.node_name, updated_at=datetime.now().strftime(self.date_format))
        output_path = self.site_dir / 'tags' / 'index.mu'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding='utf-8')

    def _generate_root_index(self, root_pages, subdir_indexes, recent_pages, tags_list, menu_items):
        template = self.env.get_template('index.mu.j2')
        rendered = template.render(site_name=self.site_name, description=self.site_description, root_pages=root_pages, subdir_indexes=subdir_indexes, recent_pages=recent_pages, tags=tags_list, node_name=self.node_name, menu_items=menu_items, updated_at=datetime.now().strftime(self.date_format))
        output_path = self.site_dir / 'index.mu'
        output_path.write_text(rendered, encoding='utf-8')

    def _generate_node_info(self, all_pages, menu_items):
        template = self.env.get_template('node.info.j2')
        rendered = template.render(node_name=self.node_name, node_description=os.getenv('NOMADNET_NODE_DESCRIPTION', ''), owner=os.getenv('NOMADNET_OWNER', 'Anonymous'), contact=os.getenv('NOMADNET_CONTACT', ''), pages=all_pages, menu_items=menu_items, updated_at=datetime.now().strftime(self.date_format))
        output_path = self.site_dir / 'node.info'
        output_path.write_text(rendered, encoding='utf-8')

    def _parse_frontmatter(self, content: str):
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1])
                    return metadata or {}, parts[2].strip()
                except Exception:
                    pass
        return {}, content

if __name__ == '__main__':
    builder = SiteBuilder()
    builder.build()