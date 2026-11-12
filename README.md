# MkMuDocs

Автоматический генератор сайтов для сети NomadNet из Markdown-файлов с мониторингом изменений в реальном времени.

💡 **MkMuDocs** — читается как *"Make My Docs"* (сделай мои документы), что отражает суть проекта: вы пишете Markdown, а система автоматически создаёт для вас готовый NomadNet сайт.

## Возможности

✅ Автоматическая конвертация Markdown → Micron (`.mu`)  
✅ Мониторинг изменений в реальном времени через `watchdog`  
✅ Автоматическая обработка изображений (конвертация в WebP, оптимизация размера)  
✅ Автоматическая обработка и дедупликация файлов (сохранение в каталоге `files/`)  
✅ Поддержка YAML frontmatter для метаданных  
✅ Автоматическая генерация индексов каталогов и страниц тегов  
✅ Навигация `prev`/`next` между страницами  
✅ Подключение к публичным узлам NomadNet по умолчанию  
✅ Гибкая настройка через переменные окружения  
✅ Автоматическое создание каталогов с правильными правами внутри контейнера  

---

## Быстрый старт

### 1. Подготовка структуры каталогов

Создайте каталог для вашего контента на хост-машине:

```bash
mkdir -p my-content/pages
```

### 2. Добавьте Markdown-файлы

Создайте ваш первый файл. Главная страница (`index.mu`) и служебный файл узла (`node.info`) будут сгенерированы автоматически внутри контейнера на основе шаблонов и переменных окружения, поэтому создавать их вручную не нужно.

```bash
cat > my-content/pages/about.md << 'EOF'
---
title: О проекте
author: Your Name
tags: [nomadnet, tutorial]
---

# О проекте

Это мой NomadNet сайт, созданный с помощью **MkMuDocs**.

## Возможности

- Автоматическая конвертация из Markdown
- Мониторинг изменений в реальном времени
- Поддержка изображений и файлов
- Автоматическая генерация тегов и индексов

Просто добавьте `.md` файлы в каталог `pages/`, и они автоматически появятся в сети NomadNet.

#nomadnet #tutorial
EOF
```

### 3. Создайте файл `.env`

```bash
cat > .env << 'EOF'
# Основные настройки
NOMADNET_NODE_NAME=MyNomadNode
NOMADNET_NODE_DESCRIPTION=Мой NomadNet сайт
NOMADNET_OWNER=Anonymous
NOMADNET_CONTACT=

# Сеть
NOMADNET_PORT=4242
NOMADNET_PEER_NODES=nomad.network:4242,reticulum.network:4242,us.nomadnet.org:4242

# Сайт
SITE_NAME=My NomadNet Site
SITE_DESCRIPTION=Автоматически сгенерированный сайт

# Пути на хосте
HOST_PAGES_DIR=./my-content/pages
HOST_CONFIG_DIR=./my-config

# Интерфейсы
ENABLE_AUTO_INTERFACE=true
ENABLE_TCP_SERVER=true
ENABLE_I2P=false
RETICULUM_ENABLE_TRANSPORT=false
AUTO_GROUP_ID=nomadnet

# Пользователь (должен совпадать с владельцем файлов на хосте)
PUID=1000
PGID=1000

# Изображения
IMAGE_MAX_WIDTH=1200
IMAGE_QUALITY=85

# Формат даты
DATE_FORMAT=%Y-%m-%d %H:%M
EOF
```

### 4. Запустите контейнер

```bash
docker compose up -d
```

### 5. Готово!

Сайт автоматически сгенерируется внутри контейнера и будет опубликован в сети NomadNet. Логи можно посмотреть командой:

```bash
docker compose logs -f
```

---

## Структура проекта (на хост-машине)

Пользователь работает только с исходными файлами и шаблонами. Выходные `.mu` файлы генерируются и хранятся исключительно внутри контейнера.

```text
.
├── docker-compose.yml          # Конфигурация Docker Compose V2
├── Dockerfile                  # Инструкция сборки образа
├── entrypoint.sh               # Скрипт инициализации и запуска
├── requirements.txt            # Python-зависимости
├── .env                        # Переменные окружения (создаётся вручную)
├── src/                        # Исходный код генератора
│   ├── __init__.py
│   ├── builder.py              # Основной билдер сайта
│   ├── watcher.py              # Мониторинг изменений
│   ├── converter.py            # Конвертер Markdown → Micron
│   └── micron.py               # Генератор Micron-разметки
├── templates/                  # Jinja2 шаблоны
│   ├── index.mu.j2             # Главная страница
│   ├── page.mu.j2              # Страница контента
│   ├── dir_index.mu.j2         # Индекс каталога
│   ├── tag.mu.j2               # Страница тега
│   ├── tags_index.mu.j2        # Индекс всех тегов
│   ├── node.info.j2            # Служебная информация об узле
│   ├── menu.mu.j2              # Компонент меню навигации
│   └── divider.mu.j2           # Компонент разделителя
└── my-content/                 # Ваш контент (монтируется в контейнер) можете указать любую директорию в .env файле
    └── pages/                  # любой тип файлов, они будут превращаться в страницы, изображения или файлы для скачивания
        └── about.md
```

---

## Внутренняя структура и логика URL в NomadNet

MkMuDocs автоматически создаёт следующую структуру в выходном каталоге (`/data/output`), которую видит демон NomadNet:

```text
/data/output/
├── index.mu                  # Главная страница (автогенерация)
├── node.info                 # Информация об узле (автогенерация)
├── about.mu                  # Сгенерированные страницы (лежат в корне или подкаталогах)
├── category/                 # Подкаталоги, повторяющие структуру /pages/
│   ├── index.mu              # Индекс подкаталога (автогенерация)
│   └── page1.mu              # Страница контента
├── media/                    # Оптимизированные изображения (WebP)
│   └── photo.webp
├── files/                    # Файлы для скачивания (с дедупликацией)
│   └── document.pdf
└── tags/                     # Страницы тегов
    ├── index.mu              # Индекс всех тегов (автогенерация)
    └── tutorial.mu           # Страница конкретного тега
```

> **⚠️ Важно о путях в NomadNet:**  
> В сети NomadNet URL имеют формат `:/тип_контента/путь_к_файлу`. Тип контента определяется демоном для маршрутизации, а не физической папкой:
> - **Страницы:** `:/page/about.mu` (тип `page`, физически файл `about.mu` лежит в корне `/data/output/` или в соответствующем подкаталоге).
> - **Изображения:** `:/media/media/photo.webp` (тип `media`, физическая папка `media/` внутри `/data/output/`).
> - **Файлы:** `:/file/document.pdf` (тип `file`, физическая папка `files/` внутри `/data/output/`, которую демон в `entrypoint.sh` получает как `files_path = ${SITE_DIR}/files` и обслуживает как корень файловых ресурсов).

---

## Markdown-синтаксис

### Frontmatter

Используйте YAML frontmatter в начале файла для метаданных:

```markdown
---
title: Название страницы
author: Имя автора
date: 2024-01-15
tags: [nomadnet, tutorial, python]
---

# Заголовок
Содержимое страницы...
```

### Изображения

```markdown
![Описание изображения](./images/photo.jpg)
```
Изображения автоматически конвертируются в WebP, оптимизируются по размеру и становятся доступны по пути `:/media/media/filename.webp`.

### Файлы

```markdown
[Скачать документ](./files/document.pdf)
```
Файлы копируются в каталог `files/` с сохранением оригинальных имен и дедупликацией по хешу. Благодаря настройке `files_path` в `entrypoint.sh`, они становятся доступны по корректному пути `:/file/document.pdf`.

### Внутренние ссылки

```markdown
[Другая страница](./other-page.md)
[Страница в подкаталоге](./category/page.md)
```
Ссылки на `.md` файлы автоматически преобразуются в формат Micron `.mu` с правильными путями (`:/page/...`).

### Теги

Хештеги в тексте автоматически превращаются в кликабельные ссылки на страницы тегов:

```markdown
Это страница про #nomadnet и #tutorial
```

### Таблицы, блоки кода и выделение

Поддерживаются стандартные конструкции Markdown, которые конвертируются в нативный синтаксис Micron:

```markdown
| Колонка 1 | Колонка 2 |
|-----------|-----------|
| Ячейка 1  | Ячейка 2  |
```

```python
def hello():
    print("Hello, NomadNet!")
```
```markdown
==Подсвеченный текст==
```

---

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `NOMADNET_NODE_NAME` | Имя узла в сети | `MyNomadSite` |
| `NOMADNET_NODE_DESCRIPTION` | Описание узла | `NomadNet Site` |
| `NOMADNET_OWNER` | Владелец узла | `Anonymous` |
| `NOMADNET_CONTACT` | Контактная информация | *(пусто)* |
| `NOMADNET_PORT` | Порт TCP/UDP | `4242` |
| `NOMADNET_PEER_NODES` | Узлы для подключения (через запятую) | `nomad.network:4242,...` |
| `SITE_NAME` | Название сайта | `My NomadNet Site` |
| `SITE_DESCRIPTION` | Описание сайта | *(пусто)* |
| `HOST_PAGES_DIR` | Путь к Markdown-файлам на хосте | `./my-content/pages` |
| `HOST_CONFIG_DIR` | Путь к конфигурации на хосте | `./my-config` |
| `ENABLE_AUTO_INTERFACE` | Обнаружение в локальной сети | `true` |
| `ENABLE_TCP_SERVER` | Запуск TCP-сервера | `true` |
| `ENABLE_I2P` | Поддержка сети I2P | `false` |
| `RETICULUM_ENABLE_TRANSPORT` | Режим транспортного узла | `false` |
| `AUTO_GROUP_ID` | ID группы Auto Interface | `nomadnet` |
| `PUID` / `PGID` | UID/GID пользователя для прав на файлы | `1000` |
| `IMAGE_MAX_WIDTH` | Максимальная ширина изображений (px) | `1200` |
| `IMAGE_QUALITY` | Качество WebP (1-100) | `85` |
| `DATE_FORMAT` | Формат даты в шаблонах | `%Y-%m-%d %H:%M` |

---

## Примеры использования

### Docker Compose (Рекомендуемый способ)

```yaml
services:
  mkmudocs:
    build: .
    image: mkmudocs:latest
    container_name: mkmudocs
    env_file:
      - .env
    volumes:
      - ${HOST_PAGES_DIR}:/pages
      - ${HOST_CONFIG_DIR}:/data/config
      - ./src:/app/src:ro
      - ./templates:/app/templates:ro
    ports:
      - "${NOMADNET_PORT:-4242}:${NOMADNET_PORT:-4242}/tcp"
      - "${NOMADNET_PORT:-4242}:${NOMADNET_PORT:-4242}/udp"
      - "37428:37428/udp"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Запуск:
```bash
docker compose up -d
```

### Минимальный запуск через Docker CLI

```bash
docker run -d \
  --name mkmudocs \
  -v $(pwd)/my-content/pages:/pages \
  -p 4242:4242/tcp \
  -p 4242:4242/udp \
  -e NOMADNET_NODE_NAME=MyNode \
  -e SITE_NAME="My Site" \
  mkmudocs:latest
```

---

## Сборка и публикация образа

```bash
# Сборка образа
docker build -t mkmudocs:latest .

# Тестирование
docker run -d --name test -v $(pwd)/my-content/pages:/pages -p 4242:4242 mkmudocs:latest

# Публикация на Docker Hub
docker login
docker tag mkmudocs:latest yourusername/mkmudocs:latest
docker push yourusername/mkmudocs:latest
```

---

## Как это работает

1. **Инициализация:** При запуске `entrypoint.sh` создает необходимые каталоги, генерирует конфигурационные файлы Reticulum и NomadNet на основе переменных окружения.
2. **Первоначальная сборка:** Запускается `builder.py`, который сканирует `/pages`, конвертирует Markdown в Micron, обрабатывает ассеты (изображения/файлы) и генерирует индексы.
3. **Мониторинг:** В фоновом режиме работает `watcher.py`. При любом создании, изменении или удалении `.md` файла он инициирует полную пересборку сайта (с защитой от множественных срабатываний — debounce).
4. **Публикация:** Демон NomadNet, запущенный в том же контейнере, автоматически подхватывает изменения в выходном каталоге (`/data/output`) и анонсирует их в сети (по умолчанию каждые 60 секунд).

---

## Логи и отладка

```bash
# Просмотр логов в реальном времени
docker compose logs -f

# Просмотр только последних 100 строк
docker compose logs --tail=100

# Вход в контейнер для отладки (проверка сгенерированных файлов)
docker compose exec mkmudocs /bin/bash
```

---

## Лицензия

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) - see the [LICENSE](LICENSE) file for details.

This software uses the following GPL-3.0 licensed components:
- [Reticulum Network Stack](https://github.com/markqvist/Reticulum)
- [LXMF](https://github.com/markqvist/LXMF)

## Благодарности

Проект вдохновлен простотой [MkDocs](https://www.mkdocs.org/) и адаптирован для децентрализованной сети [NomadNet](https://nomadnet.org/) и формата разметки [Micron](https://github.com/acehoss/nomadnet).
