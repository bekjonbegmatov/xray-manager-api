# Xray Manager API

Автономный REST API-сервис для управления Xray/VLESS пользователями на VPN-сервере.

## 🚀 Особенности

- **Автономность**: Работает локально на VPN-сервере без внешних зависимостей
- **REST API**: Полноценный API для управления пользователями VLESS
- **Docker поддержка**: Готовые контейнеры для быстрого развертывания
- **Безопасность**: API-ключи для аутентификации
- **Мониторинг**: Отслеживание трафика и статуса пользователей
- **Автоматическая установка**: Скрипт для полной настройки системы

## 📋 Требования

- **ОС**: Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+
- **Python**: 3.8+
- **Права**: root доступ для установки
- **Порты**: 443 (Xray), 8000 (API)

## 🛠 Быстрая установка

### Вариант 1: Автоматическая установка (рекомендуется)

```bash
# Клонируем репозиторий
git clone https://github.com/bekjonbegmatov/xray-manager-api.git
cd xray-manager-api

# Запускаем установочный скрипт
sudo bash install.sh
```

### Вариант 2: Docker установка

```bash
# Клонируем репозиторий
git clone https://github.com/bekjonbegmatov/xray-manager-api.git
cd xray-manager-api

# Устанавливаем Docker (если не установлен)
sudo bash install.sh docker

# Запускаем через Docker Compose
docker-compose up -d
```

## 📖 API Документация

После установки API будет доступен по адресу:
- **API**: `http://YOUR_SERVER_IP:8000`
- **Документация**: `http://YOUR_SERVER_IP:8000/docs`
- **Статус**: `http://YOUR_SERVER_IP:8000/status`

### Аутентификация

Все запросы требуют заголовок авторизации:

```bash
Authorization: Bearer YOUR_API_KEY
```

API-ключ генерируется автоматически при установке и сохраняется в файле `/var/lib/xray-manager-api/initial_api_key.txt`.

### Основные эндпоинты

#### 1. Создание пользователя

```bash
POST /users
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "email": "user@example.com",
  "name": "Test User",
  "traffic_limit": 10737418240
}
```

**Ответ:**
```json
{
  "uuid": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "Test User",
  "vless_link": "vless://123e4567-e89b-12d3-a456-426614174000@1.2.3.4:443?security=reality&encryption=none&flow=xtls-rprx-vision&type=tcp&fp=chrome&sni=www.microsoft.com&pbk=PUBLIC_KEY&sid=SHORT_ID#DeltaVPN",
  "status": "active",
  "traffic_limit": 10737418240,
  "created_at": "2024-01-20T10:30:00Z"
}
```

#### 2. Получение информации о пользователе

```bash
GET /users/{uuid}
Authorization: Bearer YOUR_API_KEY
```

#### 3. Список всех пользователей

```bash
GET /users
Authorization: Bearer YOUR_API_KEY
```

#### 4. Приостановка пользователя

```bash
POST /users/{uuid}/suspend
Authorization: Bearer YOUR_API_KEY
```

#### 5. Возобновление пользователя

```bash
POST /users/{uuid}/resume
Authorization: Bearer YOUR_API_KEY
```

#### 6. Удаление пользователя

```bash
DELETE /users/{uuid}
Authorization: Bearer YOUR_API_KEY
```

#### 7. Статистика трафика

```bash
GET /traffic/{uuid}
Authorization: Bearer YOUR_API_KEY
```

**Ответ:**
```json
{
  "uuid": "123e4567-e89b-12d3-a456-426614174000",
  "upload": 1073741824,
  "download": 2147483648,
  "total": 3221225472,
  "last_updated": "2024-01-20T10:30:00Z"
}
```

#### 8. Статус системы

```bash
GET /status
Authorization: Bearer YOUR_API_KEY
```

## 🔧 Конфигурация

### Переменные окружения

Основные настройки находятся в файле `/etc/xray-manager-api/config.env`:

```bash
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
SECRET_KEY=your_secret_key_here

# VLESS настройки по умолчанию
DEFAULT_PORT=443
DEFAULT_SECURITY=reality
DEFAULT_FLOW=xtls-rprx-vision
DEFAULT_FP=chrome
DEFAULT_SNI=www.microsoft.com
```

### Конфигурация Xray

Базовая конфигурация Xray создается автоматически в `/etc/xray/config.json`. Вы можете изменить настройки Reality, порты и другие параметры по необходимости.

## 🔐 Безопасность

### API-ключи

- Генерируются автоматически при установке
- Хранятся в зашифрованном виде
- Поддерживают ротацию и отзыв
- Логируются все операции

### Системная безопасность

- Приложение работает от непривилегированного пользователя `xrayapi`
- Конфигурационные файлы защищены правами доступа
- Логи ротируются автоматически
- Поддержка файрвола (UFW/Firewalld)

## 📊 Мониторинг

### Логи

```bash
# Логи API сервиса
journalctl -u xray-manager-api -f

# Логи Xray
journalctl -u xray -f

# Логи доступа Xray
tail -f /var/log/xray/access.log

# Логи ошибок Xray
tail -f /var/log/xray/error.log
```

### Статус сервисов

```bash
# Статус API
systemctl status xray-manager-api

# Статус Xray
systemctl status xray

# Перезапуск сервисов
systemctl restart xray-manager-api
systemctl restart xray
```

## 🐳 Docker

### Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Обновление
docker-compose pull
docker-compose up -d
```

### Переменные окружения для Docker

Создайте файл `.env` в корне проекта:

```bash
# Основные настройки
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Xray настройки
XRAY_PORT=443
XRAY_SNI=www.microsoft.com

# Безопасность
SECRET_KEY=your_secret_key_here
INITIAL_API_KEY=your_initial_api_key_here

# Мониторинг (опционально)
ENABLE_PROMETHEUS=true
ENABLE_GRAFANA=true
```

## 🔄 Обновление

### Автоматическое обновление

```bash
cd /path/to/xray-manager-api
git pull origin main
sudo systemctl restart xray-manager-api
```

### Docker обновление

```bash
cd /path/to/xray-manager-api
docker-compose pull
docker-compose up -d
```

## 🛠 Разработка

### Локальная разработка

```bash
# Клонируем репозиторий
git clone https://github.com/bekjonbegmatov/xray-manager-api.git
cd xray-manager-api

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Запускаем в режиме разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Тестирование

```bash
# Установка зависимостей для тестирования
pip install -r requirements-dev.txt

# Запуск тестов
pytest

# Проверка покрытия
pytest --cov=app tests/
```

## 📁 Структура проекта

```
xray-manager-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Основное FastAPI приложение
│   ├── auth.py              # Система аутентификации
│   ├── database.py          # Работа с базой данных
│   ├── models.py            # Модели данных
│   ├── xray_manager.py      # Управление Xray
│   └── utils.py             # Вспомогательные функции
├── tests/                   # Тесты
├── docker-compose.yml       # Docker Compose конфигурация
├── Dockerfile              # Docker образ
├── requirements.txt        # Python зависимости
├── install.sh              # Установочный скрипт
├── .dockerignore           # Docker ignore файл
└── README.md               # Документация
```

## 🤝 Поддержка

### Часто задаваемые вопросы

**Q: Как изменить порт API?**
A: Измените переменную `PORT` в файле `/etc/xray-manager-api/config.env` и перезапустите сервис.

**Q: Как добавить новый API-ключ?**
A: Используйте эндпоинт `/auth/keys` или добавьте ключ через административный интерфейс.

**Q: Как настроить HTTPS?**
A: Используйте Nginx как reverse proxy или настройте SSL сертификаты в Docker Compose.

### Получение помощи

- **Issues**: [GitHub Issues](https://github.com/bekjonbegmatov/xray-manager-api/issues)
- **Документация**: [Wiki](https://github.com/bekjonbegmatov/xray-manager-api/wiki)
- **Telegram**: @your_support_channel

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE) для подробностей.

## 🙏 Благодарности

- [Xray-core](https://github.com/XTLS/Xray-core) - Основа для VPN функциональности
- [FastAPI](https://fastapi.tiangolo.com/) - Веб-фреймворк
- [SQLAlchemy](https://sqlalchemy.org/) - ORM для работы с базой данных

---

**Важно**: Этот проект предназначен только для образовательных целей. Убедитесь, что использование VPN технологий соответствует законодательству вашей страны.