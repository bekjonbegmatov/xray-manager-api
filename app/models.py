from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid

class UserStatus(str, Enum):
    """Статусы пользователей"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class UserCreate(BaseModel):
    """Модель для создания пользователя"""
    name: Optional[str] = Field(None, description="Имя пользователя")
    email: Optional[str] = Field(None, description="Email пользователя")

class UserResponse(BaseModel):
    """Модель ответа при создании/получении пользователя"""
    uuid: str = Field(..., description="UUID пользователя")
    name: Optional[str] = Field(None, description="Имя пользователя")
    email: Optional[str] = Field(None, description="Email пользователя")
    vless_link: str = Field(..., description="VLESS ссылка для подключения")
    status: UserStatus = Field(..., description="Статус пользователя")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата последнего обновления")

class UserUpdate(BaseModel):
    """Модель для обновления пользователя"""
    name: Optional[str] = Field(None, description="Имя пользователя")
    email: Optional[str] = Field(None, description="Email пользователя")

class TrafficResponse(BaseModel):
    """Модель ответа с информацией о трафике"""
    uuid: str = Field(..., description="UUID пользователя")
    upload: int = Field(..., description="Исходящий трафик в байтах")
    download: int = Field(..., description="Входящий трафик в байтах")
    total: int = Field(..., description="Общий трафик в байтах")
    last_updated: datetime = Field(..., description="Время последнего обновления")

class StatusResponse(BaseModel):
    """Модель ответа статуса сервиса"""
    xray_status: str = Field(..., description="Статус Xray сервиса")
    api_status: str = Field(..., description="Статус API")
    total_users: int = Field(..., description="Общее количество пользователей")
    active_users: int = Field(..., description="Количество активных пользователей")
    suspended_users: int = Field(..., description="Количество приостановленных пользователей")
    uptime: str = Field(..., description="Время работы сервиса")

class APIResponse(BaseModel):
    """Базовая модель API ответа"""
    success: bool = Field(..., description="Успешность операции")
    message: str = Field(..., description="Сообщение")
    data: Optional[dict] = Field(None, description="Данные ответа")

class ErrorResponse(BaseModel):
    """Модель ошибки"""
    success: bool = Field(False, description="Успешность операции")
    error: str = Field(..., description="Описание ошибки")
    code: int = Field(..., description="Код ошибки")

# Модели для базы данных
class User:
    """Модель пользователя для базы данных"""
    def __init__(self, uuid: str, name: Optional[str] = None, email: Optional[str] = None,
                 status: UserStatus = UserStatus.ACTIVE, created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.uuid = uuid
        self.name = name
        self.email = email
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'uuid': self.uuid,
            'name': self.name,
            'email': self.email,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Создать из словаря"""
        return cls(
            uuid=data['uuid'],
            name=data.get('name'),
            email=data.get('email'),
            status=UserStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )