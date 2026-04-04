"""Webhook management API."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.webhook import Webhook
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


class WebhookCreate(BaseModel):
    name: str
    url: str
    secret: Optional[str] = None
    events: list[str] = ["new_article", "scrape_complete"]
    language_filter: Optional[list[str]] = None
    outlet_filter: Optional[list[int]] = None
    article_type_filter: Optional[list[str]] = None


class WebhookResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    url: str
    is_active: bool
    events: Optional[list] = None
    language_filter: Optional[list] = None
    outlet_filter: Optional[list] = None
    article_type_filter: Optional[list] = None
    total_deliveries: int = 0
    total_failures: int = 0
    last_delivery_at: Optional[str] = None
    last_response_code: Optional[int] = None


@router.post("/", response_model=WebhookResponse)
def create_webhook(data: WebhookCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Register a new webhook."""
    from app.utils.url_safety import is_safe_url
    if not is_safe_url(data.url):
        raise HTTPException(status_code=400, detail="Webhook URL is not allowed (targets internal or private network)")
    webhook = Webhook(
        name=data.name,
        url=data.url,
        secret=data.secret,
        events=data.events,
        language_filter=data.language_filter,
        outlet_filter=data.outlet_filter,
        article_type_filter=data.article_type_filter,
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.get("/", response_model=list[WebhookResponse])
def list_webhooks(db: Session = Depends(get_db)):
    """List all webhooks."""
    return db.query(Webhook).all()


@router.get("/{webhook_id}", response_model=WebhookResponse)
def get_webhook(webhook_id: int, db: Session = Depends(get_db)):
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.delete("/{webhook_id}")
def delete_webhook(webhook_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(webhook)
    db.commit()
    return {"status": "deleted"}


@router.post("/{webhook_id}/toggle")
def toggle_webhook(webhook_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    webhook.is_active = not webhook.is_active
    db.commit()
    return {"is_active": webhook.is_active}


@router.post("/{webhook_id}/test")
def test_webhook(webhook_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Send a test event to a webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    from app.services.webhook_service import _deliver
    _deliver(webhook.id, webhook.url, webhook.secret, "test", {
        "message": "This is a test webhook delivery",
    })
    return {"status": "test_sent"}
