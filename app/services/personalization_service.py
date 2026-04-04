"""
Individualized outreach personalization using Claude AI + Google Translate.

Flow:
  Base Message → Claude personalizes for specific contact → Google Translate to contact's language
  → MessagePersonalization record saved
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.investor import GamingInvestor
from app.models.message import Message
from app.models.outlet import GamingOutlet
from app.models.personalization import MessagePersonalization
from app.models.streamer import Streamer
from app.services.profile_service import (
    compile_investor_profile,
    compile_outlet_profile,
    compile_streamer_profile,
)
from app.services.translation_service import translate_text

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# Contact-type → focus field label used in the Claude prompt
FOCUS_FIELD_LABELS = {
    "outlet": "editorial focus and topics covered",
    "streamer": "game focus and content style",
    "vc": "investment thesis and portfolio focus",
}


def _build_prompt(
    base_title: str,
    base_body: str,
    source_language: str,
    contact_name: str,
    contact_type: str,
    contact_profile: str,
) -> str:
    focus_field = FOCUS_FIELD_LABELS.get(contact_type, "specific interests")
    return f"""You are helping a game developer write personalized outreach to a {contact_type}.

Base message (in {source_language}):
Title: {base_title}
Body: {base_body}

Contact: {contact_name}
Profile: {contact_profile}

Rewrite the message personalized for {contact_name}. Reference their specific {focus_field}.
Keep the core pitch. Stay in {source_language}. Be concise.

Respond ONLY in this exact format (no extra text):
TITLE: <personalized title>
BODY: <personalized body>"""


def personalize_with_claude(
    base_title: str,
    base_body: str,
    source_language: str,
    contact_name: str,
    contact_type: str,
    contact_profile: str,
) -> tuple[str, str]:
    """Call Claude API to adapt base message for a specific contact.
    Returns (personalized_title, personalized_body) in source_language."""
    try:
        import anthropic  # lazy import — not installed in all envs

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = _build_prompt(
            base_title, base_body, source_language, contact_name, contact_type, contact_profile
        )

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()

        # Parse TITLE: ... BODY: ... format
        title = base_title
        body = base_body

        lines = raw.split("\n")
        body_lines = []
        in_body = False
        for line in lines:
            if line.startswith("TITLE:") and not in_body:
                title = line[len("TITLE:"):].strip()
            elif line.startswith("BODY:"):
                in_body = True
                body_lines.append(line[len("BODY:"):].strip())
            elif in_body:
                body_lines.append(line)

        if body_lines:
            body = "\n".join(body_lines).strip()

        return title, body

    except Exception as e:
        logger.error(f"Claude personalization failed for {contact_name}: {e}")
        return base_title, base_body


def personalize_and_translate(
    db: Session, personalization: MessagePersonalization, message: Message
) -> None:
    """Run full pipeline: Claude personalization → Google Translate → save."""
    try:
        personalized_title, personalized_body = personalize_with_claude(
            base_title=message.title,
            base_body=message.body,
            source_language=message.source_language,
            contact_name=personalization.target_name,
            contact_type=personalization.target_type,
            contact_profile=_get_contact_profile(db, personalization),
        )

        # Translate to contact's language if different from source
        target_lang = personalization.target_language
        source_lang = message.source_language

        if target_lang and target_lang != source_lang:
            try:
                personalized_title = translate_text(personalized_title, source_lang, target_lang)
                personalized_body = translate_text(personalized_body, source_lang, target_lang)
            except Exception as e:
                logger.warning(
                    f"Translation to {target_lang} failed for {personalization.target_name}: {e}"
                    " — keeping personalized text in source language"
                )

        personalization.personalized_title = personalized_title
        personalization.personalized_body = personalized_body
        personalization.status = "completed"
        personalization.error_message = None

    except Exception as e:
        logger.error(f"Personalization failed for {personalization.target_name}: {e}")
        personalization.status = "failed"
        personalization.error_message = str(e)

    db.add(personalization)
    db.commit()


def _get_contact_profile(db: Session, personalization: MessagePersonalization) -> str:
    """Return stored outreach_profile string or compile it on the fly."""
    target_type = personalization.target_type
    target_id = personalization.target_id

    if target_type == "outlet":
        entity = db.query(GamingOutlet).filter(GamingOutlet.id == target_id).first()
        if entity:
            return entity.outreach_profile or compile_outlet_profile(entity)
    elif target_type == "streamer":
        entity = db.query(Streamer).filter(Streamer.id == target_id).first()
        if entity:
            return entity.outreach_profile or compile_streamer_profile(entity)
    elif target_type == "vc":
        entity = db.query(GamingInvestor).filter(GamingInvestor.id == target_id).first()
        if entity:
            return entity.outreach_profile or compile_investor_profile(entity)

    return "{}"


def get_contacts_for_message(db: Session, message: Message) -> list[dict]:
    """Return list of {id, name, language, target_type} for all active contacts in category."""
    contacts = []

    if message.category == "gaming_news":
        outlets = (
            db.query(GamingOutlet)
            .filter(GamingOutlet.is_active.is_(True))
            .all()
        )
        for o in outlets:
            contacts.append({
                "id": o.id,
                "name": o.name,
                "language": o.language or message.source_language,
                "target_type": "outlet",
            })

    elif message.category == "gaming_streamer":
        streamers = (
            db.query(Streamer)
            .filter(Streamer.is_active.is_(True))
            .all()
        )
        for s in streamers:
            contacts.append({
                "id": s.id,
                "name": s.name,
                "language": s.language or message.source_language,
                "target_type": "streamer",
            })

    elif message.category == "gaming_vc":
        from app.services.message_translation_service import VC_REGION_LANGUAGE_MAP
        investors = (
            db.query(GamingInvestor)
            .filter(GamingInvestor.is_active.is_(True))
            .all()
        )
        for inv in investors:
            region = inv.headquarters_region or "GLOBAL"
            langs = VC_REGION_LANGUAGE_MAP.get(region, ["en"])
            lang = langs[0] if langs else "en"
            contacts.append({
                "id": inv.id,
                "name": inv.name,
                "language": lang,
                "target_type": "vc",
            })

    return contacts


def generate_personalizations(
    db: Session, message_id: int, target_ids: Optional[list[int]] = None
) -> list[MessagePersonalization]:
    """Create/update MessagePersonalization records and process them in parallel."""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise ValueError(f"Message {message_id} not found")

    all_contacts = get_contacts_for_message(db, message)

    if target_ids is not None:
        all_contacts = [c for c in all_contacts if c["id"] in target_ids]

    # Upsert personalization records
    records: list[MessagePersonalization] = []
    for contact in all_contacts:
        existing = (
            db.query(MessagePersonalization)
            .filter(
                MessagePersonalization.message_id == message_id,
                MessagePersonalization.target_type == contact["target_type"],
                MessagePersonalization.target_id == contact["id"],
            )
            .first()
        )
        if existing:
            existing.status = "pending"
            existing.error_message = None
            db.add(existing)
            records.append(existing)
        else:
            p = MessagePersonalization(
                message_id=message_id,
                target_type=contact["target_type"],
                target_id=contact["id"],
                target_name=contact["name"],
                target_language=contact["language"],
                status="pending",
            )
            db.add(p)
            records.append(p)

    db.commit()
    for r in records:
        db.refresh(r)

    # Process in parallel
    def _process(personalization_id: int) -> None:
        from app.database import SessionLocal
        thread_db = SessionLocal()
        try:
            p = thread_db.query(MessagePersonalization).filter(MessagePersonalization.id == personalization_id).first()
            msg = thread_db.query(Message).filter(Message.id == message_id).first()
            if p and msg:
                personalize_and_translate(thread_db, p, msg)
        finally:
            thread_db.close()

    record_ids = [r.id for r in records]
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(_process, pid): pid for pid in record_ids}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Personalization worker error: {e}")

    db.expire_all()
    return (
        db.query(MessagePersonalization)
        .filter(MessagePersonalization.message_id == message_id)
        .all()
    )


def retry_failed_personalizations(
    db: Session, message_id: int
) -> list[MessagePersonalization]:
    """Re-run only failed/pending personalizations."""
    failed = (
        db.query(MessagePersonalization)
        .filter(
            MessagePersonalization.message_id == message_id,
            MessagePersonalization.status.in_(["failed", "pending"]),
        )
        .all()
    )
    target_ids = [p.target_id for p in failed]
    if not target_ids:
        return []
    return generate_personalizations(db, message_id, target_ids=target_ids)
