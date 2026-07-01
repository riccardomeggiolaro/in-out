import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


def generate_api_key() -> str:
    """Genera una nuova API key in chiaro (mostrata una sola volta al momento della creazione)."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Le API key sono ad alta entropia: un hash sha256 indicizzabile è sufficiente e permette
    una lookup diretta (a differenza di bcrypt, che richiederebbe un confronto per ogni sito)."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
