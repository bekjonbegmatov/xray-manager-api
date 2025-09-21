import json
import asyncio
import subprocess
import uuid
from typing import Dict, List, Optional
from pathlib import Path
import logging

from .config import settings
from .models import User

logger = logging.getLogger(__name__)

class XrayManager:
    """Класс для управления Xray конфигурацией"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or settings.XRAY_CONFIG_PATH
        self.service_name = settings.XRAY_SERVICE_NAME
        
    async def _run_command(self, command: List[str]) -> tuple[int, str, str]:
        """Выполнить команду асинхронно"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode, stdout.decode(), stderr.decode()
        except Exception as e:
            logger.error(f"Ошибка выполнения команды {' '.join(command)}: {e}")
            return 1, "", str(e)
    
    async def get_config(self) -> Optional[Dict]:
        """Получить текущую конфигурацию Xray"""
        try:
            if not Path(self.config_path).exists():
                logger.warning(f"Конфигурационный файл {self.config_path} не найден")
                return None
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения конфигурации: {e}")
            return None
    
    async def save_config(self, config: Dict) -> bool:
        """Сохранить конфигурацию Xray"""
        try:
            # Создаем резервную копию
            backup_path = f"{self.config_path}.backup"
            if Path(self.config_path).exists():
                await self._run_command(["cp", self.config_path, backup_path])
            
            # Сохраняем новую конфигурацию
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    async def restart_xray(self) -> bool:
        """Перезапустить сервис Xray"""
        try:
            # Проверяем конфигурацию перед перезапуском
            returncode, stdout, stderr = await self._run_command([
                "xray", "-test", "-config", self.config_path
            ])
            
            if returncode != 0:
                logger.error(f"Конфигурация Xray невалидна: {stderr}")
                return False
            
            # Перезапускаем сервис
            returncode, stdout, stderr = await self._run_command([
                "systemctl", "restart", self.service_name
            ])
            
            if returncode != 0:
                logger.error(f"Ошибка перезапуска Xray: {stderr}")
                return False
            
            # Ждем немного и проверяем статус
            await asyncio.sleep(2)
            return await self.is_running()
            
        except Exception as e:
            logger.error(f"Ошибка перезапуска Xray: {e}")
            return False
    
    async def is_running(self) -> bool:
        """Проверить, запущен ли Xray"""
        try:
            returncode, stdout, stderr = await self._run_command([
                "systemctl", "is-active", self.service_name
            ])
            return returncode == 0 and "active" in stdout
        except Exception as e:
            logger.error(f"Ошибка проверки статуса Xray: {e}")
            return False
    
    async def get_status(self) -> Dict[str, str]:
        """Получить статус Xray сервиса"""
        try:
            returncode, stdout, stderr = await self._run_command([
                "systemctl", "status", self.service_name, "--no-pager"
            ])
            
            is_active = await self.is_running()
            
            return {
                "status": "active" if is_active else "inactive",
                "details": stdout if returncode == 0 else stderr
            }
        except Exception as e:
            logger.error(f"Ошибка получения статуса Xray: {e}")
            return {"status": "error", "details": str(e)}
    
    def generate_vless_link(self, user_uuid: str, server_ip: str = None) -> str:
        """Генерировать VLESS ссылку"""
        if not server_ip:
            server_ip = "YOUR_SERVER_IP"  # Заменить на реальный IP
        
        # Базовые параметры VLESS
        params = {
            "security": settings.DEFAULT_SECURITY,
            "encryption": "none",
            "flow": settings.DEFAULT_FLOW,
            "type": "tcp",
            "fp": settings.DEFAULT_FP,
            "sni": settings.DEFAULT_SNI,
            "pbk": "PUBLIC_KEY",  # Заменить на реальный публичный ключ
            "sid": "SHORT_ID"     # Заменить на реальный короткий ID
        }
        
        # Формируем параметры строки
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        
        # Формируем VLESS ссылку
        vless_link = f"vless://{user_uuid}@{server_ip}:{settings.DEFAULT_PORT}?{param_str}#DeltaVPN"
        
        return vless_link
    
    async def add_user(self, user: User, server_ip: str = None) -> bool:
        """Добавить пользователя в конфигурацию Xray"""
        try:
            config = await self.get_config()
            if not config:
                logger.error("Не удалось получить конфигурацию Xray")
                return False
            
            # Ищем inbound с протоколом VLESS
            vless_inbound = None
            for inbound in config.get("inbounds", []):
                if inbound.get("protocol") == "vless":
                    vless_inbound = inbound
                    break
            
            if not vless_inbound:
                logger.error("VLESS inbound не найден в конфигурации")
                return False
            
            # Добавляем пользователя
            clients = vless_inbound.get("settings", {}).get("clients", [])
            
            # Проверяем, что пользователь еще не существует
            for client in clients:
                if client.get("id") == user.uuid:
                    logger.warning(f"Пользователь {user.uuid} уже существует")
                    return True
            
            # Добавляем нового клиента
            new_client = {
                "id": user.uuid,
                "flow": settings.DEFAULT_FLOW,
                "email": user.email or f"user_{user.uuid[:8]}"
            }
            
            clients.append(new_client)
            
            # Сохраняем конфигурацию
            if await self.save_config(config):
                return await self.restart_xray()
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False
    
    async def remove_user(self, user_uuid: str) -> bool:
        """Удалить пользователя из конфигурации Xray"""
        try:
            config = await self.get_config()
            if not config:
                return False
            
            # Ищем и удаляем пользователя из всех inbound
            user_found = False
            for inbound in config.get("inbounds", []):
                if inbound.get("protocol") == "vless":
                    clients = inbound.get("settings", {}).get("clients", [])
                    original_count = len(clients)
                    
                    # Фильтруем клиентов, исключая удаляемого
                    inbound["settings"]["clients"] = [
                        client for client in clients 
                        if client.get("id") != user_uuid
                    ]
                    
                    if len(inbound["settings"]["clients"]) < original_count:
                        user_found = True
            
            if not user_found:
                logger.warning(f"Пользователь {user_uuid} не найден в конфигурации")
                return True  # Считаем успешным, если пользователя уже нет
            
            # Сохраняем конфигурацию и перезапускаем
            if await self.save_config(config):
                return await self.restart_xray()
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя: {e}")
            return False
    
    async def get_traffic_stats(self) -> Dict[str, Dict[str, int]]:
        """Получить статистику трафика (заглушка)"""
        # В реальной реализации здесь должен быть запрос к Xray API
        # Для демонстрации возвращаем пустую статистику
        return {}
    
    async def create_default_config(self) -> bool:
        """Создать базовую конфигурацию Xray"""
        try:
            default_config = {
                "log": {
                    "loglevel": "warning"
                },
                "inbounds": [
                    {
                        "port": settings.DEFAULT_PORT,
                        "protocol": "vless",
                        "settings": {
                            "clients": [],
                            "decryption": "none"
                        },
                        "streamSettings": {
                            "network": "tcp",
                            "security": "reality",
                            "realitySettings": {
                                "show": False,
                                "dest": f"{settings.DEFAULT_SNI}:443",
                                "xver": 0,
                                "serverNames": [settings.DEFAULT_SNI],
                                "privateKey": "",  # Заменить на реальный
                                "shortIds": [""]      # Заменить на реальный
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
            
            return await self.save_config(default_config)
            
        except Exception as e:
            logger.error(f"Ошибка создания конфигурации по умолчанию: {e}")
            return False

# Глобальный экземпляр менеджера
xray_manager = XrayManager()