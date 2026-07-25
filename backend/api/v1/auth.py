import asyncio
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.core.responses import ok
from backend.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.schemas.auth import LoginRequest, RefreshTokenRequest, RegisterRequest, TokenData


router = APIRouter()


@router.post("/register")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> dict:
    user_count_result = await db.execute(text("SELECT COUNT(*) FROM users"))
    is_first_user = int(user_count_result.scalar_one() or 0) == 0
    role = payload.role if is_first_user else "user"
    exists = await db.execute(
        text("SELECT id FROM users WHERE username = :username OR email = :email LIMIT 1"),
        {"username": payload.username, "email": payload.email},
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名或邮箱已存在")

    password_hash = hash_password(payload.password)
    result = await db.execute(
        text(
            """
            INSERT INTO users (username, email, hashed_password, role)
            VALUES (:username, :email, :hashed_password, :role)
            RETURNING id, username, email, role
            """
        ),
        {
            "username": payload.username,
            "email": payload.email,
            "hashed_password": password_hash,
            "role": role,
        },
    )
    await db.commit()
    user = result.mappings().one()
    return ok(
        {"id": str(user["id"]), "username": user["username"], "email": user["email"], "role": user["role"]},
        "注册成功",
    )


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    settings = get_settings()
    result = await db.execute(
        text(
            """
            SELECT id, username, email, role, hashed_password, is_active, login_attempts, locked_until
            FROM users
            WHERE username = :identifier OR email = :identifier
            LIMIT 1
            """
        ),
        {"identifier": payload.username},
    )
    user = result.mappings().first()
    if not user or not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if user.get("locked_until") and user["locked_until"] > datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="登录失败次数过多，请稍后再试")

    loop = asyncio.get_running_loop()
    password_ok = await loop.run_in_executor(
        None,
        verify_password,
        payload.password,
        user["hashed_password"],
    )
    if not password_ok:
        attempts = int(user.get("login_attempts") or 0) + 1
        locked_until = None
        if attempts >= settings.login_max_attempts:
            locked_until = datetime.now(UTC) + timedelta(minutes=settings.login_lock_minutes)
        await db.execute(
            text(
                """
                UPDATE users
                SET login_attempts = :attempts,
                    locked_until = :locked_until,
                    updated_at = NOW()
                WHERE id = :user_id
                """
            ),
            {"attempts": attempts, "locked_until": locked_until, "user_id": user["id"]},
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    refresh_token = create_refresh_token()
    refresh_expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    await db.execute(
        text(
            """
            UPDATE users
            SET login_attempts = 0,
                locked_until = NULL,
                last_login_at = NOW(),
                refresh_token_hash = :refresh_token_hash,
                refresh_token_expires_at = :refresh_token_expires_at,
                updated_at = NOW()
            WHERE id = :user_id
            """
        ),
        {
            "refresh_token_hash": hash_refresh_token(refresh_token),
            "refresh_token_expires_at": refresh_expires_at,
            "user_id": user["id"],
        },
    )
    await db.commit()
    token = create_access_token(str(user["id"]), {"username": user["username"], "role": user["role"]})
    token_data = TokenData(
        access_token=token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_expires_in=settings.refresh_token_expire_days * 86400,
        user_id=str(user["id"]),
        username=user["username"],
        email=user["email"],
        role=user["role"],
    )
    return ok(token_data.model_dump())


@router.post("/refresh")
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> dict:
    settings = get_settings()
    token_hash = hash_refresh_token(payload.refresh_token)
    result = await db.execute(
        text(
            """
            SELECT id, username, email, role, is_active, refresh_token_expires_at
            FROM users
            WHERE refresh_token_hash = :token_hash
            LIMIT 1
            """
        ),
        {"token_hash": token_hash},
    )
    user = result.mappings().first()
    if not user or not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌无效")
    if not user["refresh_token_expires_at"] or user["refresh_token_expires_at"] <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌已过期")

    new_refresh_token = create_refresh_token()
    refresh_expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    await db.execute(
        text(
            """
            UPDATE users
            SET refresh_token_hash = :refresh_token_hash,
                refresh_token_expires_at = :refresh_token_expires_at,
                updated_at = NOW()
            WHERE id = :user_id
            """
        ),
        {
            "refresh_token_hash": hash_refresh_token(new_refresh_token),
            "refresh_token_expires_at": refresh_expires_at,
            "user_id": user["id"],
        },
    )
    await db.commit()
    access_token = create_access_token(str(user["id"]), {"username": user["username"], "role": user["role"]})
    return ok(
        TokenData(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_expires_in=settings.refresh_token_expire_days * 86400,
            user_id=str(user["id"]),
            username=user["username"],
            email=user["email"],
            role=user["role"],
        ).model_dump()
    )


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    return ok(current_user)
