# MkMuDocs


> ⚠️ **A Note for Non-Russian Speakers**
> 
> I am a Russian-speaking developer and initially created this project primarily for myself. The page templates are adapted mainly for the Russian language.
> 
> If you wish, you can improve the project by creating a fork or simply modifying the files in the `templates/` directory to adapt them for your native language.
> 
> In the future, I may implement language selection via the `.env` file and multilingual support, but this is not yet implemented at the current stage.

Automatic site generator for the NomadNet network from Markdown files with real-time change monitoring.

💡 **MkMuDocs** — pronounced as *"Make My Docs"*, reflecting the essence of the project: you write Markdown, and the system automatically creates a ready-to-use NomadNet site for you.

## Features

✅ Automatic Markdown → Micron (`.mu`) conversion  
✅ Real-time change monitoring via `watchdog`  
✅ Automatic image processing (WebP conversion, size optimization)  
✅ Automatic file processing and deduplication (saved in `files/` directory)  
✅ YAML frontmatter support for metadata  
✅ Automatic generation of directory indexes and tag pages  
✅ `prev`/`next` navigation between pages  
✅ Default connection to public NomadNet nodes  
✅ Flexible configuration via environment variables  
✅ Automatic directory creation with correct permissions inside the container  

---

## Quick Start

### 1. Prepare Directory Structure

Create a directory for your content on the host machine:

```bash
mkdir -p my-content/pages
```

### 2. Add Markdown Files

Create your first file. The main page (`index.mu`) and node service file (`node.info`) will be generated automatically inside the container based on templates and environment variables, so there's no need to create them manually.

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
```

### 5. Done!

The site will be automatically generated inside the container and published to the NomadNet network. You can view the logs with:

```bash
docker compose logs -f
```

---

## Project Structure (on Host Machine)

Users work only with source files and templates. Output `.mu` files are generated and stored exclusively inside the container.

```text
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
│   └── micron.py               # Micron markup generator
├── templates/                  # Jinja2 templates
│   ├── index.mu.j2             # Main page
│   ├── page.mu.j2              # Content page
│   ├── dir_index.mu.j2         # Directory index
│   ├── tag.mu.j2               # Tag page
│   ├── tags_index.mu.j2        # All tags index
│   ├── node.info.j2            # Node service information
│   ├── menu.mu.j2              # Navigation menu component
│   └── divider.mu.j2           # Divider component
└── my-content/                 # Your content (mounted into container)
    └── pages/                  # Markdown files, images files and over
        └── about.md
```

---

## Internal Structure and URL Logic in NomadNet

MkMuDocs automatically creates the following structure in the output directory (`/data/output`), which the NomadNet daemon sees:

```text
/data/output/
├── index.mu                  # Main page (auto-generated)
├── node.info                 # Node information (auto-generated)
├── about.mu                  # Generated pages (in root or subdirectories)
├── category/                 # Subdirectories mirroring /pages/ structure
│   ├── index.mu              # Subdirectory index (auto-generated)
│   └── page1.mu              # Content page
├── media/                    # Optimized images (WebP)
│   └── photo.webp
├── files/                    # Downloadable files (with deduplication)
│   └── document.pdf
└── tags/                     # Tag pages
    ├── index.mu              # All tags index (auto-generated)
    └── tutorial.mu           # Specific tag page
```

> **⚠️ Important about paths in NomadNet:**  
> In the NomadNet network, URLs have the format `:/content_type/path_to_file`. The content type is determined by the daemon for routing, not by the physical folder:
> - **Pages:** `:/page/about.mu` (type `page`, physically the file `about.mu` is in the root of `/data/output/` or in the corresponding subdirectory).
> - **Images:** `:/media/media/photo.webp` (type `media`, physical folder `media/` inside `/data/output/`).
> - **Files:** `:/file/document.pdf` (type `file`, physical folder `files/` inside `/data/output/`, which the daemon receives in `entrypoint.sh` as `files_path = ${SITE_DIR}/files` and serves as the root of file resources).

---

## Markdown Syntax

### Frontmatter

Use YAML frontmatter at the beginning of the file for metadata:

```markdown
---
title: Page Title
author: Author Name
date: 2024-01-15
tags: [nomadnet, tutorial, python]
---

# Heading
Page content...
```

### Images

```markdown
![Image description](./images/photo.jpg)
```
Images are automatically converted to WebP, optimized by size, and become available at `:/media/media/filename.webp`.

### Files

```markdown
[Download document](./files/document.pdf)
```
Files are copied to the `files/` directory with original names preserved and deduplicated by hash. Thanks to the `files_path` setting in `entrypoint.sh`, they become available at the correct path `:/file/document.pdf`.

### Internal Links

```markdown
[Another page](./other-page.md)
[Page in subdirectory](./category/page.md)
```
Links to `.md` files are automatically converted to Micron `.mu` format with correct paths (`:/page/...`).

### Tags

Hashtags in text automatically become clickable links to tag pages:

```markdown
This is a page about #nomadnet and #tutorial
```

### Tables, Code Blocks, and Highlighting

Standard Markdown constructs are supported, which are converted to native Micron syntax:

```markdown
| Column 1 | Column 2 |
|----------|----------|
| Cell 1   | Cell 2   |
```
```python
def hello():
    print("Hello, NomadNet!")
```
```
==Highlighted text==
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NOMADNET_NODE_NAME` | Node name in the network | `MyNomadSite` |
| `NOMADNET_NODE_DESCRIPTION` | Node description | `NomadNet Site` |
| `NOMADNET_OWNER` | Node owner | `Anonymous` |
| `NOMADNET_CONTACT` | Contact information | *(empty)* |
| `NOMADNET_PORT` | TCP/UDP port | `4242` |
| `NOMADNET_PEER_NODES` | Nodes to connect to (comma-separated) | `nomad.network:4242,...` |
| `SITE_NAME` | Site name | `My NomadNet Site` |
| `SITE_DESCRIPTION` | Site description | *(empty)* |
| `HOST_PAGES_DIR` | Path to Markdown files on host | `./my-content/pages` |
| `HOST_CONFIG_DIR` | Path to configuration on host | `./my-config` |
| `ENABLE_AUTO_INTERFACE` | Local network discovery | `true` |
| `ENABLE_TCP_SERVER` | TCP server startup | `true` |
| `ENABLE_I2P` | I2P network support | `false` |
| `RETICULUM_ENABLE_TRANSPORT` | Transport node mode | `false` |
| `AUTO_GROUP_ID` | Auto Interface group ID | `nomadnet` |
| `PUID` / `PGID` | User UID/GID for file permissions | `1000` |
| `IMAGE_MAX_WIDTH` | Maximum image width (px) | `1200` |
| `IMAGE_QUALITY` | WebP quality (1-100) | `85` |
| `DATE_FORMAT` | Date format in templates | `%Y-%m-%d %H:%M` |

---

## Usage Examples

### Docker Compose (Recommended Method)

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

Launch:
```bash
docker compose up -d
```

### Minimal Launch via Docker CLI

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

## Building and Publishing the Image

```bash
# Build the image
docker build -t mkmudocs:latest .

# Testing
docker run -d --name test -v $(pwd)/my-content/pages:/pages -p 4242:4242 mkmudocs:latest

# Publish to Docker Hub
docker login
docker tag mkmudocs:latest yourusername/mkmudocs:latest
docker push yourusername/mkmudocs:latest
```

---

## How It Works

1. **Initialization:** When launched, `entrypoint.sh` creates the necessary directories and generates Reticulum and NomadNet configuration files based on environment variables.
2. **Initial Build:** `builder.py` runs, which scans `/pages`, converts Markdown to Micron, processes assets (images/files), and generates indexes.
3. **Monitoring:** `watcher.py` runs in the background. When any `.md` file is created, modified, or deleted, it initiates a full site rebuild (with protection against multiple triggers — debounce).
4. **Publication:** The NomadNet daemon, running in the same container, automatically picks up changes in the output directory (`/data/output`) and announces them to the network (by default every 60 seconds).

---

## Logs and Debugging

```bash
# View logs in real-time
docker compose logs -f

# View only the last 100 lines
docker compose logs --tail=100

# Enter the container for debugging (check generated files)
docker compose exec mkmudocs /bin/bash
```

---

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) - see the [LICENSE](LICENSE) file for details.

This software uses the following GPL-3.0 licensed components:
- [Reticulum Network Stack](https://github.com/markqvist/Reticulum)
- [LXMF](https://github.com/markqvist/LXMF)

## Acknowledgments

The project is inspired by the simplicity of [MkDocs](https://www.mkdocs.org/) and adapted for the decentralized network [NomadNet](https://nomadnet.org/) and the markup format [Micron](https://github.com/acehoss/nomadnet).
