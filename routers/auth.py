from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

from database import get_db
from models import AdminUser
from schemas import LoginRequest, TokenResponse
from config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_admin(token: str, db: Session) -> AdminUser:
    """驗證 JWT，回傳管理員物件"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無效的認證憑證",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = db.query(AdminUser).filter(AdminUser.username == username, AdminUser.is_active == True).first()
    if user is None:
        raise credentials_exception
    return user


def ensure_default_admin(db: Session):
    """若資料庫中沒有任何管理員，自動建立預設帳號"""
    if not db.query(AdminUser).first():
        admin = AdminUser(
            username=settings.ADMIN_USERNAME,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            display_name="系統管理員",
        )
        db.add(admin)
        db.commit()
        print(f"✅ 預設管理員帳號已建立: {settings.ADMIN_USERNAME}")


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """管理員登入"""
    ensure_default_admin(db)

    user = db.query(AdminUser).filter(
        AdminUser.username == payload.username,
        AdminUser.is_active == True,
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
        )

    token = create_access_token({"sub": user.username})
    return TokenResponse(
        access_token=token,
        display_name=user.display_name,
    )
