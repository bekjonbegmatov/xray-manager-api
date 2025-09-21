# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    systemctl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для приложения
RUN useradd -m -u 1000 xrayapi && \
    mkdir -p /app /data /config && \
    chown -R xrayapi:xrayapi /app /data /config

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app/ ./app/

# Создаем директории для данных
RUN mkdir -p /data/db /data/logs /config/xray

# Устанавливаем Xray
RUN XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | jq -r .tag_name) && \
    wget -O /tmp/xray.zip "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-64.zip" && \
    unzip /tmp/xray.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/xray && \
    rm /tmp/xray.zip

# Создаем конфигурационный файл для Xray
RUN echo '{}' > /config/xray/config.json

# Создаем скрипт запуска
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

# Инициализация базы данных и конфигурации
python -c "
import asyncio
import sys
sys.path.append('/app')
from app.database import database
from app.xray_manager import xray_manager
from app.auth import generate_initial_key

async def init():
    await database.init_db()
    
    # Создаем базовую конфигурацию Xray если не существует
    config = await xray_manager.get_config()
    if not config:
        await xray_manager.create_default_config()
    
    # Генерируем API ключ если не существует
    api_key = generate_initial_key()
    if api_key:
        print(f'Generated API Key: {api_key}')
        print('Save this key securely!')

asyncio.run(init())
"

# Запускаем Xray в фоне
xray -config /config/xray/config.json &

# Запускаем FastAPI приложение
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF

RUN chmod +x /app/start.sh

# Переключаемся на пользователя приложения
USER xrayapi

# Открываем порты
EXPOSE 8000 443

# Определяем volumes
VOLUME ["/data", "/config"]

# Переменные окружения
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///data/db/xray_manager.db
ENV XRAY_CONFIG_PATH=/config/xray/config.json
ENV API_KEYS_FILE=/data/api_keys.json

# Команда запуска
CMD ["/app/start.sh"]

# Метаданные
LABEL maintainer="Xray Manager API"
LABEL description="REST API для управления Xray/VLESS пользователями"
LABEL version="1.0.0"