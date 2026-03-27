from fastapi import APIRouter, Depends, Header, HTTPException
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

    user = get_user_by_id(db, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
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
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return user
