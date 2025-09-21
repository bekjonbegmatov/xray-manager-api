from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import logging
import uuid
from typing import Dict, List

from .config import settings
from .models import (
    UserCreate, UserResponse, UserUpdate, TrafficResponse, 
    StatusResponse, APIResponse, ErrorResponse, UserStatus
)
from .database import database
from .xray_manager import xray_manager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Xray Manager API",
    description="REST API для управления Xray/VLESS пользователями",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить конкретными доменами
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка аутентификации
security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Проверка API ключа"""
    if not settings.verify_api_key(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный API ключ",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    try:
        # Инициализация базы данных
        await database.init_db()
        logger.info("База данных инициализирована")
        
        # Проверка статуса Xray
        status = await xray_manager.get_status()
        logger.info(f"Статус Xray: {status}")
        
        # Генерация API ключа если не существует
        if not settings.API_KEY:
            api_key = settings.generate_api_key()
            logger.info(f"Сгенерирован новый API ключ: {api_key}")
        
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")

@app.get("/", response_model=APIResponse)
async def root():
    """Корневой эндпоинт"""
    return APIResponse(
        success=True,
        message="Xray Manager API работает",
        data={"version": "1.0.0"}
    )

@app.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    api_key: str = Depends(verify_api_key)
):
    """Создать нового VLESS пользователя"""
    try:
        # Генерируем UUID для пользователя
        user_uuid = str(uuid.uuid4())
        
        # Создаем пользователя в базе данных
        user = await database.create_user(
            uuid=user_uuid,
            email=user_data.email,
            name=user_data.name,
            traffic_limit=user_data.traffic_limit
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка создания пользователя в базе данных"
            )
        
        # Добавляем пользователя в конфигурацию Xray
        if not await xray_manager.add_user(user):
            # Если не удалось добавить в Xray, удаляем из базы
            await database.delete_user(user_uuid)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка добавления пользователя в Xray"
            )
        
        # Генерируем VLESS ссылку
        vless_link = xray_manager.generate_vless_link(user_uuid)
        
        return UserResponse(
            uuid=user_uuid,
            email=user.email,
            name=user.name,
            status=UserStatus.ACTIVE,
            vless_link=vless_link,
            traffic_limit=user.traffic_limit,
            traffic_used=0,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@app.delete("/users/{user_uuid}", response_model=APIResponse)
async def delete_user(
    user_uuid: str,
    api_key: str = Depends(verify_api_key)
):
    """Удалить пользователя"""
    try:
        # Проверяем существование пользователя
        user = await database.get_user(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Удаляем из конфигурации Xray
        if not await xray_manager.remove_user(user_uuid):
            logger.warning(f"Не удалось удалить пользователя {user_uuid} из Xray")
        
        # Удаляем из базы данных
        if await database.delete_user(user_uuid):
            return APIResponse(
                success=True,
                message="Пользователь успешно удален"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка удаления пользователя из базы данных"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@app.post("/users/{user_uuid}/suspend", response_model=APIResponse)
async def suspend_user(
    user_uuid: str,
    api_key: str = Depends(verify_api_key)
):
    """Приостановить пользователя"""
    try:
        # Проверяем существование пользователя
        user = await database.get_user(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        if user.status == UserStatus.SUSPENDED:
            return APIResponse(
                success=True,
                message="Пользователь уже приостановлен"
            )
        
        # Удаляем из конфигурации Xray (временно)
        if not await xray_manager.remove_user(user_uuid):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка приостановки пользователя в Xray"
            )
        
        # Обновляем статус в базе данных
        if await database.update_user_status(user_uuid, UserStatus.SUSPENDED):
            return APIResponse(
                success=True,
                message="Пользователь успешно приостановлен"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка обновления статуса пользователя"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка приостановки пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@app.post("/users/{user_uuid}/resume", response_model=APIResponse)
async def resume_user(
    user_uuid: str,
    api_key: str = Depends(verify_api_key)
):
    """Возобновить пользователя"""
    try:
        # Проверяем существование пользователя
        user = await database.get_user(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        if user.status == UserStatus.ACTIVE:
            return APIResponse(
                success=True,
                message="Пользователь уже активен"
            )
        
        # Добавляем обратно в конфигурацию Xray
        if not await xray_manager.add_user(user):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка возобновления пользователя в Xray"
            )
        
        # Обновляем статус в базе данных
        if await database.update_user_status(user_uuid, UserStatus.ACTIVE):
            return APIResponse(
                success=True,
                message="Пользователь успешно возобновлен"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка обновления статуса пользователя"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка возобновления пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@app.get("/users/{user_uuid}", response_model=UserResponse)
async def get_user(
    user_uuid: str,
    api_key: str = Depends(verify_api_key)
):
    """Получить информацию о пользователе"""
    try:
        user = await database.get_user(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Генерируем VLESS ссылку
        vless_link = xray_manager.generate_vless_link(user_uuid)
        
        return UserResponse(
            uuid=user.uuid,
            email=user.email,
            name=user.name,
            status=user.status,
            vless_link=vless_link,
            traffic_limit=user.traffic_limit,
            traffic_used=user.traffic_used,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@app.get("/users", response_model=List[UserResponse])
async def list_users(
    api_key: str = Depends(verify_api_key)
):
    """Получить список всех пользователей"""
    try:
        users = await database.get_all_users()
        result = []
        
        for user in users:
            vless_link = xray_manager.generate_vless_link(user.uuid)
            result.append(UserResponse(
                uuid=user.uuid,
                email=user.email,
                name=user.name,
                status=user.status,
                vless_link=vless_link,
                traffic_limit=user.traffic_limit,
                traffic_used=user.traffic_used,
                created_at=user.created_at
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@app.get("/traffic/{user_uuid}", response_model=TrafficResponse)
async def get_user_traffic(
    user_uuid: str,
    api_key: str = Depends(verify_api_key)
):
    """Получить статистику трафика пользователя"""
    try:
        # Проверяем существование пользователя
        user = await database.get_user(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Получаем статистику трафика из Xray
        traffic_stats = await xray_manager.get_traffic_stats()
        user_traffic = traffic_stats.get(user_uuid, {"uplink": 0, "downlink": 0})
        
        return TrafficResponse(
            uuid=user_uuid,
            uplink=user_traffic.get("uplink", 0),
            downlink=user_traffic.get("downlink", 0),
            total=user_traffic.get("uplink", 0) + user_traffic.get("downlink", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения трафика пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@app.get("/status", response_model=StatusResponse)
async def get_status(api_key: str = Depends(verify_api_key)):
    """Получить статус Xray сервиса"""
    try:
        xray_status = await xray_manager.get_status()
        
        return StatusResponse(
            xray_status=xray_status["status"],
            xray_details=xray_status.get("details", ""),
            api_version="1.0.0",
            users_count=await database.get_users_count()
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обработчик HTTP исключений"""
    return ErrorResponse(
        success=False,
        error=exc.detail,
        status_code=exc.status_code
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Обработчик общих исключений"""
    logger.error(f"Необработанная ошибка: {exc}")
    return ErrorResponse(
        success=False,
        error="Внутренняя ошибка сервера",
        status_code=500
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )