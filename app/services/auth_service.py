import hashlib
import hmac
import json
import base64
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User


# --- Password hashing using hashlib (PBKDF2-SHA256) ---

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    salt, key_hex = hashed_password.split("$", 1)
    key = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt.encode(), 100000)
    return hmac.compare_digest(key.hex(), key_hex)


# --- JWT using hmac (HS256 only) ---

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_access_token(data: dict) -> str:
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    payload["exp"] = int(expire.timestamp())
    payload_encoded = _b64url_encode(json.dumps(payload).encode())
    signing_input = f"{header}.{payload_encoded}"
    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        signing_input = f"{parts[0]}.{parts[1]}"
        expected_sig = hmac.new(
            settings.JWT_SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256
        ).digest()
        actual_sig = _b64url_decode(parts[2])
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64url_decode(parts[1]))
        if payload.get("exp") and payload["exp"] < datetime.now(timezone.utc).timestamp():
            return None
        return payload
    except Exception:
        return None


# --- User operations ---

def register_user(db: Session, username: str, email: str, password: str) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()
