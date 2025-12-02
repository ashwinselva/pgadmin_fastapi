from typing import Optional
import os
import jwt
from datetime import datetime, timedelta
import bcrypt

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    # Convert to bytes and hash
    password_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against the hashed value."""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=JWT_EXP_MINUTES))
    payload = {"sub": str(user_id), "exp": expire, "iat": now}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_access_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        return user_id
    except Exception:
        return None


def revoke_access_token(token: str) -> None:
    # Stateless JWTs can't be revoked without a store. Keep a no-op here for API compatibility.
    return None

