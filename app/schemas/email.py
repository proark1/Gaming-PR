from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ── Domain Schemas ──

class DomainCreate(BaseModel):
    domain: str
    from_name_default: Optional[str] = None
    from_email_default: Optional[str] = None


class DomainResponse(BaseModel):
    id: int
    domain: str
    status: str
    external_domain_id: Optional[str] = None
    dns_records: Optional[list] = None
    from_name_default: Optional[str] = None
    from_email_default: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    verified_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DomainVerifyResponse(BaseModel):
    id: int
    domain: str
    status: str
    dns_records: Optional[list] = None
    verified_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Email Schemas ──

class EmailSend(BaseModel):
    domain_id: int
    from_email: str
    from_name: Optional[str] = None
    to: list[str]
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    reply_to: Optional[str] = None
    subject: str
    html: Optional[str] = None
    text: Optional[str] = None
    tags: Optional[list[str]] = None


class EmailBatchSend(BaseModel):
    domain_id: int
    emails: list[EmailSend]


class EmailResponse(BaseModel):
    id: int
    domain_id: int
    external_email_id: Optional[str] = None
    from_email: str
    from_name: Optional[str] = None
    to_emails: list[str]
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    subject: str
    status: str
    error_message: Optional[str] = None
    opens: int = 0
    clicks: int = 0
    tags: Optional[list[str]] = None
    created_at: datetime
    sent_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EmailListResponse(BaseModel):
    emails: list[EmailResponse]
    total: int
    page: int
    per_page: int


class EmailStatsResponse(BaseModel):
    total_sent: int
    total_delivered: int
    total_bounced: int
    total_failed: int
    total_opens: int
    total_clicks: int
    domains_connected: int
    domains_verified: int
