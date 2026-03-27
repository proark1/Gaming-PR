import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.email import ConnectedDomain, SentEmail

logger = logging.getLogger(__name__)

# ─── Helpers ───

def _api_url(path: str) -> str:
    """Build the full email service API URL."""
    base = settings.EMAIL_SERVICE_URL.rstrip("/")
    return f"{base}{path}"


def _headers() -> dict:
    """Auth headers for the email service."""
    return {
        "Authorization": f"Bearer {settings.EMAIL_SERVICE_API_KEY}",
        "Content-Type": "application/json",
    }


# ─── Domain Operations ───

def add_domain(db: Session, domain: str, from_name: Optional[str] = None, from_email: Optional[str] = None) -> ConnectedDomain:
    """Register a domain with the external email service and store locally."""
    # Call the email service to add the domain
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            _api_url("/v1/domains"),
            headers=_headers(),
            json={"domain": domain},
        )
        resp.raise_for_status()
        data = resp.json()

    db_domain = ConnectedDomain(
        domain=domain,
        status=data.get("status", "pending"),
        external_domain_id=str(data.get("id", "")),
        dns_records=data.get("dnsRecords", data.get("dns_records", [])),
        from_name_default=from_name,
        from_email_default=from_email,
    )
    db.add(db_domain)
    db.commit()
    db.refresh(db_domain)
    logger.info(f"Domain added: {domain} (external_id={db_domain.external_domain_id})")
    return db_domain


def verify_domain(db: Session, domain_id: int) -> ConnectedDomain:
    """Trigger domain verification via the email service."""
    db_domain = db.query(ConnectedDomain).filter(ConnectedDomain.id == domain_id).first()
    if not db_domain:
        raise ValueError(f"Domain with id {domain_id} not found")

    db_domain.status = "verifying"
    db.commit()

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            _api_url(f"/v1/domains/{db_domain.external_domain_id}/verify"),
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    db_domain.status = data.get("status", "pending")
    db_domain.dns_records = data.get("dnsRecords", data.get("dns_records", db_domain.dns_records))
    if db_domain.status == "verified":
        db_domain.verified_at = datetime.now(timezone.utc)
    db_domain.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_domain)
    logger.info(f"Domain verification triggered: {db_domain.domain} -> {db_domain.status}")
    return db_domain


def list_domains(db: Session) -> list[ConnectedDomain]:
    """List all connected domains."""
    return db.query(ConnectedDomain).order_by(ConnectedDomain.created_at.desc()).all()


def get_domain(db: Session, domain_id: int) -> Optional[ConnectedDomain]:
    """Get a single domain by ID."""
    return db.query(ConnectedDomain).filter(ConnectedDomain.id == domain_id).first()


def delete_domain(db: Session, domain_id: int) -> bool:
    """Remove a domain from the platform and the email service."""
    db_domain = db.query(ConnectedDomain).filter(ConnectedDomain.id == domain_id).first()
    if not db_domain:
        return False

    # Remove from email service
    if db_domain.external_domain_id:
        try:
            with httpx.Client(timeout=30) as client:
                client.delete(
                    _api_url(f"/v1/domains/{db_domain.external_domain_id}"),
                    headers=_headers(),
                )
        except Exception as e:
            logger.warning(f"Failed to delete domain from email service: {e}")

    db.delete(db_domain)
    db.commit()
    logger.info(f"Domain deleted: {db_domain.domain}")
    return True


# ─── Email Operations ───

def send_email(
    db: Session,
    domain_id: int,
    from_email: str,
    to: list[str],
    subject: str,
    html: Optional[str] = None,
    text: Optional[str] = None,
    from_name: Optional[str] = None,
    cc: Optional[list[str]] = None,
    bcc: Optional[list[str]] = None,
    reply_to: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> SentEmail:
    """Send an email via the external email service."""
    db_domain = db.query(ConnectedDomain).filter(ConnectedDomain.id == domain_id).first()
    if not db_domain:
        raise ValueError(f"Domain with id {domain_id} not found")
    if db_domain.status != "verified":
        raise ValueError(f"Domain {db_domain.domain} is not verified (status: {db_domain.status})")

    # Build the payload for the email service
    payload = {
        "from": f"{from_name} <{from_email}>" if from_name else from_email,
        "to": to,
        "subject": subject,
    }
    if html:
        payload["html"] = html
    if text:
        payload["text"] = text
    if cc:
        payload["cc"] = cc
    if bcc:
        payload["bcc"] = bcc
    if reply_to:
        payload["reply_to"] = reply_to
    if tags:
        payload["tags"] = tags

    # Create local record
    db_email = SentEmail(
        domain_id=domain_id,
        from_email=from_email,
        from_name=from_name,
        to_emails=to,
        cc=cc or [],
        bcc=bcc or [],
        reply_to=reply_to,
        subject=subject,
        html_body=html,
        text_body=text,
        status="queued",
        tags=tags or [],
    )
    db.add(db_email)
    db.commit()

    # Send via email service
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                _api_url("/v1/emails"),
                headers=_headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        db_email.external_email_id = str(data.get("id", ""))
        db_email.status = "sent"
        db_email.sent_at = datetime.now(timezone.utc)
    except Exception as e:
        db_email.status = "failed"
        db_email.error_message = str(e)
        logger.error(f"Failed to send email: {e}")

    db.commit()
    db.refresh(db_email)
    return db_email


def send_batch(
    db: Session,
    domain_id: int,
    emails: list[dict],
) -> list[SentEmail]:
    """Send a batch of emails (up to 100) via the email service."""
    db_domain = db.query(ConnectedDomain).filter(ConnectedDomain.id == domain_id).first()
    if not db_domain:
        raise ValueError(f"Domain with id {domain_id} not found")
    if db_domain.status != "verified":
        raise ValueError(f"Domain {db_domain.domain} is not verified")

    results = []
    # Build payloads for email service batch API
    batch_payload = []
    db_emails = []

    for email_data in emails[:100]:
        from_name = email_data.get("from_name")
        from_email = email_data["from_email"]
        payload = {
            "from": f"{from_name} <{from_email}>" if from_name else from_email,
            "to": email_data["to"],
            "subject": email_data["subject"],
        }
        if email_data.get("html"):
            payload["html"] = email_data["html"]
        if email_data.get("text"):
            payload["text"] = email_data["text"]
        batch_payload.append(payload)

        db_email = SentEmail(
            domain_id=domain_id,
            from_email=from_email,
            from_name=from_name,
            to_emails=email_data["to"],
            cc=email_data.get("cc", []),
            bcc=email_data.get("bcc", []),
            subject=email_data["subject"],
            html_body=email_data.get("html"),
            text_body=email_data.get("text"),
            status="queued",
            tags=email_data.get("tags", []),
        )
        db.add(db_email)
        db_emails.append(db_email)

    db.commit()

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                _api_url("/v1/emails/batch"),
                headers=_headers(),
                json=batch_payload,
            )
            resp.raise_for_status()
            data = resp.json()

        sent_ids = data.get("ids", [])
        for i, db_email in enumerate(db_emails):
            db_email.status = "sent"
            db_email.sent_at = datetime.now(timezone.utc)
            if i < len(sent_ids):
                db_email.external_email_id = str(sent_ids[i])
    except Exception as e:
        for db_email in db_emails:
            db_email.status = "failed"
            db_email.error_message = str(e)
        logger.error(f"Batch send failed: {e}")

    db.commit()
    for db_email in db_emails:
        db.refresh(db_email)
    return db_emails


def list_emails(
    db: Session,
    domain_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[SentEmail], int]:
    """List sent emails with optional filters."""
    query = db.query(SentEmail)
    if domain_id:
        query = query.filter(SentEmail.domain_id == domain_id)
    if status:
        query = query.filter(SentEmail.status == status)

    total = query.count()
    emails = (
        query.order_by(SentEmail.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return emails, total


def get_email(db: Session, email_id: int) -> Optional[SentEmail]:
    """Get a single email by ID."""
    return db.query(SentEmail).filter(SentEmail.id == email_id).first()


def get_email_stats(db: Session) -> dict:
    """Get aggregate email statistics."""
    total_sent = db.query(SentEmail).filter(SentEmail.status == "sent").count()
    total_delivered = db.query(SentEmail).filter(SentEmail.status == "delivered").count()
    total_bounced = db.query(SentEmail).filter(SentEmail.status == "bounced").count()
    total_failed = db.query(SentEmail).filter(SentEmail.status == "failed").count()
    total_opens = db.query(func.sum(SentEmail.opens)).scalar() or 0
    total_clicks = db.query(func.sum(SentEmail.clicks)).scalar() or 0
    domains_connected = db.query(ConnectedDomain).count()
    domains_verified = db.query(ConnectedDomain).filter(ConnectedDomain.status == "verified").count()

    return {
        "total_sent": total_sent,
        "total_delivered": total_delivered,
        "total_bounced": total_bounced,
        "total_failed": total_failed,
        "total_opens": total_opens,
        "total_clicks": total_clicks,
        "domains_connected": domains_connected,
        "domains_verified": domains_verified,
    }
