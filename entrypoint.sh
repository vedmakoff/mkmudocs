#!/bin/bash
set -e

echo "========================================="
echo "NomadNet Site Builder"
echo "========================================="
echo "Узел: ${NOMADNET_NODE_NAME}"
echo "Порт: ${NOMADNET_PORT}"
echo "Сайт: ${SITE_NAME}"
echo "Markdown: ${PAGES_DIR}"
echo "Output: ${SITE_DIR}"
echo "Config: ${CONFIG_DIR}"
echo "========================================="

# Создание каталогов
create_dir() {
    if [ ! -d "$1" ]; then
        echo "Создание: $1"
        mkdir -p "$1"
    fi
}

create_dir "$PAGES_DIR"
create_dir "$SITE_DIR"
create_dir "$SITE_DIR/files"
create_dir "${CONFIG_DIR}"
create_dir "${CONFIG_DIR}/storage"
create_dir "${CONFIG_DIR}/reticulum"
create_dir "${CONFIG_DIR}/nomadnet"

echo "Установка прав (UID: $PUID, GID: $PGID)..."
chown -R $PUID:$PGID "$PAGES_DIR" 2>/dev/null || true
chown -R $PUID:$PGID "$SITE_DIR" 2>/dev/null || true
chown -R $PUID:$PGID "$CONFIG_DIR" 2>/dev/null || true

# ============================================
# Генерация конфигурации Reticulum
# ============================================
echo "Генерация конфигурации Reticulum..."

cat > "${CONFIG_DIR}/reticulum/config" <<EOF
[reticulum]
enable_transport = ${RETICULUM_ENABLE_TRANSPORT}
share_instance = ${RETICULUM_SHARE_INSTANCE}

[logging]
loglevel = 1
destination = stderr

[interfaces]
EOF

if [ "${ENABLE_AUTO_INTERFACE}" = "true" ]; then
    cat >> "${CONFIG_DIR}/reticulum/config" <<EOF

[[Auto Interface]]
type = AutoInterface
enabled = yes
discover_path = yes
group_id = ${AUTO_GROUP_ID}
EOF
fi

if [ "${ENABLE_TCP_SERVER}" = "true" ]; then
    cat >> "${CONFIG_DIR}/reticulum/config" <<EOF

[[TCP Server]]
type = TCPServerInterface
enabled = yes
listen_ip = 0.0.0.0
listen_port = ${NOMADNET_PORT}
EOF
fi

# Добавляем TCP Client интерфейсы для подключения к пирам
if [ -n "${NOMADNET_PEER_NODES}" ]; then
    IFS=',' read -ra PEERS <<< "$NOMADNET_PEER_NODES"
    for i in "${!PEERS[@]}"; do
        peer="${PEERS[$i]}"
        host=$(echo "$peer" | cut -d':' -f1)
        port=$(echo "$peer" | cut -d':' -f2)
        
        if [ -z "$port" ] || [ "$port" = "$host" ]; then
            port=4242
        fi
        
        cat >> "${CONFIG_DIR}/reticulum/config" <<EOF

[[TCP Client $i]]
type = TCPClientInterface
enabled = yes
target_host = $host
target_port = $port
EOF
    done
fi

echo "Reticulum конфигурация создана."

# ============================================
# Генерация конфигурации NomadNet
# ============================================
echo "Генерация конфигурации NomadNet..."

cat > "${CONFIG_DIR}/nomadnet/config" <<EOF
[client]
enable_client = no
enable_lxmf = no

[node]
enable_node = yes
node_name = ${NOMADNET_NODE_NAME}
announce_at_start = yes
announce_interval = 60

# Отключаем встроенный propagation node, чтобы избежать бага с RNS в LXMF
disable_propagation = Yes

# Путь к сгенерированным страницам
pages_path = ${SITE_DIR}
files_path = ${SITE_DIR}/files
# периодичность пересканирования каталога со страницами
page_refresh_interval = 1
EOF

echo "NomadNet конфигурация создана."

# ============================================
# Запуск сервисов
# ============================================
echo "Первоначальная сборка сайта..."
python -u -m src.builder

echo "Запуск мониторинга файлов (watchdog)..."
python -u -m src.watcher 2>&1 &
WATCHER_PID=$!

echo "Запуск NomadNet в режиме демона..."
nomadnet --config "${CONFIG_DIR}/nomadnet" --rnsconfig "${CONFIG_DIR}/reticulum" --daemon 2>&1 &
NOMADNET_PID=$!

echo "========================================="
echo "✅ Сервисы запущены!"
echo "========================================="

# Даем демону 2 секунды на создание лог-файла
sleep 2

# Ищем лог-файл и выводим его в главный поток Docker (чтобы мы его видели в docker compose logs)
LOG_FILE=$(find /data/config -name "logfile" -type f 2>/dev/null | head -n 1)

if [ -n "$LOG_FILE" ]; then
    echo "📜 Поток логов NomadNet активирован: $LOG_FILE"
    echo "========================================="
    # tail -f удерживает контейнер от закрытия и показывает логи демона в реальном времени
    tail -f "$LOG_FILE"
else
    echo "⚠️ Лог-файл не найден, но демон работает. Контейнер остается активным благодаря watchdog."
    # Удерживаем контейнер активным, пока работает watchdog
    wait $WATCHER_PID
fi