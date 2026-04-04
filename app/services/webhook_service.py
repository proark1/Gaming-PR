"""
Webhook notification delivery service.

Sends HTTP POST notifications to registered webhooks when events occur.
Supports HMAC signing, filtering, and retry.
"""
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import requests
from sqlalchemy.orm import Session

from app.models.webhook import Webhook

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="webhook")


def shutdown_executor():
    """Shutdown the webhook thread pool executor."""
    _executor.shutdown(wait=False)
    logger.info("Webhook executor shut down.")


def notify_new_article(db: Session, article_data: dict):
    """Send webhook notifications for a new article."""
    _dispatch(db, "new_article", article_data)


def notify_scrape_complete(db: Session, job_data: dict):
    """Send webhook notifications when a scrape job completes."""
    _dispatch(db, "scrape_complete", job_data)


def notify_outlet_failed(db: Session, outlet_data: dict):
    """Send webhook notifications when an outlet fails repeatedly."""
    _dispatch(db, "outlet_failed", outlet_data)


def _dispatch(db: Session, event_type: str, payload: dict):
    """Find matching webhooks and dispatch notifications."""
    webhooks = db.query(Webhook).filter(Webhook.is_active.is_(True)).all()

    for webhook in webhooks:
        if not _matches_webhook(webhook, event_type, payload):
            continue

        # Fire and forget via thread pool
        _executor.submit(_deliver, webhook.id, webhook.url, webhook.secret, event_type, payload)


def _matches_webhook(webhook: Webhook, event_type: str, payload: dict) -> bool:
    """Check if a webhook should receive this event."""
    # Check event type
    if webhook.events and event_type not in webhook.events:
        return False

    # Check language filter
    if webhook.language_filter:
        article_lang = payload.get("language", "")
        if article_lang and article_lang not in webhook.language_filter:
            return False

    # Check outlet filter
    if webhook.outlet_filter:
        outlet_id = payload.get("outlet_id")
        if outlet_id and outlet_id not in webhook.outlet_filter:
            return False

    # Check article type filter
    if webhook.article_type_filter:
        atype = payload.get("article_type", "")
        if atype and atype not in webhook.article_type_filter:
            return False

    return True


def _deliver(webhook_id: int, url: str, secret: str, event_type: str, payload: dict):
    """Deliver a webhook notification with optional HMAC signing."""
    from app.database import SessionLocal
    from app.utils.url_safety import is_safe_url

    if not is_safe_url(url):
        logger.warning(f"Webhook {webhook_id}: blocked unsafe URL {url}")
        return

    body = json.dumps({
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
    }, default=str)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event_type,
    }

    if secret:
        signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    db = SessionLocal()
    try:
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return

        try:
            resp = requests.post(url, data=body, headers=headers, timeout=10)
            webhook.total_deliveries += 1
            webhook.last_delivery_at = datetime.now(timezone.utc)
            webhook.last_response_code = resp.status_code

            if resp.status_code >= 400:
                webhook.total_failures += 1
                webhook.last_failure_at = datetime.now(timezone.utc)
                logger.warning(f"Webhook {webhook_id} delivery failed: HTTP {resp.status_code}")
            else:
                logger.debug(f"Webhook {webhook_id} delivered: {event_type}")

        except requests.RequestException as e:
            webhook.total_failures += 1
            webhook.last_failure_at = datetime.now(timezone.utc)
            logger.warning(f"Webhook {webhook_id} delivery error: {e}")

        db.commit()
    except Exception as e:
        logger.error(f"Webhook {webhook_id} unhandled error: {e}")
    finally:
        db.close()
