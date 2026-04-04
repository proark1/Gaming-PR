import time
from collections import defaultdict

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import UserRegister, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_access_token,
    decode_access_token,
    get_user_by_id,
    get_user_by_username,
    get_user_by_email,
)

# Simple in-memory rate limiter per IP
_rate_limits: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(request: Request, max_requests: int = 10, window_seconds: int = 60):
    """Raise 429 if IP exceeds max_requests within window_seconds."""
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    hits = _rate_limits[ip]
    # Remove expired entries
    _rate_limits[ip] = [t for t in hits if now - t < window_seconds]
    if len(_rate_limits[ip]) >= max_requests:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
    _rate_limits[ip].append(now)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_current_user(db: Session = Depends(get_db), authorization: str = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")
    return user


def get_admin_user(user=Depends(get_current_user)):
    """Dependency that requires the current user to be an admin."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(request: Request, data: UserRegister, db: Session = Depends(get_db)):
    """Create a new user account. Rate limited to 5 per minute per IP."""
    _check_rate_limit(request, max_requests=5, window_seconds=60)
    if get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    if get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = register_user(db, data.username, data.email, data.password)
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(request: Request, data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and receive a JWT token. Rate limited to 10 per minute per IP."""
    _check_rate_limit(request, max_requests=10, window_seconds=60)
    user = authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return user
