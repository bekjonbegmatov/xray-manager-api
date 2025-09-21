# API Examples - Примеры использования

Этот документ содержит практические примеры использования Xray Manager API.

## 🔑 Получение API ключа

После установки API ключ можно найти в файле:

```bash
# На сервере после установки
sudo cat /var/lib/xray-manager-api/initial_api_key.txt
```

Или получить через API (если у вас уже есть ключ):

```bash
curl -X GET "http://YOUR_SERVER_IP:8000/auth/keys" \
  -H "Authorization: Bearer YOUR_EXISTING_API_KEY"
```

## 👤 Управление пользователями

### Создание пользователя

```bash
# Базовое создание пользователя
curl -X POST "http://YOUR_SERVER_IP:8000/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "email": "user@example.com",
    "name": "Test User"
  }'

# Создание с лимитом трафика (10 ГБ)
curl -X POST "http://YOUR_SERVER_IP:8000/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "email": "premium@example.com",
    "name": "Premium User",
    "traffic_limit": 10737418240
  }'
```

**Ответ:**
```json
{
  "uuid": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "Test User",
  "vless_link": "vless://123e4567-e89b-12d3-a456-426614174000@1.2.3.4:443?security=reality&encryption=none&flow=xtls-rprx-vision&type=tcp&fp=chrome&sni=www.microsoft.com&pbk=PUBLIC_KEY&sid=SHORT_ID#DeltaVPN",
  "status": "active",
  "traffic_limit": null,
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:30:00Z"
}
```

### Получение информации о пользователе

```bash
curl -X GET "http://YOUR_SERVER_IP:8000/users/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Список всех пользователей

```bash
# Все пользователи
curl -X GET "http://YOUR_SERVER_IP:8000/users" \
  -H "Authorization: Bearer YOUR_API_KEY"

# С пагинацией
curl -X GET "http://YOUR_SERVER_IP:8000/users?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Фильтр по статусу
curl -X GET "http://YOUR_SERVER_IP:8000/users?status=active" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Приостановка пользователя

```bash
curl -X POST "http://YOUR_SERVER_IP:8000/users/123e4567-e89b-12d3-a456-426614174000/suspend" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Возобновление пользователя

```bash
curl -X POST "http://YOUR_SERVER_IP:8000/users/123e4567-e89b-12d3-a456-426614174000/resume" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Удаление пользователя

```bash
curl -X DELETE "http://YOUR_SERVER_IP:8000/users/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 📊 Статистика трафика

### Получение трафика пользователя

```bash
curl -X GET "http://YOUR_SERVER_IP:8000/traffic/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_API_KEY"
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

### Сброс статистики трафика

```bash
curl -X POST "http://YOUR_SERVER_IP:8000/traffic/123e4567-e89b-12d3-a456-426614174000/reset" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 🔍 Мониторинг системы

### Статус системы

```bash
curl -X GET "http://YOUR_SERVER_IP:8000/status" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Ответ:**
```json
{
  "status": "healthy",
  "xray_status": "running",
  "api_version": "1.0.0",
  "uptime": 3600,
  "total_users": 5,
  "active_users": 4,
  "suspended_users": 1,
  "system_info": {
    "cpu_usage": 15.2,
    "memory_usage": 45.8,
    "disk_usage": 23.1
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### Логи системы

```bash
curl -X GET "http://YOUR_SERVER_IP:8000/logs?lines=100" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 🔐 Управление API ключами

### Создание нового API ключа

```bash
curl -X POST "http://YOUR_SERVER_IP:8000/auth/keys" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "name": "Bot API Key",
    "expires_in_days": 365
  }'
```

### Список API ключей

```bash
curl -X GET "http://YOUR_SERVER_IP:8000/auth/keys" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Отзыв API ключа

```bash
curl -X DELETE "http://YOUR_SERVER_IP:8000/auth/keys/key_id_here" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 🐍 Python примеры

### Базовый клиент

```python
import requests
import json

class XrayManagerClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_user(self, email, name, traffic_limit=None):
        data = {'email': email, 'name': name}
        if traffic_limit:
            data['traffic_limit'] = traffic_limit
        
        response = requests.post(
            f'{self.base_url}/users',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def get_user(self, uuid):
        response = requests.get(
            f'{self.base_url}/users/{uuid}',
            headers=self.headers
        )
        return response.json()
    
    def suspend_user(self, uuid):
        response = requests.post(
            f'{self.base_url}/users/{uuid}/suspend',
            headers=self.headers
        )
        return response.json()
    
    def get_traffic(self, uuid):
        response = requests.get(
            f'{self.base_url}/traffic/{uuid}',
            headers=self.headers
        )
        return response.json()

# Использование
client = XrayManagerClient('http://YOUR_SERVER_IP:8000', 'YOUR_API_KEY')

# Создание пользователя
user = client.create_user('test@example.com', 'Test User', 10737418240)
print(f"Created user: {user['uuid']}")
print(f"VLESS link: {user['vless_link']}")

# Получение статистики
traffic = client.get_traffic(user['uuid'])
print(f"Traffic: {traffic['total']} bytes")
```

### Асинхронный клиент

```python
import aiohttp
import asyncio

class AsyncXrayManagerClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def create_user(self, session, email, name, traffic_limit=None):
        data = {'email': email, 'name': name}
        if traffic_limit:
            data['traffic_limit'] = traffic_limit
        
        async with session.post(
            f'{self.base_url}/users',
            headers=self.headers,
            json=data
        ) as response:
            return await response.json()
    
    async def get_users(self, session):
        async with session.get(
            f'{self.base_url}/users',
            headers=self.headers
        ) as response:
            return await response.json()

async def main():
    client = AsyncXrayManagerClient('http://YOUR_SERVER_IP:8000', 'YOUR_API_KEY')
    
    async with aiohttp.ClientSession() as session:
        # Создание нескольких пользователей параллельно
        tasks = [
            client.create_user(session, f'user{i}@example.com', f'User {i}')
            for i in range(5)
        ]
        users = await asyncio.gather(*tasks)
        
        for user in users:
            print(f"Created: {user['email']} - {user['uuid']}")

# Запуск
asyncio.run(main())
```

## 🤖 Telegram Bot пример

```python
import telebot
import requests
from telebot import types

bot = telebot.TeleBot('YOUR_BOT_TOKEN')
API_BASE_URL = 'http://YOUR_SERVER_IP:8000'
API_KEY = 'YOUR_API_KEY'

def api_request(method, endpoint, data=None):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    url = f'{API_BASE_URL}{endpoint}'
    
    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data)
    elif method == 'DELETE':
        response = requests.delete(url, headers=headers)
    
    return response.json()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Создать пользователя', 'Мои пользователи')
    markup.add('Статус системы')
    
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в Xray Manager Bot!",
        reply_markup=markup
    )

@bot.message_handler(text=['Создать пользователя'])
def create_user_start(message):
    bot.send_message(message.chat.id, "Введите email для нового пользователя:")
    bot.register_next_step_handler(message, create_user_email)

def create_user_email(message):
    email = message.text
    bot.send_message(message.chat.id, "Введите имя пользователя:")
    bot.register_next_step_handler(message, lambda m: create_user_name(m, email))

def create_user_name(message, email):
    name = message.text
    
    try:
        user = api_request('POST', '/users', {
            'email': email,
            'name': name
        })
        
        response_text = f"""
✅ Пользователь создан!

📧 Email: {user['email']}
👤 Имя: {user['name']}
🆔 UUID: {user['uuid']}
📊 Статус: {user['status']}

🔗 VLESS ссылка:
`{user['vless_link']}`
        """
        
        bot.send_message(message.chat.id, response_text, parse_mode='Markdown')
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(text=['Статус системы'])
def system_status(message):
    try:
        status = api_request('GET', '/status')
        
        response_text = f"""
📊 Статус системы:

🟢 API: {status['status']}
🔧 Xray: {status['xray_status']}
📈 Версия: {status['api_version']}
⏱ Время работы: {status['uptime']} сек

👥 Пользователи:
• Всего: {status['total_users']}
• Активных: {status['active_users']}
• Приостановлено: {status['suspended_users']}

💻 Система:
• CPU: {status['system_info']['cpu_usage']}%
• RAM: {status['system_info']['memory_usage']}%
• Диск: {status['system_info']['disk_usage']}%
        """
        
        bot.send_message(message.chat.id, response_text)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

if __name__ == '__main__':
    bot.polling(none_stop=True)
```

## 📱 JavaScript/Node.js пример

```javascript
const axios = require('axios');

class XrayManagerClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async createUser(email, name, trafficLimit = null) {
        const data = { email, name };
        if (trafficLimit) data.traffic_limit = trafficLimit;

        const response = await axios.post(
            `${this.baseUrl}/users`,
            data,
            { headers: this.headers }
        );
        return response.data;
    }

    async getUsers() {
        const response = await axios.get(
            `${this.baseUrl}/users`,
            { headers: this.headers }
        );
        return response.data;
    }

    async getTraffic(uuid) {
        const response = await axios.get(
            `${this.baseUrl}/traffic/${uuid}`,
            { headers: this.headers }
        );
        return response.data;
    }
}

// Использование
async function main() {
    const client = new XrayManagerClient(
        'http://YOUR_SERVER_IP:8000',
        'YOUR_API_KEY'
    );

    try {
        // Создание пользователя
        const user = await client.createUser(
            'test@example.com',
            'Test User',
            10737418240 // 10 GB
        );
        console.log('User created:', user.uuid);
        console.log('VLESS link:', user.vless_link);

        // Получение списка пользователей
        const users = await client.getUsers();
        console.log('Total users:', users.length);

    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

main();
```

## 🔧 Bash скрипты

### Массовое создание пользователей

```bash
#!/bin/bash

API_URL="http://YOUR_SERVER_IP:8000"
API_KEY="YOUR_API_KEY"

# Создание пользователей из файла
# Формат файла: email,name,traffic_limit
while IFS=',' read -r email name traffic_limit; do
    echo "Creating user: $email"
    
    curl -s -X POST "$API_URL/users" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "{
            \"email\": \"$email\",
            \"name\": \"$name\",
            \"traffic_limit\": $traffic_limit
        }" | jq -r '.vless_link'
    
    sleep 1
done < users.csv
```

### Мониторинг трафика

```bash
#!/bin/bash

API_URL="http://YOUR_SERVER_IP:8000"
API_KEY="YOUR_API_KEY"

# Получение всех пользователей и их трафика
users=$(curl -s -H "Authorization: Bearer $API_KEY" "$API_URL/users" | jq -r '.[].uuid')

echo "UUID,Email,Upload,Download,Total"

for uuid in $users; do
    user_info=$(curl -s -H "Authorization: Bearer $API_KEY" "$API_URL/users/$uuid")
    traffic_info=$(curl -s -H "Authorization: Bearer $API_KEY" "$API_URL/traffic/$uuid")
    
    email=$(echo "$user_info" | jq -r '.email')
    upload=$(echo "$traffic_info" | jq -r '.upload')
    download=$(echo "$traffic_info" | jq -r '.download')
    total=$(echo "$traffic_info" | jq -r '.total')
    
    echo "$uuid,$email,$upload,$download,$total"
done
```

## 🚨 Обработка ошибок

### Типичные ошибки и их обработка

```python
import requests
from requests.exceptions import RequestException

def safe_api_call(method, url, **kwargs):
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            print("❌ Неверный API ключ")
        elif response.status_code == 404:
            print("❌ Пользователь не найден")
        elif response.status_code == 409:
            print("❌ Пользователь уже существует")
        elif response.status_code == 422:
            print("❌ Неверные данные запроса")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
        return None
    
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к серверу")
        return None
    
    except requests.exceptions.Timeout:
        print("❌ Превышено время ожидания")
        return None
    
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {str(e)}")
        return None

# Использование
result = safe_api_call(
    'POST',
    'http://YOUR_SERVER_IP:8000/users',
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    json={'email': 'test@example.com', 'name': 'Test'}
)

if result:
    print(f"✅ Пользователь создан: {result['uuid']}")
```

---

Эти примеры помогут вам быстро начать работу с Xray Manager API. Для получения полной документации посетите `/docs` эндпоинт вашего API сервера.