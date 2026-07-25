from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import decode_access_token
from backend.db.session import AsyncSessionLocal, get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效登录")

    result = await db.execute(
        text("SELECT id, username, email, role, is_active FROM users WHERE id = :id"),
        {"id": user_id},
    )
    row = result.mappings().first()
    if not row or not row["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号不可用")
    return {"id": str(row["id"]), "username": row["username"], "email": row["email"], "role": row["role"]}


def require_role(*roles: str):
    async def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in set(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return current_user

    return dependency


get_current_admin = require_role("admin")
