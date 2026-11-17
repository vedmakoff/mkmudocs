# MkMuDocs

Автоматический генератор сайтов для сети NomadNet из Markdown-файлов с мониторингом изменений в реальном времени.

💡 **MkMuDocs** — читается как "Make My Docs" (сделай мои документы), что отражает суть проекта: вы пишете Markdown, а система автоматически создаёт для вас готовый NomadNet сайт.

## Возможности

- ✅ Автоматическая конвертация Markdown → Micron (`.mu`)
- ✅ Мониторинг изменений в реальном времени через `watchdog`
- ✅ Полнотекстовый поиск по сайту — форма доступна в меню на каждой странице
- ✅ Автоматическая обработка изображений (конвертация в WebP, оптимизация размера)
- ✅ Автоматическая обработка и дедупликация файлов (каталог `files/`)
- ✅ Поддержка YAML frontmatter для метаданных
- ✅ Автоматическая генерация индексов каталогов с любой глубиной вложенности
- ✅ Страницы тегов и индекс всех тегов
- ✅ Навигация `prev` / `next` между страницами
- ✅ Таблицы, блоки кода, `==подсветка==`, сворачиваемые блоки `<details>`
- ✅ Поддержка динамических страниц (формируются в момент запроса)
- ✅ Подключение к публичным узлам NomadNet по умолчанию
- ✅ Гибкая настройка через переменные окружения
- ✅ Автоматическое создание каталогов с правильными правами внутри контейнера

## Быстрый старт

### 1. Подготовка структуры каталогов

```bash
mkdir -p my-content/pages
```

### 2. Добавьте Markdown-файлы

Главная страница (`index.mu`) и служебный файл узла (`node.info`) генерируются автоматически внутри контейнера — создавать их вручную не нужно.

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
- Полнотекстовый поиск
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
docker compose logs -f
```

Сайт автоматически сгенерируется внутри контейнера и будет опубликован в сети NomadNet.

## Структура проекта (на хост-машине)

Пользователь работает только с исходными файлами и шаблонами. Выходные `.mu` файлы генерируются и хранятся исключительно внутри контейнера.

```
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
│   ├── micron.py               # Генератор Micron-разметки
│   └── dynamic/                # Динамические страницы
│       └── search.mu           # Страница поиска
├── templates/                  # Jinja2 шаблоны
│   ├── index.mu.j2             # Главная страница
│   ├── page.mu.j2              # Страница контента
│   ├── dir_index.mu.j2         # Индекс каталога
│   ├── tag.mu.j2               # Страница тега
│   ├── tags_index.mu.j2        # Индекс всех тегов
│   ├── node.info.j2            # Служебная информация об узле
│   ├── menu.mu.j2              # Меню навигации + форма поиска
│   └── divider.mu.j2           # Компонент разделителя
└── my-content/                 # Ваш контент (путь задаётся в .env)
    └── pages/                  # .md файлы, изображения, документы
        └── about.md
```

## Внутренняя структура и логика URL в NomadNet

MkMuDocs автоматически создаёт следующую структуру в выходном каталоге (`/data/output`):

```
/data/output/
├── index.mu                  # Главная страница (автогенерация)
├── node.info                 # Информация об узле (автогенерация)
├── menu.mu                   # Готовая шапка для динамических страниц
├── footer.mu                 # Готовый подвал: имя узла + дата сборки
├── search.mu                 # Страница поиска
├── search_index.json         # Поисковый индекс (автогенерация)
├── about.mu                  # Сгенерированные страницы
├── category/                 # Подкаталоги, повторяющие структуру /pages/
│   ├── index.mu              # Индекс раздела (страницы + вложенные каталоги)
│   ├── page1.mu
│   └── subcategory/          # Вложенность любой глубины
│       ├── index.mu
│       └── page2.mu
├── media/                    # Оптимизированные изображения (WebP)
│   └── photo.webp
├── files/                    # Файлы для скачивания (с дедупликацией)
│   └── document.pdf
└── tags/                     # Страницы тегов
    ├── index.mu
    └── tutorial.mu
```

> ⚠️ **Важно о путях в NomadNet**
>
> URL имеют формат `:/тип_контента/путь_к_файлу`. Тип контента определяется демоном для маршрутизации, а не физической папкой:
>
> - **Страницы:** `:/page/about.mu` — файл `about.mu` в корне `/data/output/` или в подкаталоге
> - **Изображения:** `:/media/media/photo.webp` — физическая папка `media/` внутри `/data/output/`
> - **Файлы:** `:/file/document.pdf` — физическая папка `files/`, которую демон получает как `files_path = ${SITE_DIR}/files`
> - **Поиск:** `:/page/search.mu`

## Поиск по сайту

На сайте есть полнотекстовый поиск, и он доступен **с любой страницы** — не нужно сначала куда-то переходить.

### Как пользоваться

1. В строке меню под навигацией находится поле ввода и кнопка 🔍
2. Введите слово или несколько слов
3. Нажмите 🔍 — откроется страница результатов
4. Кликните по названию найденной страницы, чтобы перейти к ней

Страница результатов оформлена в том же стиле, что и остальные страницы сайта: то же меню, заголовок, разделители и подвал с именем узла. Поле поиска в меню остаётся на месте — можно сразу искать снова, не возвращаясь назад.

### Что ищет

Поиск проходит по **заголовкам, тегам и тексту** всех страниц. Регистр не важен, слова ищутся по подстроке — можно вводить часть слова. Страницы, где совпадение найдено в заголовке, поднимаются выше в выдаче. Для каждого результата показывается небольшой фрагмент текста вокруг найденного слова, чтобы было понятно, о чём страница.

### Что стоит знать

- Минимальная длина слова — **2 символа**
- На странице показывается до **20 результатов**; если найдено больше, уточните запрос
- Индекс пересобирается автоматически при каждом изменении `.md` файлов — новые и отредактированные страницы попадают в поиск сразу, без ручных действий
- Отдельная страница поиска доступна по адресу `:/page/search.mu`

## Динамические страницы

Помимо обычных `.mu` файлов проект умеет отдавать страницы, которые формируются в момент запроса — именно так работает поиск. NomadNet запускает исполняемый файл из каталога страниц и отдаёт клиенту его вывод.

Чтобы добавить свою такую страницу:

1. Положите скрипт в `src/dynamic/` — например `src/dynamic/guestbook.mu`
2. Начните файл с шебанга `#!/usr/bin/env python3`
3. Перезапустите контейнер — билдер скопирует файл в выходной каталог и выставит права на исполнение
4. Страница будет доступна по адресу `:/page/guestbook.mu`

Шапку и подвал билдер готовит заранее — это файлы `menu.mu` и `footer.mu` в выходном каталоге. Достаточно вывести их содержимое, и страница получит то же меню и тот же подвал, что и весь остальной сайт.

## Markdown-синтаксис

### Frontmatter

```yaml
---
title: Название страницы
author: Имя автора
date: 2024-01-15
tags: [nomadnet, tutorial, python]
---
```

Если `title` не указан, берётся первый заголовок `#` из текста, а если и его нет — имя файла. Дата по умолчанию берётся из времени изменения файла.

### Изображения

```markdown
![Описание изображения](./images/photo.jpg)
```

Конвертируются в WebP, оптимизируются по размеру и доступны по `:/media/media/filename.webp`.

### Файлы

```markdown
[Скачать документ](./files/document.pdf)
```

Копируются в `files/` с сохранением оригинальных имён и дедупликацией по хешу, доступны по `:/file/document.pdf`.

### Внутренние ссылки

```markdown
[Другая страница](./other-page.md)
[Страница в подкаталоге](./category/page.md)
```

Автоматически преобразуются в `:/page/...` с расширением `.mu`.

### Теги

```markdown
Это страница про #nomadnet и #tutorial
```

Хештеги становятся кликабельными ссылками на страницы тегов и участвуют в поиске.

### Таблицы, код, выделение

Поддерживаются таблицы, блоки кода с подписью языка, инлайн-код и `==подсвеченный текст==`.

### Сворачиваемые блоки

```markdown
<details>
<summary>Подробнее</summary>

Скрытый текст с **Markdown** внутри.

</details>
```

Преобразуются в нативные фолды Micron. Атрибут `open` разворачивает блок по умолчанию.

### Вложенные каталоги

Структура каталогов любой глубины повторяется автоматически. Индекс раздела показывает и страницы, и вложенные подразделы с количеством страниц в каждом.

## Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `NOMADNET_NODE_NAME` | Имя узла в сети | `MyNomadSite` |
| `NOMADNET_NODE_DESCRIPTION` | Описание узла | `NomadNet Site` |
| `NOMADNET_OWNER` | Владелец узла | `Anonymous` |
| `NOMADNET_CONTACT` | Контактная информация | (пусто) |
| `NOMADNET_PORT` | Порт TCP/UDP | `4242` |
| `NOMADNET_PEER_NODES` | Узлы для подключения (через запятую) | `nomad.network:4242,...` |
| `SITE_NAME` | Название сайта | `My NomadNet Site` |
| `SITE_DESCRIPTION` | Описание сайта | (пусто) |
| `HOST_PAGES_DIR` | Путь к Markdown-файлам на хосте | `./my-content/pages` |
| `HOST_CONFIG_DIR` | Путь к конфигурации на хосте | `./my-config` |
| `ENABLE_AUTO_INTERFACE` | Обнаружение в локальной сети | `true` |
| `ENABLE_TCP_SERVER` | Запуск TCP-сервера | `true` |
| `ENABLE_I2P` | Поддержка сети I2P | `false` |
| `RETICULUM_ENABLE_TRANSPORT` | Режим транспортного узла | `false` |
| `AUTO_GROUP_ID` | ID группы Auto Interface | `nomadnet` |
| `PUID` / `PGID` | UID/GID пользователя для прав на файлы | `1000` |
| `IMAGE_MAX_WIDTH` | Максимальная ширина изображений (px) | `1200` |
| `IMAGE_QUALITY` | Качество WebP (1–100) | `85` |
| `DATE_FORMAT` | Формат даты в шаблонах | `%Y-%m-%d %H:%M` |

## Примеры использования

### Docker Compose (рекомендуемый способ)

```yaml
services:
  nomadnet-site:
    build: .
    image: nomadnet-site-builder:latest
    container_name: nomadnet-site
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

```bash
docker compose up -d
```

### Минимальный запуск через Docker CLI

```bash
docker run -d \
  --name nomadnet-site \
  -v $(pwd)/my-content/pages:/pages \
  -p 4242:4242/tcp \
  -p 4242:4242/udp \
  -e NOMADNET_NODE_NAME=MyNode \
  -e SITE_NAME="My Site" \
  nomadnet-site-builder:latest
```

### Сборка и публикация образа

```bash
docker build -t mkmudocs:latest .
docker run -d --name test -v $(pwd)/my-content/pages:/pages -p 4242:4242 mkmudocs:latest

docker login
docker tag mkmudocs:latest yourusername/mkmudocs:latest
docker push yourusername/mkmudocs:latest
```

## Как это работает

1. **Инициализация.** `entrypoint.sh` создаёт каталоги, выставляет права и генерирует конфиги Reticulum и NomadNet из переменных окружения.
2. **Сборка.** `builder.py` сканирует `/pages`, конвертирует Markdown в Micron, обрабатывает изображения и файлы, генерирует индексы каталогов и страницы тегов.
3. **Поиск.** Собирается поисковый индекс по всем страницам, страница поиска устанавливается в выходной каталог.
4. **Оформление.** Рендерятся `menu.mu` и `footer.mu` — общая шапка и подвал, которые используют динамические страницы.
5. **Мониторинг.** `watcher.py` следит за `.md` в `/pages` и запускает полную пересборку с защитой от множественных срабатываний (debounce).
6. **Публикация.** Демон NomadNet в том же контейнере подхватывает изменения (`page_refresh_interval = 1`) и анонсирует узел каждые 60 секунд.

> ℹ️ Watchdog реагирует только на `.md` файлы в `/pages`. После правки шаблонов в `templates/` или скриптов в `src/dynamic/` нужен перезапуск: `docker compose restart nomadnet-site`.

## Логи и отладка

```bash
# Логи в реальном времени
docker compose logs -f

# Последние 100 строк
docker compose logs --tail=100

# Войти в контейнер
docker compose exec nomadnet-site /bin/bash

# Посмотреть сгенерированные файлы
docker compose exec nomadnet-site ls -l /data/output
```

Проверить поиск, не заходя в сеть:

```bash
# Пустая форма
docker compose exec nomadnet-site python3 /data/output/search.mu

# Результаты по запросу
docker compose exec -e field_query=привет nomadnet-site python3 /data/output/search.mu
```

Если страница поиска отдаётся как исходный код вместо результатов — проверьте, что у файла есть права на исполнение:

```bash
docker compose exec nomadnet-site ls -l /data/output/search.mu
# ожидается -rwxr-xr-x
```

## Лицензия

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) — see the [LICENSE](LICENSE) file for details.

This software uses the following GPL-3.0 licensed components:

- [Reticulum Network Stack](https://github.com/markqvist/Reticulum)
- [LXMF](https://github.com/markqvist/LXMF)

## Благодарности

Проект вдохновлён простотой [MkDocs](https://www.mkdocs.org/) и адаптирован для децентрализованной сети [NomadNet](https://nomadnet.org/) и формата разметки Micron.