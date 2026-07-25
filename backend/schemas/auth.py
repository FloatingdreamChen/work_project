import re

from pydantic import BaseModel, Field, field_validator


PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="user", description="user/admin")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise ValueError("邮箱格式不正确")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not PASSWORD_PATTERN.match(value):
            raise ValueError("密码必须包含大小写字母和数字")
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in {"user", "admin"}:
            raise ValueError("角色只能是 user 或 admin")
        return value


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)


class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    user_id: str
    username: str
    email: str | None = None
    role: str = "user"
