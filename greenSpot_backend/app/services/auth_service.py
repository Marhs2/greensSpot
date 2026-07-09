from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
from app.core.config import settings
from app.models.models import RefreshToken, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import string


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "exp": expire, "type": "access", "jti": secrets.token_hex(8)}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": user_id, "exp": expire, "type": "refresh", "jti": secrets.token_hex(8)}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str, token_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != token_type:
            raise JWTError("Invalid token type")
        return payload
    except JWTError:
        return None


def generate_id() -> str:
    return secrets.token_hex(8)


def generate_share_id() -> str:
    chars = string.ascii_lowercase + string.digits
    return "sh_" + "".join(secrets.choice(chars) for _ in range(8))


async def create_refresh_token_db(db: AsyncSession, user_id: str) -> str:
    token = create_refresh_token(user_id)
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    refresh_token = RefreshToken(
        id=generate_id(),
        user_id=user_id,
        token=token,
        expires_at=expire,
    )
    db.add(refresh_token)
    await db.commit()
    return token


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str) -> User:
    user = User(
        id=generate_id(),
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def validate_refresh_token(db: AsyncSession, token: str):
    payload = decode_token(token, "refresh")
    if not payload:
        return None

    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token == token)
        .where(RefreshToken.expires_at > datetime.utcnow())
    )
    refresh_token = result.scalar_one_or_none()
    if not refresh_token:
        return None

    user = await get_user_by_id(db, refresh_token.user_id)
    return user


async def revoke_refresh_token(db: AsyncSession, token: str):
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == token))
    refresh_token = result.scalar_one_or_none()
    if refresh_token:
        await db.delete(refresh_token)
        await db.commit()