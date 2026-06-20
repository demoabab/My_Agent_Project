from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from chatchat.settings import Settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_jwt_secret() -> str:
    return Settings.basic_settings.JWT_SECRET_KEY


def get_jwt_algorithm() -> str:
    return Settings.basic_settings.JWT_ALGORITHM


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        or timedelta(minutes=Settings.basic_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, get_jwt_secret(), algorithm=get_jwt_algorithm())


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, get_jwt_secret(), algorithms=[get_jwt_algorithm()]
        )
        return payload
    except JWTError:
        return {}


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
