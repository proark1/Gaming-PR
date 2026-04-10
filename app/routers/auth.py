"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import base64
import hashlib

from app.config import settings
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = None


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: str = None
    message: str = None


def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(plain) == hashed


def create_token(email: str) -> str:
    """Create a simple token (base64 encoded email:timestamp)."""
    import time
    token_data = f"{email}:{int(time.time())}"
    return base64.b64encode(token_data.encode()).decode()


@router.post("/register", response_model=LoginResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Validate password length
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    # Create user
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Return token
    token = create_token(request.email)
    return LoginResponse(success=True, token=token)


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return auth token."""
    # Check if email/password match admin credentials
    if request.email == settings.ADMIN_EMAIL and request.password == settings.ADMIN_PASSWORD:
        token = create_token(request.email)
        return LoginResponse(success=True, token=token)

    # Check database for user
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    token = create_token(request.email)
    return LoginResponse(success=True, token=token)


@router.post("/logout")
def logout():
    """Logout (client-side clears token)."""
    return {"success": True}


@router.get("/verify")
def verify_token(token: str = None, db: Session = Depends(get_db)):
    """Verify if token is valid."""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")

    try:
        decoded = base64.b64decode(token.encode()).decode()
        email = decoded.split(':')[0]
        # Token is valid if it's the admin
        if email == settings.ADMIN_EMAIL:
            return {"success": True, "email": email}
        # Or if the email belongs to a registered active user
        user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
        if user:
            return {"success": True, "email": email}
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Invalid token")

