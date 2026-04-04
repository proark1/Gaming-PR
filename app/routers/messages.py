from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessageWithTranslations,
    MessageTranslationResponse,
)
from app.schemas.personalization import MessagePersonalizationResponse, PersonalizeRequest
from app.services.message_translation_service import (
    create_message,
    get_message,
    list_messages,
    update_message,
    delete_message,
    translate_message,
)
from app.services.personalization_service import (
    generate_personalizations,
    retry_failed_personalizations,
)
from app.models.message import Message, MessageTranslation
from app.models.personalization import MessagePersonalization
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


def _run_translation(message_id: int):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        translate_message(db, message_id)
    finally:
        db.close()


@router.post("/", response_model=MessageResponse, status_code=201)
def create(data: MessageCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Create a new message. Automatically triggers background translation based on category."""
    message = create_message(db, data)
    background_tasks.add_task(_run_translation, message.id)
    return message


@router.get("/", response_model=list[MessageResponse])
def list_all(category: Optional[str] = None, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """List messages with optional category filter and pagination."""
    return list_messages(db, category=category, skip=skip, limit=limit)


@router.get("/{message_id}", response_model=MessageWithTranslations)
def get_one(message_id: int, include_translations: bool = True, db: Session = Depends(get_db)):
    """Get a single message with its translations."""
    message = get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if not include_translations:
        message.translations = []
    return message


@router.put("/{message_id}", response_model=MessageResponse)
def update(message_id: int, data: MessageUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Update a message. Re-translates if title or body changed."""
    message = update_message(db, message_id, data)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if data.title is not None or data.body is not None:
        background_tasks.add_task(_run_translation, message.id)
    return message


@router.delete("/{message_id}", status_code=204)
def delete(message_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Delete a message and all its translations."""
    if not delete_message(db, message_id):
        raise HTTPException(status_code=404, detail="Message not found")


@router.get("/{message_id}/translations/", response_model=list[MessageTranslationResponse])
def list_translations(message_id: int, db: Session = Depends(get_db)):
    """List all translations for a message."""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message.translations


@router.post("/{message_id}/translations/retry", response_model=list[MessageTranslationResponse])
def retry_translations(message_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Retry failed and pending translations. Skips already completed ones."""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    def _run():
        from app.database import SessionLocal
        session = SessionLocal()
        try:
            translate_message(session, message_id, retry_only=True)
        finally:
            session.close()

    background_tasks.add_task(_run)
    return message.translations


# ─── Personalization endpoints ───

@router.post("/{message_id}/personalize")
def personalize_message(
    message_id: int,
    request: PersonalizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Trigger personalization generation for all (or selected) contacts. Runs in background."""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    from app.services.personalization_service import get_contacts_for_message
    contacts = get_contacts_for_message(db, message)
    if request.target_ids is not None:
        contacts = [c for c in contacts if c["id"] in request.target_ids]

    def _run():
        from app.database import SessionLocal
        session = SessionLocal()
        try:
            generate_personalizations(session, message_id, target_ids=request.target_ids)
        finally:
            session.close()

    background_tasks.add_task(_run)
    return {"queued": len(contacts), "message": "Personalization started in background"}


@router.get("/{message_id}/personalizations", response_model=list[MessagePersonalizationResponse])
def list_personalizations(
    message_id: int,
    status: Optional[str] = None,
    target_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List personalized messages for a specific message, with optional status/type filters."""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    q = db.query(MessagePersonalization).filter(MessagePersonalization.message_id == message_id)
    if status:
        q = q.filter(MessagePersonalization.status == status)
    if target_type:
        q = q.filter(MessagePersonalization.target_type == target_type)
    return q.order_by(MessagePersonalization.target_name).all()


@router.post("/{message_id}/personalizations/retry", response_model=list[MessagePersonalizationResponse])
def retry_personalizations(
    message_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Retry failed/pending personalizations for a message."""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    pending = (
        db.query(MessagePersonalization)
        .filter(
            MessagePersonalization.message_id == message_id,
            MessagePersonalization.status.in_(["failed", "pending"]),
        )
        .all()
    )

    def _run():
        from app.database import SessionLocal
        session = SessionLocal()
        try:
            retry_failed_personalizations(session, message_id)
        finally:
            session.close()

    background_tasks.add_task(_run)
    return pending
