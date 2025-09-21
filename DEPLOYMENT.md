# Руководство по развертыванию Xray Manager API

Это подробное руководство по развертыванию Xray Manager API в различных окружениях.

## 📋 Содержание

- [Системные требования](#системные-требования)
- [Автоматическая установка](#автоматическая-установка)
- [Ручная установка](#ручная-установка)
- [Docker развертывание](#docker-развертывание)
- [Настройка HTTPS](#настройка-https)
- [Настройка файрвола](#настройка-файрвола)
- [Мониторинг и логи](#мониторинг-и-логи)
- [Обновление](#обновление)
- [Резервное копирование](#резервное-копирование)
- [Устранение неполадок](#устранение-неполадок)

## 🖥️ Системные требования

### Минимальные требования
- **ОС**: Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+
- **RAM**: 512 MB (рекомендуется 1 GB+)
- **CPU**: 1 vCPU (рекомендуется 2+ vCPU)
- **Диск**: 2 GB свободного места
- **Сеть**: Публичный IP адрес

### Рекомендуемые требования
- **RAM**: 2 GB+
- **CPU**: 2+ vCPU
- **Диск**: 10 GB+ SSD
- **Сеть**: Минимум 100 Mbps

### Поддерживаемые ОС
- ✅ Ubuntu 20.04, 22.04, 24.04
- ✅ Debian 11, 12
- ✅ CentOS 8, 9
- ✅ RHEL 8, 9
- ✅ Rocky Linux 8, 9
- ✅ AlmaLinux 8, 9

## 🚀 Автоматическая установка

### Быстрая установка (рекомендуется)

```bash
# Скачивание и запуск установочного скрипта
curl -fsSL https://raw.githubusercontent.com/bekjonbegmatov/xray-manager-api/main/install.sh | sudo bash
```

### Установка с параметрами

```bash
# Скачивание скрипта
wget https://raw.githubusercontent.com/bekjonbegmatov/xray-manager-api/main/install.sh

# Просмотр доступных опций
chmod +x install.sh
sudo ./install.sh --help

# Установка с кастомными параметрами
sudo ./install.sh \
    --port 8080 \
    --domain your-domain.com \
    --ssl-cert /path/to/cert.pem \
    --ssl-key /path/to/key.pem \
    --reality-domain microsoft.com \
    --install-nginx
```

### Параметры установки

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `--port` | Порт API сервера | 8000 |
| `--domain` | Домен для HTTPS | localhost |
| `--ssl-cert` | Путь к SSL сертификату | - |
| `--ssl-key` | Путь к SSL ключу | - |
| `--reality-domain` | Домен для Reality маскировки | microsoft.com |
| `--install-nginx` | Установить Nginx как прокси | false |
| `--skip-xray` | Пропустить установку Xray | false |
| `--skip-firewall` | Пропустить настройку файрвола | false |

## 🔧 Ручная установка

### Шаг 1: Подготовка системы

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# или
sudo yum update -y  # CentOS/RHEL

# Установка базовых зависимостей
sudo apt install -y curl wget git jq unzip python3 python3-pip  # Ubuntu/Debian
# или
sudo yum install -y curl wget git jq unzip python3 python3-pip  # CentOS/RHEL
```

### Шаг 2: Установка Xray

```bash
# Скачивание и установка Xray
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install

# Проверка установки
xray version
```

### Шаг 3: Создание пользователя приложения

```bash
# Создание системного пользователя
sudo useradd -r -s /bin/false -d /var/lib/xray-manager-api xray-manager

# Создание директорий
sudo mkdir -p /var/lib/xray-manager-api/{data,logs,config}
sudo mkdir -p /etc/xray-manager-api

# Установка прав доступа
sudo chown -R xray-manager:xray-manager /var/lib/xray-manager-api
sudo chmod 755 /var/lib/xray-manager-api
```

### Шаг 4: Установка приложения

```bash
# Клонирование репозитория
git clone https://github.com/USERNAME/xray-manager-api.git
cd xray-manager-api

# Установка Python зависимостей
sudo pip3 install -r requirements.txt

# Копирование файлов
sudo cp -r app /opt/xray-manager-api/
sudo cp config/config.yaml /etc/xray-manager-api/
sudo chown -R xray-manager:xray-manager /opt/xray-manager-api
```

### Шаг 5: Настройка конфигурации

```bash
# Редактирование конфигурации
sudo nano /etc/xray-manager-api/config.yaml
```

```yaml
# Базовая конфигурация
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4

xray:
  config_path: "/usr/local/etc/xray/config.json"
  executable: "/usr/local/bin/xray"
  service_name: "xray"

reality:
  domain: "microsoft.com"
  server_name: "www.microsoft.com"

database:
  path: "/var/lib/xray-manager-api/data/users.db"

logging:
  level: "INFO"
  file: "/var/lib/xray-manager-api/logs/app.log"
  max_size: "10MB"
  backup_count: 5

security:
  api_key_length: 32
  jwt_secret_key: "your-secret-key-here"
  cors_origins: ["*"]
```

### Шаг 6: Создание systemd сервиса

```bash
# Создание файла сервиса
sudo tee /etc/systemd/system/xray-manager-api.service > /dev/null <<EOF
[Unit]
Description=Xray Manager API Service
After=network.target xray.service
Wants=xray.service

[Service]
Type=exec
User=xray-manager
Group=xray-manager
WorkingDirectory=/opt/xray-manager-api
Environment=PYTHONPATH=/opt/xray-manager-api
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd и запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable xray-manager-api
sudo systemctl start xray-manager-api
```

## 🐳 Docker развертывание

### Docker Compose (рекомендуется)

```yaml
# docker-compose.yml
version: '3.8'

services:
  xray-manager-api:
    build: .
    container_name: xray-manager-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
      - /etc/xray:/etc/xray:ro
    environment:
      - CONFIG_PATH=/app/config/config.yaml
    depends_on:
      - xray
    networks:
      - xray-network

  xray:
    image: teddysun/xray:latest
    container_name: xray
    restart: unless-stopped
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./xray-config:/etc/xray
      - ./xray-logs:/var/log/xray
    networks:
      - xray-network

  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - xray-manager-api
    networks:
      - xray-network

networks:
  xray-network:
    driver: bridge
```

### Запуск через Docker Compose

```bash
# Клонирование репозитория
git clone https://github.com/USERNAME/xray-manager-api.git
cd xray-manager-api

# Создание необходимых директорий
mkdir -p {data,logs,config,xray-config,xray-logs,ssl}

# Копирование конфигураций
cp config/config.yaml config/
cp config/xray-template.json xray-config/config.json

# Запуск сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps
docker-compose logs -f xray-manager-api
```

### Standalone Docker

```bash
# Сборка образа
docker build -t xray-manager-api .

# Запуск контейнера
docker run -d \
  --name xray-manager-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config \
  xray-manager-api
```

## 🔒 Настройка HTTPS

### Использование Let's Encrypt

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx  # Ubuntu/Debian
# или
sudo yum install certbot python3-certbot-nginx  # CentOS/RHEL

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавить строку:
0 12 * * * /usr/bin/certbot renew --quiet
```

### Ручная настройка SSL

```bash
# Создание директории для сертификатов
sudo mkdir -p /etc/ssl/xray-manager

# Копирование сертификатов
sudo cp your-cert.pem /etc/ssl/xray-manager/
sudo cp your-key.pem /etc/ssl/xray-manager/

# Установка прав доступа
sudo chmod 600 /etc/ssl/xray-manager/*
sudo chown root:root /etc/ssl/xray-manager/*
```

### Конфигурация Nginx для HTTPS

```nginx
# /etc/nginx/sites-available/xray-manager-api
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/xray-manager/cert.pem;
    ssl_certificate_key /etc/ssl/xray-manager/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🛡️ Настройка файрвола

### UFW (Ubuntu/Debian)

```bash
# Включение UFW
sudo ufw enable

# Базовые правила
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешение SSH
sudo ufw allow ssh

# Разрешение портов для Xray Manager API
sudo ufw allow 8000/tcp  # API порт
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 80/tcp    # HTTP (для редиректа)

# Проверка статуса
sudo ufw status verbose
```

### Firewalld (CentOS/RHEL)

```bash
# Включение firewalld
sudo systemctl enable --now firewalld

# Добавление портов
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=80/tcp

# Применение правил
sudo firewall-cmd --reload

# Проверка статуса
sudo firewall-cmd --list-all
```

### Iptables

```bash
# Базовые правила
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Разрешение loopback
sudo iptables -A INPUT -i lo -j ACCEPT

# Разрешение установленных соединений
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Разрешение SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Разрешение портов приложения
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# Сохранение правил
sudo iptables-save > /etc/iptables/rules.v4
```

## 📊 Мониторинг и логи

### Настройка логирования

```bash
# Конфигурация rsyslog для приложения
sudo tee /etc/rsyslog.d/50-xray-manager-api.conf > /dev/null <<EOF
# Xray Manager API logs
:programname, isequal, "xray-manager-api" /var/log/xray-manager-api.log
& stop
EOF

# Перезапуск rsyslog
sudo systemctl restart rsyslog
```

### Ротация логов

```bash
# Создание конфигурации logrotate
sudo tee /etc/logrotate.d/xray-manager-api > /dev/null <<EOF
/var/log/xray-manager-api.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 syslog adm
    postrotate
        systemctl reload xray-manager-api
    endscript
}
EOF
```

### Мониторинг с помощью systemd

```bash
# Проверка статуса сервиса
sudo systemctl status xray-manager-api

# Просмотр логов
sudo journalctl -u xray-manager-api -f

# Просмотр логов за последний час
sudo journalctl -u xray-manager-api --since "1 hour ago"
```

### Настройка мониторинга с Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'xray-manager-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

## 🔄 Обновление

### Автоматическое обновление

```bash
# Создание скрипта обновления
sudo tee /usr/local/bin/update-xray-manager-api.sh > /dev/null <<'EOF'
#!/bin/bash

set -e

echo "Updating Xray Manager API..."

# Остановка сервиса
sudo systemctl stop xray-manager-api

# Создание резервной копии
sudo cp -r /opt/xray-manager-api /opt/xray-manager-api.backup.$(date +%Y%m%d_%H%M%S)

# Обновление кода
cd /tmp
git clone https://github.com/USERNAME/xray-manager-api.git
sudo cp -r xray-manager-api/app/* /opt/xray-manager-api/
sudo chown -R xray-manager:xray-manager /opt/xray-manager-api

# Обновление зависимостей
sudo pip3 install -r xray-manager-api/requirements.txt

# Запуск сервиса
sudo systemctl start xray-manager-api

# Проверка статуса
sleep 5
sudo systemctl status xray-manager-api

echo "Update completed successfully!"
EOF

sudo chmod +x /usr/local/bin/update-xray-manager-api.sh
```

### Ручное обновление

```bash
# Остановка сервиса
sudo systemctl stop xray-manager-api

# Резервное копирование
sudo cp -r /opt/xray-manager-api /opt/xray-manager-api.backup

# Скачивание новой версии
cd /tmp
git clone https://github.com/USERNAME/xray-manager-api.git
cd xray-manager-api

# Обновление файлов
sudo cp -r app/* /opt/xray-manager-api/
sudo pip3 install -r requirements.txt

# Запуск сервиса
sudo systemctl start xray-manager-api
```

## 💾 Резервное копирование

### Скрипт резервного копирования

```bash
# Создание скрипта резервного копирования
sudo tee /usr/local/bin/backup-xray-manager-api.sh > /dev/null <<'EOF'
#!/bin/bash

BACKUP_DIR="/var/backups/xray-manager-api"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="xray-manager-api-backup-$DATE.tar.gz"

# Создание директории для резервных копий
mkdir -p $BACKUP_DIR

# Создание резервной копии
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    /var/lib/xray-manager-api/data \
    /etc/xray-manager-api \
    /usr/local/etc/xray/config.json

# Удаление старых резервных копий (старше 30 дней)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup created: $BACKUP_DIR/$BACKUP_FILE"
EOF

sudo chmod +x /usr/local/bin/backup-xray-manager-api.sh

# Добавление в crontab для ежедневного резервного копирования
echo "0 2 * * * /usr/local/bin/backup-xray-manager-api.sh" | sudo crontab -
```

### Восстановление из резервной копии

```bash
# Остановка сервисов
sudo systemctl stop xray-manager-api xray

# Восстановление данных
sudo tar -xzf /var/backups/xray-manager-api/xray-manager-api-backup-YYYYMMDD_HHMMSS.tar.gz -C /

# Установка прав доступа
sudo chown -R xray-manager:xray-manager /var/lib/xray-manager-api

# Запуск сервисов
sudo systemctl start xray xray-manager-api
```

## 🔧 Устранение неполадок

### Проверка статуса сервисов

```bash
# Проверка статуса всех сервисов
sudo systemctl status xray-manager-api xray nginx

# Проверка портов
sudo netstat -tlnp | grep -E ':(8000|443|80)'
sudo ss -tlnp | grep -E ':(8000|443|80)'
```

### Проверка логов

```bash
# Логи приложения
sudo journalctl -u xray-manager-api -n 100
sudo tail -f /var/lib/xray-manager-api/logs/app.log

# Логи Xray
sudo journalctl -u xray -n 100
sudo tail -f /var/log/xray/access.log
sudo tail -f /var/log/xray/error.log

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Типичные проблемы и решения

#### Проблема: API не отвечает

```bash
# Проверка процесса
ps aux | grep xray-manager-api

# Проверка порта
sudo lsof -i :8000

# Перезапуск сервиса
sudo systemctl restart xray-manager-api
```

#### Проблема: Xray не запускается

```bash
# Проверка конфигурации Xray
xray -test -config /usr/local/etc/xray/config.json

# Проверка прав доступа
ls -la /usr/local/etc/xray/config.json

# Исправление прав
sudo chown xray:xray /usr/local/etc/xray/config.json
sudo chmod 644 /usr/local/etc/xray/config.json
```

#### Проблема: Ошибки базы данных

```bash
# Проверка файла базы данных
ls -la /var/lib/xray-manager-api/data/users.db

# Проверка целостности SQLite
sqlite3 /var/lib/xray-manager-api/data/users.db "PRAGMA integrity_check;"

# Восстановление из резервной копии при необходимости
```

### Диагностический скрипт

```bash
# Создание диагностического скрипта
sudo tee /usr/local/bin/diagnose-xray-manager-api.sh > /dev/null <<'EOF'
#!/bin/bash

echo "=== Xray Manager API Diagnostics ==="
echo

echo "1. Service Status:"
systemctl is-active xray-manager-api xray nginx
echo

echo "2. Port Status:"
netstat -tlnp | grep -E ':(8000|443|80)'
echo

echo "3. Process Status:"
ps aux | grep -E '(xray|nginx)' | grep -v grep
echo

echo "4. Disk Usage:"
df -h /var/lib/xray-manager-api
echo

echo "5. Memory Usage:"
free -h
echo

echo "6. Recent Errors (last 10 lines):"
journalctl -u xray-manager-api -n 10 --no-pager
echo

echo "7. Configuration Test:"
python3 -c "
import sys
sys.path.append('/opt/xray-manager-api')
try:
    from app.config import settings
    print('✅ Configuration loaded successfully')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"
EOF

sudo chmod +x /usr/local/bin/diagnose-xray-manager-api.sh
```

### Получение поддержки

Если проблема не решается:

1. Запустите диагностический скрипт: `sudo /usr/local/bin/diagnose-xray-manager-api.sh`
2. Соберите логи: `sudo journalctl -u xray-manager-api --since "1 hour ago" > logs.txt`
3. Создайте issue в GitHub репозитории с подробным описанием проблемы
4. Приложите результаты диагностики и логи

---

Это руководство покрывает основные сценарии развертывания. Для специфических случаев обратитесь к документации или создайте issue в репозитории проекта.