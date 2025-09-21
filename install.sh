#!/bin/bash

# Xray Manager API - Установочный скрипт
# Автоматическая установка и настройка REST API для управления Xray/VLESS

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт должен быть запущен с правами root"
        print_info "Используйте: sudo bash install.sh"
        exit 1
    fi
}

# Определение операционной системы
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        print_error "Не удалось определить операционную систему"
        exit 1
    fi
    
    print_info "Обнаружена ОС: $OS $VERSION"
}

# Установка зависимостей
install_dependencies() {
    print_info "Установка системных зависимостей..."
    
    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y curl wget unzip python3 python3-pip python3-venv git jq
            ;;
        centos|rhel|fedora)
            if command -v dnf &> /dev/null; then
                dnf install -y curl wget unzip python3 python3-pip git jq systemd
            else
                yum install -y curl wget unzip python3 python3-pip git jq systemd
            fi
            ;;
        *)
            print_error "Неподдерживаемая операционная система: $OS"
            exit 1
            ;;
    esac
    
    print_success "Системные зависимости установлены"
}

# Установка Docker (опционально)
install_docker() {
    if command -v docker &> /dev/null; then
        print_info "Docker уже установлен"
        return
    fi
    
    print_info "Установка Docker..."
    
    case $OS in
        ubuntu|debian)
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            rm get-docker.sh
            ;;
        centos|rhel|fedora)
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            rm get-docker.sh
            ;;
    esac
    
    # Установка Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Запуск Docker
    systemctl enable docker
    systemctl start docker
    
    print_success "Docker установлен и запущен"
}

# Установка Xray
install_xray() {
    if command -v xray &> /dev/null; then
        print_info "Xray уже установлен"
        return
    fi
    
    print_info "Установка Xray..."
    
    # Получаем последнюю версию
    XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | jq -r .tag_name)
    
    # Определяем архитектуру
    ARCH=$(uname -m)
    case $ARCH in
        x86_64) ARCH="64" ;;
        aarch64) ARCH="arm64-v8a" ;;
        armv7l) ARCH="arm32-v7a" ;;
        *) print_error "Неподдерживаемая архитектура: $ARCH"; exit 1 ;;
    esac
    
    # Скачиваем и устанавливаем
    wget -O /tmp/xray.zip "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-${ARCH}.zip"
    unzip /tmp/xray.zip -d /tmp/xray/
    
    # Устанавливаем бинарник
    cp /tmp/xray/xray /usr/local/bin/
    chmod +x /usr/local/bin/xray
    
    # Создаем пользователя и директории
    useradd -r -s /usr/sbin/nologin xray || true
    mkdir -p /etc/xray /var/log/xray
    chown xray:xray /var/log/xray
    
    # Создаем systemd сервис
    cat > /etc/systemd/system/xray.service << EOF
[Unit]
Description=Xray Service
Documentation=https://github.com/xtls
After=network.target nss-lookup.target

[Service]
User=xray
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart=/usr/local/bin/xray run -config /etc/xray/config.json
Restart=on-failure
RestartPreventExitStatus=23
LimitNPROC=10000
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
EOF
    
    # Очистка
    rm -rf /tmp/xray /tmp/xray.zip
    
    systemctl daemon-reload
    systemctl enable xray
    
    print_success "Xray установлен"
}

# Создание пользователя для приложения
create_app_user() {
    if id "xrayapi" &>/dev/null; then
        print_info "Пользователь xrayapi уже существует"
        return
    fi
    
    print_info "Создание пользователя приложения..."
    useradd -r -m -s /bin/bash xrayapi
    usermod -aG docker xrayapi || true
    
    print_success "Пользователь xrayapi создан"
}

# Установка приложения
install_app() {
    print_info "Установка Xray Manager API..."
    
    # Создаем директории
    mkdir -p /opt/xray-manager-api
    mkdir -p /var/lib/xray-manager-api/{data,config,logs}
    mkdir -p /etc/xray-manager-api
    
    # Копируем файлы приложения
    if [[ -d "app" ]]; then
        cp -r app /opt/xray-manager-api/
        cp requirements.txt /opt/xray-manager-api/
    else
        print_error "Файлы приложения не найдены. Убедитесь, что скрипт запущен из корня проекта."
        exit 1
    fi
    
    # Создаем виртуальное окружение
    cd /opt/xray-manager-api
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Устанавливаем права
    chown -R xrayapi:xrayapi /opt/xray-manager-api
    chown -R xrayapi:xrayapi /var/lib/xray-manager-api
    
    print_success "Приложение установлено"
}

# Создание конфигурации
create_config() {
    print_info "Создание конфигурации..."
    
    # Создаем базовую конфигурацию Xray
    cat > /etc/xray/config.json << EOF
{
  "log": {
    "loglevel": "warning",
    "access": "/var/log/xray/access.log",
    "error": "/var/log/xray/error.log"
  },
  "inbounds": [
    {
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "www.microsoft.com:443",
          "xver": 0,
          "serverNames": ["www.microsoft.com"],
          "privateKey": "",
          "shortIds": [""]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "settings": {}
    }
  ]
}
EOF
    
    # Создаем конфигурацию приложения
    cat > /etc/xray-manager-api/config.env << EOF
# Основные настройки
HOST=0.0.0.0
PORT=8000
DEBUG=false

# База данных
DATABASE_URL=sqlite:///var/lib/xray-manager-api/data/xray_manager.db

# Xray настройки
XRAY_CONFIG_PATH=/etc/xray/config.json
XRAY_SERVICE_NAME=xray

# Безопасность
API_KEYS_FILE=/var/lib/xray-manager-api/data/api_keys.json
SECRET_KEY=$(openssl rand -hex 32)

# VLESS настройки по умолчанию
DEFAULT_PORT=443
DEFAULT_SECURITY=reality
DEFAULT_FLOW=xtls-rprx-vision
DEFAULT_FP=chrome
DEFAULT_SNI=www.microsoft.com
EOF
    
    chown xrayapi:xrayapi /etc/xray-manager-api/config.env
    chmod 600 /etc/xray-manager-api/config.env
    
    print_success "Конфигурация создана"
}

# Создание systemd сервиса
create_systemd_service() {
    print_info "Создание systemd сервиса..."
    
    cat > /etc/systemd/system/xray-manager-api.service << EOF
[Unit]
Description=Xray Manager API Service
After=network.target xray.service
Wants=xray.service

[Service]
Type=simple
User=xrayapi
Group=xrayapi
WorkingDirectory=/opt/xray-manager-api
Environment=PATH=/opt/xray-manager-api/venv/bin
EnvironmentFile=/etc/xray-manager-api/config.env
ExecStart=/opt/xray-manager-api/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=xray-manager-api

# Безопасность
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/lib/xray-manager-api /etc/xray

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable xray-manager-api
    
    print_success "Systemd сервис создан"
}

# Генерация ключей Reality
generate_reality_keys() {
    print_info "Генерация ключей Reality..."
    
    # Генерируем ключи с помощью Xray
    KEYS_OUTPUT=$(xray x25519)
    PRIVATE_KEY=$(echo "$KEYS_OUTPUT" | grep "Private key:" | cut -d' ' -f3)
    PUBLIC_KEY=$(echo "$KEYS_OUTPUT" | grep "Public key:" | cut -d' ' -f3)
    SHORT_ID=$(openssl rand -hex 8)
    
    # Обновляем конфигурацию
    sed -i "s/CHANGE_THIS_PRIVATE_KEY/$PRIVATE_KEY/g" /etc/xray/config.json
    sed -i "s/CHANGE_THIS_SHORT_ID/$SHORT_ID/g" /etc/xray/config.json
    
    print_success "Ключи Reality сгенерированы"
    print_info "Public Key: $PUBLIC_KEY"
    print_info "Short ID: $SHORT_ID"
}

# Запуск сервисов
start_services() {
    print_info "Запуск сервисов..."
    
    # Запускаем Xray
    systemctl start xray
    sleep 2
    
    if systemctl is-active --quiet xray; then
        print_success "Xray запущен"
    else
        print_error "Не удалось запустить Xray"
        systemctl status xray
        exit 1
    fi
    
    # Запускаем API
    systemctl start xray-manager-api
    sleep 3
    
    if systemctl is-active --quiet xray-manager-api; then
        print_success "Xray Manager API запущен"
    else
        print_error "Не удалось запустить Xray Manager API"
        systemctl status xray-manager-api
        exit 1
    fi
}

# Генерация API ключа
generate_api_key() {
    print_info "Генерация API ключа..."
    
    # Ждем запуска API
    sleep 5
    
    # Генерируем ключ через Python скрипт
    cd /opt/xray-manager-api
    source venv/bin/activate
    
    API_KEY=$(python3 -c "
import sys
sys.path.append('/opt/xray-manager-api')
from app.auth import generate_initial_key
key = generate_initial_key()
if key:
    print(key)
")
    
    if [[ -n "$API_KEY" ]]; then
        print_success "API ключ сгенерирован: $API_KEY"
        echo "$API_KEY" > /var/lib/xray-manager-api/initial_api_key.txt
        chown xrayapi:xrayapi /var/lib/xray-manager-api/initial_api_key.txt
        chmod 600 /var/lib/xray-manager-api/initial_api_key.txt
    else
        print_warning "Не удалось сгенерировать API ключ автоматически"
    fi
}

# Настройка файрвола
setup_firewall() {
    print_info "Настройка файрвола..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 8000/tcp comment "Xray Manager API"
        ufw allow 443/tcp comment "Xray VLESS"
        print_success "UFW правила добавлены"
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-port=8000/tcp
        firewall-cmd --permanent --add-port=443/tcp
        firewall-cmd --reload
        print_success "Firewalld правила добавлены"
    else
        print_warning "Файрвол не обнаружен. Убедитесь, что порты 8000 и 443 открыты"
    fi
}

# Финальная информация
show_final_info() {
    SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "YOUR_SERVER_IP")
    
    echo
    print_success "Установка завершена!"
    echo
    print_info "=== Информация о сервисе ==="
    print_info "API URL: http://$SERVER_IP:8000"
    print_info "Документация: http://$SERVER_IP:8000/docs"
    print_info "Статус: http://$SERVER_IP:8000/status"
    echo
    
    if [[ -f "/var/lib/xray-manager-api/initial_api_key.txt" ]]; then
        API_KEY=$(cat /var/lib/xray-manager-api/initial_api_key.txt)
        print_info "API ключ: $API_KEY"
        print_warning "Сохраните этот ключ в безопасном месте!"
    fi
    
    echo
    print_info "=== Управление сервисами ==="
    print_info "Статус API: systemctl status xray-manager-api"
    print_info "Статус Xray: systemctl status xray"
    print_info "Логи API: journalctl -u xray-manager-api -f"
    print_info "Логи Xray: journalctl -u xray -f"
    echo
    
    print_info "=== Конфигурационные файлы ==="
    print_info "API конфигурация: /etc/xray-manager-api/config.env"
    print_info "Xray конфигурация: /etc/xray/config.json"
    print_info "Данные приложения: /var/lib/xray-manager-api/"
    echo
}

# Основная функция
main() {
    echo "========================================"
    echo "  Xray Manager API - Установочный скрипт"
    echo "========================================"
    echo
    
    # Проверяем режим установки
    INSTALL_MODE=${1:-"full"}
    
    case $INSTALL_MODE in
        "docker")
            print_info "Режим установки: Docker"
            check_root
            detect_os
            install_dependencies
            install_docker
            print_success "Docker установка завершена. Используйте docker-compose up -d для запуска"
            ;;
        "full"|*)
            print_info "Режим установки: Полная установка"
            check_root
            detect_os
            install_dependencies
            install_xray
            create_app_user
            install_app
            create_config
            create_systemd_service
            generate_reality_keys
            start_services
            generate_api_key
            setup_firewall
            show_final_info
            ;;
    esac
}

# Запуск
main "$@"