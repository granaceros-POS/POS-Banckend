from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.core.config import settings
from pydantic import BaseModel

# --- ¡YA NO USAMOS passlib NI bcrypt/argon2! ---
# (Hemos eliminado pwd_context, verify_password, get_password_hash)

class TokenData(BaseModel):
    username: str | None = None

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Crea el token JWT que usará la app de Android.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt