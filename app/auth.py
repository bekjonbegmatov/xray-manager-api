import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Менеджер для управления API ключами"""
    
    def __init__(self, keys_file: str = "api_keys.json"):
        self.keys_file = Path(keys_file)
        self.keys_data = self._load_keys()
    
    def _load_keys(self) -> Dict:
        """Загрузить ключи из файла"""
        if not self.keys_file.exists():
            return {"keys": {}, "created_at": datetime.now().isoformat()}
        
        try:
            with open(self.keys_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки ключей: {e}")
            return {"keys": {}, "created_at": datetime.now().isoformat()}
    
    def _save_keys(self) -> bool:
        """Сохранить ключи в файл"""
        try:
            with open(self.keys_file, 'w', encoding='utf-8') as f:
                json.dump(self.keys_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения ключей: {e}")
            return False
    
    def _hash_key(self, key: str) -> str:
        """Хешировать ключ для безопасного хранения"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def generate_key(self, name: str = "default", expires_days: Optional[int] = None) -> str:
        """Сгенерировать новый API ключ"""
        # Генерируем случайный ключ
        key = secrets.token_urlsafe(32)
        key_hash = self._hash_key(key)
        
        # Подготавливаем данные ключа
        key_data = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "usage_count": 0,
            "is_active": True
        }
        
        # Добавляем срок действия если указан
        if expires_days:
            expiry_date = datetime.now() + timedelta(days=expires_days)
            key_data["expires_at"] = expiry_date.isoformat()
        
        # Сохраняем ключ
        self.keys_data["keys"][key_hash] = key_data
        self._save_keys()
        
        logger.info(f"Создан новый API ключ: {name}")
        return key
    
    def verify_key(self, key: str) -> bool:
        """Проверить валидность API ключа"""
        if not key:
            return False
        
        key_hash = self._hash_key(key)
        key_data = self.keys_data["keys"].get(key_hash)
        
        if not key_data:
            return False
        
        # Проверяем активность ключа
        if not key_data.get("is_active", True):
            return False
        
        # Проверяем срок действия
        expires_at = key_data.get("expires_at")
        if expires_at:
            expiry_date = datetime.fromisoformat(expires_at)
            if datetime.now() > expiry_date:
                logger.warning(f"API ключ истек: {key_data.get('name', 'unknown')}")
                return False
        
        # Обновляем статистику использования
        key_data["last_used"] = datetime.now().isoformat()
        key_data["usage_count"] = key_data.get("usage_count", 0) + 1
        self._save_keys()
        
        return True
    
    def revoke_key(self, key: str) -> bool:
        """Отозвать API ключ"""
        key_hash = self._hash_key(key)
        key_data = self.keys_data["keys"].get(key_hash)
        
        if not key_data:
            return False
        
        key_data["is_active"] = False
        key_data["revoked_at"] = datetime.now().isoformat()
        self._save_keys()
        
        logger.info(f"API ключ отозван: {key_data.get('name', 'unknown')}")
        return True
    
    def list_keys(self) -> List[Dict]:
        """Получить список всех ключей (без самих ключей)"""
        result = []
        for key_hash, key_data in self.keys_data["keys"].items():
            result.append({
                "hash": key_hash[:16] + "...",  # Показываем только часть хеша
                "name": key_data.get("name", "unknown"),
                "created_at": key_data.get("created_at"),
                "last_used": key_data.get("last_used"),
                "usage_count": key_data.get("usage_count", 0),
                "is_active": key_data.get("is_active", True),
                "expires_at": key_data.get("expires_at")
            })
        return result
    
    def cleanup_expired_keys(self) -> int:
        """Удалить истекшие ключи"""
        current_time = datetime.now()
        expired_keys = []
        
        for key_hash, key_data in self.keys_data["keys"].items():
            expires_at = key_data.get("expires_at")
            if expires_at:
                expiry_date = datetime.fromisoformat(expires_at)
                if current_time > expiry_date:
                    expired_keys.append(key_hash)
        
        # Удаляем истекшие ключи
        for key_hash in expired_keys:
            del self.keys_data["keys"][key_hash]
        
        if expired_keys:
            self._save_keys()
            logger.info(f"Удалено {len(expired_keys)} истекших ключей")
        
        return len(expired_keys)
    
    def get_key_info(self, key: str) -> Optional[Dict]:
        """Получить информацию о ключе"""
        key_hash = self._hash_key(key)
        key_data = self.keys_data["keys"].get(key_hash)
        
        if not key_data:
            return None
        
        return {
            "name": key_data.get("name", "unknown"),
            "created_at": key_data.get("created_at"),
            "last_used": key_data.get("last_used"),
            "usage_count": key_data.get("usage_count", 0),
            "is_active": key_data.get("is_active", True),
            "expires_at": key_data.get("expires_at")
        }

# Глобальный экземпляр менеджера ключей
api_key_manager = APIKeyManager()

def generate_initial_key() -> str:
    """Генерировать начальный API ключ при первом запуске"""
    # Проверяем, есть ли уже активные ключи
    active_keys = [
        key_data for key_data in api_key_manager.keys_data["keys"].values()
        if key_data.get("is_active", True)
    ]
    
    if not active_keys:
        # Генерируем первый ключ
        key = api_key_manager.generate_key("initial_key")
        logger.info("Сгенерирован начальный API ключ")
        return key
    
    return None

def verify_api_key(key: str) -> bool:
    """Проверить API ключ"""
    return api_key_manager.verify_key(key)

def create_api_key(name: str = "user_key", expires_days: Optional[int] = None) -> str:
    """Создать новый API ключ"""
    return api_key_manager.generate_key(name, expires_days)

def revoke_api_key(key: str) -> bool:
    """Отозвать API ключ"""
    return api_key_manager.revoke_key(key)

def list_api_keys() -> List[Dict]:
    """Получить список API ключей"""
    return api_key_manager.list_keys()

def cleanup_expired_keys() -> int:
    """Очистить истекшие ключи"""
    return api_key_manager.cleanup_expired_keys()

# Middleware для логирования запросов с API ключами
class APIKeyLoggingMiddleware:
    """Middleware для логирования использования API ключей"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Извлекаем информацию о запросе
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]  # Убираем "Bearer "
                key_info = api_key_manager.get_key_info(api_key)
                
                if key_info:
                    logger.info(
                        f"API запрос от ключа '{key_info['name']}' "
                        f"к {scope['method']} {scope['path']}"
                    )
        
        await self.app(scope, receive, send)