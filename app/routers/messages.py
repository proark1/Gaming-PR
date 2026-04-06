"""Message endpoints for outlet communication."""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import base64

from app.config import settings
from app.database import get_db
from app.models.message import Message, MessageStatus
from app.models.outlet import GamingOutlet
from app.models.user import User
from app.schemas.message import MessageCreate, MessageUpdate, MessageResponse, MessageListResponse

router = APIRouter(prefix="/api/messages", tags=["messages"])


def get_current_user(token: Optional[str] = Query(None), db: Session = Depends(get_db)) -> User:
    """Get current user from token."""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")

    try:
        # Decode token to extract email
        decoded = base64.b64decode(token.encode()).decode()
        email = decoded.split(':')[0]

        # Check if it's the admin user
        if email == settings.ADMIN_EMAIL:
            # Create or get admin user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(email=email, password_hash="", full_name="Administrator")
                db.add(user)
                db.commit()
                db.refresh(user)
            return user

        # Look up user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")

        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/", response_model=MessageResponse)
def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new message (draft or send immediately)."""
    # Verify outlet exists
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == message.outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    # Create message
    db_message = Message(
        outlet_id=message.outlet_id,
        user_id=current_user.id,
        subject=message.subject,
        body=message.body,
        message_type=message.message_type,
        status=MessageStatus.draft,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


@router.get("/", response_model=list[MessageListResponse])
def list_messages(
    outlet_id: Optional[int] = None,
    status: Optional[MessageStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List messages (filtered by outlet and status)."""
    query = db.query(Message).filter(Message.user_id == current_user.id)

    if outlet_id:
        query = query.filter(Message.outlet_id == outlet_id)
    if status:
        query = query.filter(Message.status == status)

    return query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{message_id}", response_model=MessageResponse)
def get_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get message detail."""
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.user_id == current_user.id,
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message


@router.put("/{message_id}", response_model=MessageResponse)
def update_message(
    message_id: int,
    update: MessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update message (only if draft)."""
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.user_id == current_user.id,
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.status != MessageStatus.draft:
        raise HTTPException(status_code=400, detail="Can only edit draft messages")

    # Update fields
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(message, field, value)

    message.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(message)

    return message


@router.post("/{message_id}/send", response_model=MessageResponse)
def send_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a draft message via email."""
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.user_id == current_user.id,
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.status != MessageStatus.draft:
        raise HTTPException(status_code=400, detail="Can only send draft messages")

    # Get outlet
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == message.outlet_id).first()
    if not outlet or not outlet.contact_email:
        raise HTTPException(status_code=400, detail="Outlet has no contact email")

    # Send via email service
    try:
        from app.services.email_service import send_email_to_outlet

        email_message_id = send_email_to_outlet(
            outlet=outlet,
            subject=message.subject,
            body=message.body,
            message_type=str(message.message_type),
        )

        # Update message status
        message.status = MessageStatus.sent
        message.sent_at = datetime.now(timezone.utc)
        message.sent_via_email = True
        message.email_message_id = email_message_id

    except Exception as e:
        message.status = MessageStatus.failed
        # Continue anyway to save the attempt

    message.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(message)

    return message


@router.delete("/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete message."""
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.user_id == current_user.id,
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()

    return {"success": True}


@router.get("/outlets/{outlet_id}/messages", response_model=list[MessageListResponse])
def get_outlet_messages(
    outlet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all messages for a specific outlet."""
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    messages = db.query(Message).filter(
        Message.outlet_id == outlet_id,
        Message.user_id == current_user.id,
    ).order_by(Message.created_at.desc()).all()

    return messages
