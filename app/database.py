import aiosqlite
import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from .models import User, UserStatus
from .config import settings

class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(settings.DATA_DIR / "xray_manager.db")
        self.db_path = db_path
        
    async def init_db(self):
        """Инициализация базы данных"""
        # Создаем директорию если не существует
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    uuid TEXT PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS traffic (
                    uuid TEXT PRIMARY KEY,
                    upload INTEGER DEFAULT 0,
                    download INTEGER DEFAULT 0,
                    last_updated TEXT NOT NULL,
                    FOREIGN KEY (uuid) REFERENCES users (uuid)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            await db.commit()
    
    async def create_user(self, user: User) -> User:
        """Создать нового пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (uuid, name, email, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user.uuid, user.name, user.email, user.status.value,
                user.created_at.isoformat(), user.updated_at.isoformat()
            ))
            
            # Инициализируем трафик
            await db.execute("""
                INSERT INTO traffic (uuid, upload, download, last_updated)
                VALUES (?, 0, 0, ?)
            """, (user.uuid, datetime.utcnow().isoformat()))
            
            await db.commit()
            return user
    
    async def get_user(self, uuid: str) -> Optional[User]:
        """Получить пользователя по UUID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM users WHERE uuid = ?
            """, (uuid,))
            row = await cursor.fetchone()
            
            if row:
                return User(
                    uuid=row['uuid'],
                    name=row['name'],
                    email=row['email'],
                    status=UserStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
            return None
    
    async def get_all_users(self, status: Optional[UserStatus] = None) -> List[User]:
        """Получить всех пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if status:
                cursor = await db.execute("""
                    SELECT * FROM users WHERE status = ? ORDER BY created_at DESC
                """, (status.value,))
            else:
                cursor = await db.execute("""
                    SELECT * FROM users ORDER BY created_at DESC
                """)
            
            rows = await cursor.fetchall()
            users = []
            
            for row in rows:
                users.append(User(
                    uuid=row['uuid'],
                    name=row['name'],
                    email=row['email'],
                    status=UserStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                ))
            
            return users
    
    async def update_user(self, uuid: str, **kwargs) -> Optional[User]:
        """Обновить пользователя"""
        user = await self.get_user(uuid)
        if not user:
            return None
        
        # Обновляем поля
        if 'name' in kwargs:
            user.name = kwargs['name']
        if 'email' in kwargs:
            user.email = kwargs['email']
        if 'status' in kwargs:
            user.status = kwargs['status']
        
        user.updated_at = datetime.utcnow()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users 
                SET name = ?, email = ?, status = ?, updated_at = ?
                WHERE uuid = ?
            """, (
                user.name, user.email, user.status.value,
                user.updated_at.isoformat(), uuid
            ))
            await db.commit()
        
        return user
    
    async def delete_user(self, uuid: str) -> bool:
        """Удалить пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            # Удаляем трафик
            await db.execute("DELETE FROM traffic WHERE uuid = ?", (uuid,))
            # Удаляем пользователя
            cursor = await db.execute("DELETE FROM users WHERE uuid = ?", (uuid,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_traffic(self, uuid: str) -> Optional[dict]:
        """Получить трафик пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM traffic WHERE uuid = ?
            """, (uuid,))
            row = await cursor.fetchone()
            
            if row:
                return {
                    'uuid': row['uuid'],
                    'upload': row['upload'],
                    'download': row['download'],
                    'total': row['upload'] + row['download'],
                    'last_updated': datetime.fromisoformat(row['last_updated'])
                }
            return None
    
    async def update_traffic(self, uuid: str, upload: int, download: int) -> bool:
        """Обновить трафик пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE traffic 
                SET upload = ?, download = ?, last_updated = ?
                WHERE uuid = ?
            """, (upload, download, datetime.utcnow().isoformat(), uuid))
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_stats(self) -> dict:
        """Получить статистику"""
        async with aiosqlite.connect(self.db_path) as db:
            # Общее количество пользователей
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            total_users = (await cursor.fetchone())[0]
            
            # Активные пользователи
            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE status = ?", (UserStatus.ACTIVE.value,))
            active_users = (await cursor.fetchone())[0]
            
            # Приостановленные пользователи
            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE status = ?", (UserStatus.SUSPENDED.value,))
            suspended_users = (await cursor.fetchone())[0]
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'suspended_users': suspended_users
            }
    
    async def set_config(self, key: str, value: str) -> None:
        """Сохранить конфигурацию"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.utcnow().isoformat()))
            await db.commit()
    
    async def get_config(self, key: str) -> Optional[str]:
        """Получить конфигурацию"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = await cursor.fetchone()
            return row[0] if row else None

# Глобальный экземпляр базы данных
db = Database()