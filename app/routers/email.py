from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.email import (
    DomainCreate,
    DomainResponse,
    DomainVerifyResponse,
    EmailBatchSend,
    EmailListResponse,
    EmailResponse,
    EmailSend,
    EmailStatsResponse,
)
from app.services import email_service
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/email", tags=["Email"])


# ── Domain Endpoints ──

@router.post("/domains", response_model=DomainResponse, status_code=201)
def add_domain(payload: DomainCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Connect a domain for email sending. Returns DNS records to configure."""
    try:
        domain = email_service.add_domain(
            db,
            domain=payload.domain,
            from_name=payload.from_name_default,
            from_email=payload.from_email_default,
        )
        return domain
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/domains", response_model=list[DomainResponse])
def list_domains(db: Session = Depends(get_db)):
    """List all connected domains."""
    return email_service.list_domains(db)


@router.get("/domains/{domain_id}", response_model=DomainResponse)
def get_domain(domain_id: int, db: Session = Depends(get_db)):
    """Get domain details including DNS records and verification status."""
    domain = email_service.get_domain(db, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@router.post("/domains/{domain_id}/verify", response_model=DomainVerifyResponse)
def verify_domain(domain_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Trigger DNS verification for a connected domain."""
    try:
        return email_service.verify_domain(db, domain_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/domains/{domain_id}", status_code=204)
def delete_domain(domain_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Remove a connected domain."""
    if not email_service.delete_domain(db, domain_id):
        raise HTTPException(status_code=404, detail="Domain not found")


# ── Email Endpoints ──

@router.post("/send", response_model=EmailResponse, status_code=201)
def send_email(payload: EmailSend, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Send an email through a verified domain."""
    try:
        return email_service.send_email(
            db,
            domain_id=payload.domain_id,
            from_email=payload.from_email,
            from_name=payload.from_name,
            to=payload.to,
            cc=payload.cc,
            bcc=payload.bcc,
            reply_to=payload.reply_to,
            subject=payload.subject,
            html=payload.html,
            text=payload.text,
            tags=payload.tags,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/batch", response_model=list[EmailResponse], status_code=201)
def send_batch(payload: EmailBatchSend, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Send a batch of up to 100 emails."""
    try:
        email_dicts = [e.model_dump() for e in payload.emails]
        return email_service.send_batch(db, domain_id=payload.domain_id, emails=email_dicts)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails", response_model=EmailListResponse)
def list_emails(
    domain_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List sent emails with optional filtering."""
    emails, total = email_service.list_emails(db, domain_id=domain_id, status=status, page=page, per_page=per_page)
    return EmailListResponse(emails=emails, total=total, page=page, per_page=per_page)


@router.get("/emails/{email_id}", response_model=EmailResponse)
def get_email(email_id: int, db: Session = Depends(get_db)):
    """Get details of a specific sent email."""
    email = email_service.get_email(db, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.get("/stats", response_model=EmailStatsResponse)
def email_stats(db: Session = Depends(get_db)):
    """Get aggregate email sending statistics."""
    return email_service.get_email_stats(db)
