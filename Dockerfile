FROM python:3.11-slim

LABEL maintainer="vedmakoff"
LABEL description="NomadNet site builder from Markdown files"
LABEL version="1.0.0"

WORKDIR /app

# Минимальные системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Исходный код
COPY src/ ./src/
COPY templates/ ./templates/
COPY entrypoint.sh .
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Пути
ENV PAGES_DIR=/pages \
    SITE_DIR=/data/output \
    CONFIG_DIR=/data/config \
    TEMPLATES_DIR=/app/templates \
    DATA_DIR=/data

# Настройки узла
ENV NOMADNET_NODE_NAME="MyNomadSite" \
    NOMADNET_NODE_DESCRIPTION="NomadNet Site" \
    NOMADNET_OWNER="Anonymous" \
    NOMADNET_CONTACT="" \
    NOMADNET_PORT=4242 \
    NOMADNET_PEER_NODES="nomad.network:4242,reticulum.network:4242,us.nomadnet.org:4242"

# Настройки сайта
ENV SITE_NAME="My NomadNet Site" \
    SITE_DESCRIPTION="" \
    DATE_FORMAT="%Y-%m-%d %H:%M"

# Интерфейсы Reticulum
ENV ENABLE_AUTO_INTERFACE=true \
    ENABLE_TCP_SERVER=true \
    ENABLE_I2P=false \
    AUTO_GROUP_ID=nomadnet_auto \
    RETICULUM_ENABLE_TRANSPORT=true \
    RETICULUM_SHARE_INSTANCE=false \
    PROPAGATION_ENABLED=false

# Права
ENV PUID=1000 \
    PGID=1000

# Режим работы
ENV AUTO_REBUILD=true \
    LOG_LEVEL=INFO

# Порты
EXPOSE 4242/tcp
EXPOSE 4242/udp

# Том
VOLUME ["/data"]

ENTRYPOINT ["./entrypoint.sh"]