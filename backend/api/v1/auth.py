import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.core.responses import ok
from backend.core.security import create_access_token, hash_password, verify_password
from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.schemas.auth import LoginRequest, RegisterRequest, TokenData


router = APIRouter()


@router.post("/register")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> dict:
    exists = await db.execute(
        text("SELECT id FROM users WHERE username = :username LIMIT 1"),
        {"username": payload.username},
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")

    password_hash = hash_password(payload.password)
    result = await db.execute(
        text(
            """
            INSERT INTO users (username, hashed_password)
            VALUES (:username, :hashed_password)
            RETURNING id, username
            """
        ),
        {"username": payload.username, "hashed_password": password_hash},
    )
    await db.commit()
    user = result.mappings().one()
    return ok({"id": str(user["id"]), "username": user["username"]}, "注册成功")


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        text(
            """
            SELECT id, username, hashed_password, is_active
            FROM users WHERE username = :username LIMIT 1
            """
        ),
        {"username": payload.username},
    )
    user = result.mappings().first()
    if not user or not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    loop = asyncio.get_running_loop()
    password_ok = await loop.run_in_executor(
        None,
        verify_password,
        payload.password,
        user["hashed_password"],
    )
    if not password_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    settings = get_settings()
    token = create_access_token(str(user["id"]), {"username": user["username"]})
    token_data = TokenData(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user_id=str(user["id"]),
        username=user["username"],
    )
    return ok(token_data.model_dump())


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    return ok(current_user)
