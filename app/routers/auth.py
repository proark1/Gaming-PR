"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import base64

from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: str = None
    message: str = None


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Authenticate user and return auth token."""
    if request.email == settings.ADMIN_EMAIL and request.password == settings.ADMIN_PASSWORD:
        # Create a simple token (base64 encoded email:timestamp)
        import time
        token_data = f"{request.email}:{int(time.time())}"
        token = base64.b64encode(token_data.encode()).decode()
        return LoginResponse(success=True, token=token)

    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/logout")
def logout():
    """Logout (client-side clears token)."""
    return {"success": True}


@router.get("/verify")
def verify_token(token: str = None):
    """Verify if token is valid."""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")

    try:
        decoded = base64.b64decode(token.encode()).decode()
        email = decoded.split(':')[0]
        if email == settings.ADMIN_EMAIL:
            return {"success": True, "email": email}
    except:
        pass

    raise HTTPException(status_code=401, detail="Invalid token")
