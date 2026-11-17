# MkMuDocs

⚠️ **A Note for Non-Russian Speakers**

I am a Russian-speaking developer and initially created this project primarily for myself. The page templates are adapted mainly for the Russian language.

If you wish, you can improve the project by creating a fork or simply modifying the files in the `templates/` directory to adapt them for your native language. Note that the search page (`src/dynamic/search.mu`) also contains Russian UI strings — they are plain `print()` calls and easy to translate.

In the future, I may implement language selection via the `.env` file and multilingual support, but this is not yet implemented at the current stage.

---

Automatic site generator for the NomadNet network from Markdown files with real-time change monitoring.

💡 **MkMuDocs** — pronounced as "Make My Docs", reflecting the essence of the project: you write Markdown, and the system automatically creates a ready-to-use NomadNet site for you.

## Features

- ✅ Automatic Markdown → Micron (`.mu`) conversion
- ✅ Real-time change monitoring via `watchdog`
- ✅ **Full-text site search** — the form is available in the menu on every page
- ✅ Automatic image processing (WebP conversion, size optimization)
- ✅ Automatic file processing and deduplication (`files/` directory)
- ✅ YAML frontmatter support for metadata
- ✅ Automatic generation of directory indexes **with any nesting depth**
- ✅ Tag pages and an index of all tags
- ✅ `prev` / `next` navigation between pages
- ✅ Tables, code blocks, `==highlighting==`, collapsible `<details>` blocks
- ✅ Dynamic page support (generated at request time)
- ✅ Default connection to public NomadNet nodes
- ✅ Flexible configuration via environment variables
- ✅ Automatic directory creation with correct permissions inside the container

## Quick Start

### 1. Prepare Directory Structure

```bash
mkdir -p my-content/pages
```

### 2. Add Markdown Files

The main page (`index.mu`) and the node service file (`node.info`) are generated automatically inside the container — there is no need to create them manually.

```bash
cat > my-content/pages/about.md << 'EOF'
---
title: About the Project
author: Your Name
tags: [nomadnet, tutorial]
---

# About the Project

This is my NomadNet site created with **MkMuDocs**.

## Features

- Automatic conversion from Markdown
- Real-time change monitoring
- Image and file support
- Full-text search
- Automatic tag and index generation

Simply add `.md` files to the `pages/` directory, and they will automatically appear in the NomadNet network.

#nomadnet #tutorial
EOF
```

### 3. Create `.env` File

```bash
cat > .env << 'EOF'
# Basic settings
NOMADNET_NODE_NAME=MyNomadNode
NOMADNET_NODE_DESCRIPTION=My NomadNet site
NOMADNET_OWNER=Anonymous
NOMADNET_CONTACT=

# Network
NOMADNET_PORT=4242
NOMADNET_PEER_NODES=nomad.network:4242,reticulum.network:4242,us.nomadnet.org:4242

# Site
SITE_NAME=My NomadNet Site
SITE_DESCRIPTION=Automatically generated site

# Host paths
HOST_PAGES_DIR=./my-content/pages
HOST_CONFIG_DIR=./my-config

# Interfaces
ENABLE_AUTO_INTERFACE=true
ENABLE_TCP_SERVER=true
ENABLE_I2P=false
RETICULUM_ENABLE_TRANSPORT=false
AUTO_GROUP_ID=nomadnet

# User (must match file owner on host)
PUID=1000
PGID=1000

# Images
IMAGE_MAX_WIDTH=1200
IMAGE_QUALITY=85

# Date format
DATE_FORMAT=%Y-%m-%d %H:%M
EOF
```

### 4. Start the Container

```bash
docker compose up -d
docker compose logs -f
```

The site will be generated automatically inside the container and published to the NomadNet network.

## Project Structure (on Host Machine)

Users work only with source files and templates. Output `.mu` files are generated and stored exclusively inside the container.

```
.
├── docker-compose.yml          # Docker Compose V2 configuration
├── Dockerfile                  # Image build instructions
├── entrypoint.sh               # Initialization and startup script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (created manually)
├── src/                        # Generator source code
│   ├── __init__.py
│   ├── builder.py              # Main site builder
│   ├── watcher.py              # Change monitoring
│   ├── converter.py            # Markdown → Micron converter
│   ├── micron.py               # Micron markup generator
│   └── dynamic/                # Dynamic pages
│       └── search.mu           # Search page
├── templates/                  # Jinja2 templates
│   ├── index.mu.j2             # Main page
│   ├── page.mu.j2              # Content page
│   ├── dir_index.mu.j2         # Directory index
│   ├── tag.mu.j2               # Tag page
│   ├── tags_index.mu.j2        # All tags index
│   ├── node.info.j2            # Node service information
│   ├── menu.mu.j2              # Navigation menu + search form
│   └── divider.mu.j2           # Divider component
└── my-content/                 # Your content (path set in .env)
    └── pages/                  # .md files, images, documents
        └── about.md
```

## Internal Structure and URL Logic in NomadNet

MkMuDocs automatically creates the following structure in the output directory (`/data/output`):

```
/data/output/
├── index.mu                  # Main page (auto-generated)
├── node.info                 # Node information (auto-generated)
├── menu.mu                   # Ready-made header for dynamic pages
├── footer.mu                 # Ready-made footer: node name + build date
├── search.mu                 # Search page
├── search_index.json         # Search index (auto-generated)
├── about.mu                  # Generated pages
├── category/                 # Subdirectories mirroring /pages/ structure
│   ├── index.mu              # Section index (pages + nested directories)
│   ├── page1.mu
│   └── subcategory/          # Any nesting depth
│       ├── index.mu
│       └── page2.mu
├── media/                    # Optimized images (WebP)
│   └── photo.webp
├── files/                    # Downloadable files (with deduplication)
│   └── document.pdf
└── tags/                     # Tag pages
    ├── index.mu
    └── tutorial.mu
```

> ⚠️ **Important about paths in NomadNet**
>
> URLs have the format `:/content_type/path_to_file`. The content type is determined by the daemon for routing, not by the physical folder:
>
> - **Pages:** `:/page/about.mu` — the file `about.mu` in the root of `/data/output/` or in a subdirectory
> - **Images:** `:/media/media/photo.webp` — physical folder `media/` inside `/data/output/`
> - **Files:** `:/file/document.pdf` — physical folder `files/`, which the daemon receives as `files_path = ${SITE_DIR}/files`
> - **Search:** `:/page/search.mu`

## Site Search

The site has full-text search, and it is available **from any page** — you don't need to navigate anywhere first.

### How to use it

1. In the menu bar, below the navigation links, there is an input field and a 🔍 button
2. Type a word or several words
3. Press 🔍 — the results page opens
4. Click a page title to open it

The results page uses the same layout as every other page on the site: the same menu, heading, dividers, and footer with the node name. The search field stays in the menu, so you can search again immediately without going back.

### What it searches

Search covers **titles, tags, and body text** of all pages. It is case-insensitive and matches substrings, so you can type part of a word. Pages where the match appears in the title rank higher in the results. Each result shows a short text fragment around the match, so you can tell what the page is about.

### Good to know

- Minimum word length is **2 characters**
- Up to **20 results** are shown per page; if more are found, narrow your query
- The index is rebuilt automatically whenever `.md` files change — new and edited pages become searchable right away, with no manual steps
- The standalone search page is available at `:/page/search.mu`

## Dynamic Pages

Besides regular `.mu` files, the project can serve pages that are generated at request time — this is exactly how search works. NomadNet executes an executable file from the pages directory and sends its output to the client.

To add your own:

1. Put a script into `src/dynamic/` — for example `src/dynamic/guestbook.mu`
2. Start the file with a shebang: `#!/usr/bin/env python3`
3. Restart the container — the builder copies the file into the output directory and sets executable permissions
4. The page will be available at `:/page/guestbook.mu`

The builder prepares the header and footer in advance — these are the `menu.mu` and `footer.mu` files in the output directory. Just print their contents, and your page gets the same menu and footer as the rest of the site.

## Markdown Syntax

### Frontmatter

```yaml
---
title: Page Title
author: Author Name
date: 2024-01-15
tags: [nomadnet, tutorial, python]
---
```

If `title` is not set, the first `#` heading from the text is used; if there is none, the file name is used. The date defaults to the file's modification time.

### Images

```markdown
![Image description](./images/photo.jpg)
```

Converted to WebP, optimized by size, and available at `:/media/media/filename.webp`.

### Files

```markdown
[Download document](./files/document.pdf)
```

Copied into `files/` with original names preserved and deduplicated by hash, available at `:/file/document.pdf`.

### Internal Links

```markdown
[Another page](./other-page.md)
[Page in subdirectory](./category/page.md)
```

Automatically converted to `:/page/...` with the `.mu` extension.

### Tags

```markdown
This is a page about #nomadnet and #tutorial
```

Hashtags become clickable links to tag pages and are included in search.

### Tables, Code, and Highlighting

Tables, fenced code blocks with a language label, inline code, and `==highlighted text==` are supported.

### Collapsible Blocks

```markdown
<details>
<summary>Read more</summary>

Hidden text with **Markdown** inside.

</details>
```

Converted into native Micron folds. The `open` attribute expands the block by default.

### Nested Directories

Directory structure of any depth is mirrored automatically. A section index lists both pages and nested subsections, with the page count for each.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `NOMADNET_NODE_NAME` | Node name in the network | `MyNomadSite` |
| `NOMADNET_NODE_DESCRIPTION` | Node description | `NomadNet Site` |
| `NOMADNET_OWNER` | Node owner | `Anonymous` |
| `NOMADNET_CONTACT` | Contact information | (empty) |
| `NOMADNET_PORT` | TCP/UDP port | `4242` |
| `NOMADNET_PEER_NODES` | Nodes to connect to (comma-separated) | `nomad.network:4242,...` |
| `SITE_NAME` | Site name | `My NomadNet Site` |
| `SITE_DESCRIPTION` | Site description | (empty) |
| `HOST_PAGES_DIR` | Path to Markdown files on host | `./my-content/pages` |
| `HOST_CONFIG_DIR` | Path to configuration on host | `./my-config` |
| `ENABLE_AUTO_INTERFACE` | Local network discovery | `true` |
| `ENABLE_TCP_SERVER` | TCP server startup | `true` |
| `ENABLE_I2P` | I2P network support | `false` |
| `RETICULUM_ENABLE_TRANSPORT` | Transport node mode | `false` |
| `AUTO_GROUP_ID` | Auto Interface group ID | `nomadnet` |
| `PUID` / `PGID` | User UID/GID for file permissions | `1000` |
| `IMAGE_MAX_WIDTH` | Maximum image width (px) | `1200` |
| `IMAGE_QUALITY` | WebP quality (1–100) | `85` |
| `DATE_FORMAT` | Date format in templates | `%Y-%m-%d %H:%M` |

## Usage Examples

### Docker Compose (Recommended Method)

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

### Minimal Launch via Docker CLI

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

### Building and Publishing the Image

```bash
docker build -t mkmudocs:latest .
docker run -d --name test -v $(pwd)/my-content/pages:/pages -p 4242:4242 mkmudocs:latest

docker login
docker tag mkmudocs:latest yourusername/mkmudocs:latest
docker push yourusername/mkmudocs:latest
```

## How It Works

1. **Initialization.** `entrypoint.sh` creates the required directories, sets permissions, and generates the Reticulum and NomadNet configuration files from environment variables.
2. **Build.** `builder.py` scans `/pages`, converts Markdown to Micron, processes images and files, and generates directory indexes and tag pages.
3. **Search.** A search index is built across all pages, and the search page is installed into the output directory.
4. **Layout.** `menu.mu` and `footer.mu` are rendered — the shared header and footer used by dynamic pages.
5. **Monitoring.** `watcher.py` watches `.md` files in `/pages` and triggers a full rebuild with debounce protection against multiple triggers.
6. **Publication.** The NomadNet daemon, running in the same container, picks up changes (`page_refresh_interval = 1`) and announces the node every 60 seconds.

> ℹ️ The watcher only reacts to `.md` files in `/pages`. After editing templates in `templates/` or scripts in `src/dynamic/`, a restart is required: `docker compose restart nomadnet-site`.

## Logs and Debugging

```bash
# View logs in real-time
docker compose logs -f

# View only the last 100 lines
docker compose logs --tail=100

# Enter the container
docker compose exec nomadnet-site /bin/bash

# List generated files
docker compose exec nomadnet-site ls -l /data/output
```

Check search without connecting to the network:

```bash
# Empty form
docker compose exec nomadnet-site python3 /data/output/search.mu

# Results for a query
docker compose exec -e field_query=hello nomadnet-site python3 /data/output/search.mu
```

If the search page is served as source code instead of results, check that the file has executable permissions:

```bash
docker compose exec nomadnet-site ls -l /data/output/search.mu
# expected: -rwxr-xr-x
```

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) — see the [LICENSE](LICENSE) file for details.

This software uses the following GPL-3.0 licensed components:

- [Reticulum Network Stack](https://github.com/markqvist/Reticulum)
- [LXMF](https://github.com/markqvist/LXMF)

## Acknowledgments

The project is inspired by the simplicity of [MkDocs](https://www.mkdocs.org/) and adapted for the decentralized network [NomadNet](https://nomadnet.org/) and the Micron markup format.