import os
import secrets
from pathlib import Path
from typing import Optional

class Settings:
    """Настройки приложения"""
    
    # API настройки
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Xray Manager API"
    VERSION: str = "1.0.0"
    
    # Безопасность
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    API_KEY_FILE: str = os.getenv("API_KEY_FILE", "/app/data/api_key.txt")
    
    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/xray_manager.db")
    
    # Xray настройки
    XRAY_CONFIG_PATH: str = os.getenv("XRAY_CONFIG_PATH", "/etc/xray/config.json")
    XRAY_SERVICE_NAME: str = os.getenv("XRAY_SERVICE_NAME", "xray")
    
    # Сервер настройки
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    
    # VLESS настройки по умолчанию
    DEFAULT_PORT: int = int(os.getenv("DEFAULT_PORT", "443"))
    DEFAULT_SECURITY: str = os.getenv("DEFAULT_SECURITY", "reality")
    DEFAULT_FLOW: str = os.getenv("DEFAULT_FLOW", "xtls-rprx-vision")
    DEFAULT_SNI: str = os.getenv("DEFAULT_SNI", "www.google.com")
    DEFAULT_FP: str = os.getenv("DEFAULT_FP", "chrome")
    
    # Директории
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "./data"))
    LOGS_DIR: Path = Path(os.getenv("LOGS_DIR", "./logs"))
    
    def __init__(self):
        # Создаем необходимые директории
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
    
    def get_api_key(self) -> Optional[str]:
        """Получить API ключ из файла"""
        try:
            if os.path.exists(self.API_KEY_FILE):
                with open(self.API_KEY_FILE, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        return None
    
    def save_api_key(self, api_key: str) -> None:
        """Сохранить API ключ в файл"""
        os.makedirs(os.path.dirname(self.API_KEY_FILE), exist_ok=True)
        with open(self.API_KEY_FILE, 'w') as f:
            f.write(api_key)
        # Устанавливаем права доступа только для владельца
        os.chmod(self.API_KEY_FILE, 0o600)

settings = Settings()