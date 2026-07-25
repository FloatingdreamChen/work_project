import pytest
from pydantic import ValidationError

from backend.core.security import create_refresh_token, hash_refresh_token
from backend.schemas.auth import RegisterRequest


def test_register_requires_reasonable_password_and_email() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(username="demo", email="bad-email", password="weakpass")

    payload = RegisterRequest(username="demo", email="Demo@Example.com", password="Demo123456")

    assert payload.email == "demo@example.com"
    assert payload.role == "user"


def test_refresh_token_is_hashable_and_not_plaintext() -> None:
    token = create_refresh_token()
    hashed = hash_refresh_token(token)

    assert len(token) >= 40
    assert hashed != token
    assert hash_refresh_token(token) == hashed
