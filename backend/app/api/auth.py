"""
MediaFlux Hub - Authentication API
API для аутентификации и управления сессиями
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger("mediaflux_hub.auth")

# Настройка шифрования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка JWT Bearer токенов
security = HTTPBearer()

router = APIRouter()

# Pydantic модели
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: dict

class UserInfo(BaseModel):
    username: str
    is_admin: bool
    last_login: Optional[datetime]


# Временная система аутентификации для MediaFlux Hub
# В реальном проекте здесь должна быть полноценная система пользователей
DEMO_USERS = {
    "admin": {
        "username": "admin",
        "password_hash": pwd_context.hash("mediaflux2024"),  # mediaflux2024
        "is_admin": True
    },
    "user": {
        "username": "user", 
        "password_hash": pwd_context.hash("user123"),  # user123
        "is_admin": False
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Проверка JWT токена"""
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Проверяем существование пользователя
        if username not in DEMO_USERS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "username": username,
            "is_admin": DEMO_USERS[username]["is_admin"]
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Вход в систему MediaFlux Hub
    
    Демо аккаунты:
    - admin / mediaflux2024 (администратор)
    - user / user123 (обычный пользователь)
    """
    logger.info(f"🔐 MediaFlux Hub: Попытка входа пользователя: {request.username}")
    
    # Проверяем существование пользователя
    if request.username not in DEMO_USERS:
        logger.warning(f"⚠️ MediaFlux Hub: Неизвестный пользователь: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    user = DEMO_USERS[request.username]
    
    # Проверяем пароль
    if not verify_password(request.password, user["password_hash"]):
        logger.warning(f"⚠️ MediaFlux Hub: Неверный пароль для пользователя: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    # Создаем токен
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "admin": user["is_admin"]},
        expires_delta=access_token_expires
    )
    
    logger.info(f"✅ MediaFlux Hub: Успешный вход пользователя: {request.username}")
    
    return LoginResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_info={
            "username": user["username"],
            "is_admin": user["is_admin"],
            "last_login": datetime.now().isoformat()
        }
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(verify_token)):
    """Выход из системы"""
    logger.info(f"👋 MediaFlux Hub: Выход пользователя: {current_user['username']}")
    
    # В реальной системе здесь можно добавить токен в blacklist
    # Пока просто возвращаем успешный ответ
    
    return {
        "message": "Вы успешно вышли из системы MediaFlux Hub",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/me", response_model=UserInfo)
async def get_current_user(current_user: dict = Depends(verify_token)):
    """Получение информации о текущем пользователе"""
    user_data = DEMO_USERS[current_user["username"]]
    
    return UserInfo(
        username=current_user["username"],
        is_admin=current_user["is_admin"],
        last_login=datetime.now()
    )


@router.get("/verify")
async def verify_access(current_user: dict = Depends(verify_token)):
    """Проверка действительности токена"""
    return {
        "valid": True,
        "user": current_user["username"],
        "is_admin": current_user["is_admin"],
        "timestamp": datetime.now().isoformat()
    }


# Декоратор для проверки прав администратора
def require_admin(current_user: dict = Depends(verify_token)) -> dict:
    """Проверка прав администратора"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа. Требуются права администратора."
        )
    return current_user


@router.get("/admin/test")
async def admin_test(admin_user: dict = Depends(require_admin)):
    """Тестовый endpoint для проверки прав администратора"""
    return {
        "message": "Доступ разрешен для администратора",
        "admin": admin_user["username"],
        "timestamp": datetime.now().isoformat()
    } 