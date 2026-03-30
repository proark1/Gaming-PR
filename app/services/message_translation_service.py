import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from app.models.investor import GamingInvestor
from app.models.message import Message, MessageTranslation
from app.models.outlet import GamingOutlet
from app.models.streamer import Streamer
from app.schemas.message import MessageCreate, MessageUpdate
from app.services.translation_service import translate_text

logger = logging.getLogger(__name__)

# Maps headquarters_region values to language codes
VC_REGION_LANGUAGE_MAP: dict[str, list[str]] = {
    "US": ["en"],
    "CA": ["en", "fr"],
    "GB": ["en"],
    "AU": ["en"],
    "EU": ["de", "fr", "nl", "it", "es", "pl", "sv"],
    "ASIA": ["zh-CN", "zh-HK", "ja", "ko"],
    "CN": ["zh-CN", "zh-HK"],
    "JP": ["ja"],
    "KR": ["ko"],
    "IN": ["hi"],
    "LATAM": ["es", "pt"],
    "BR": ["pt"],
    "ME": ["ar", "he"],
    "MENA": ["ar"],
    "GLOBAL": ["en"],
}

VC_FALLBACK_LANGUAGES = ["en", "zh-CN", "ja", "ko", "de", "fr"]


def get_target_languages(db: Session, message: Message) -> list[str]:
    """Return the set of target languages for a message based on its category."""
    source = message.source_language

    if message.category == "gaming_news":
        rows = (
            db.query(GamingOutlet.language)
            .filter(GamingOutlet.is_active.is_(True), GamingOutlet.language.isnot(None))
            .distinct()
            .all()
        )
        langs = [r[0] for r in rows if r[0] and r[0] != source]

    elif message.category == "gaming_streamer":
        rows = (
            db.query(Streamer.language)
            .filter(Streamer.is_active.is_(True), Streamer.language.isnot(None))
            .distinct()
            .all()
        )
        langs = [r[0] for r in rows if r[0] and r[0] != source]

    elif message.category == "gaming_vc":
        regions = (
            db.query(GamingInvestor.headquarters_region)
            .filter(GamingInvestor.is_active.is_(True), GamingInvestor.headquarters_region.isnot(None))
            .distinct()
            .all()
        )
        lang_set: set[str] = set()
        for (region,) in regions:
            for lang in VC_REGION_LANGUAGE_MAP.get(region, ["en"]):
                lang_set.add(lang)
        langs = [l for l in lang_set if l != source]
        if not langs:
            langs = [l for l in VC_FALLBACK_LANGUAGES if l != source]

    else:
        langs = []

    # Deduplicate while preserving order
    seen: set[str] = set()
    result = []
    for lang in langs:
        if lang not in seen:
            seen.add(lang)
            result.append(lang)
    return result


def translate_message_to_language(
    db: Session, message: Message, target_language: str
) -> MessageTranslation:
    """Translate a single message to a specific language."""
    existing = (
        db.query(MessageTranslation)
        .filter(
            MessageTranslation.message_id == message.id,
            MessageTranslation.language == target_language,
        )
        .first()
    )

    if existing:
        translation = existing
    else:
        translation = MessageTranslation(
            message_id=message.id,
            language=target_language,
            status="pending",
        )
        db.add(translation)
        db.flush()

    try:
        translated_title = translate_text(message.title, message.source_language, target_language)
        translated_body = translate_text(message.body, message.source_language, target_language)
        translation.translated_title = translated_title
        translation.translated_body = translated_body
        translation.status = "completed"
    except Exception as e:
        logger.error(f"Translation to {target_language} failed for message {message.id}: {e}")
        translation.status = "failed"

    db.commit()
    return translation


def translate_message(db: Session, message_id: int, retry_only: bool = False) -> list[MessageTranslation]:
    """Translate a message into category-appropriate languages (parallel per language)."""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise ValueError(f"Message {message_id} not found")

    target_langs = get_target_languages(db, message)

    def _translate_in_thread(target_lang: str) -> MessageTranslation:
        from app.database import SessionLocal
        thread_db = SessionLocal()
        try:
            thread_message = thread_db.query(Message).filter(Message.id == message_id).first()
            return translate_message_to_language(thread_db, thread_message, target_lang)
        finally:
            thread_db.close()

    if retry_only:
        completed_langs = {
            t.language
            for t in db.query(MessageTranslation)
            .filter(
                MessageTranslation.message_id == message_id,
                MessageTranslation.status == "completed",
            )
            .all()
        }
        target_langs = [lang for lang in target_langs if lang not in completed_langs]

    translations = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_translate_in_thread, lang): lang for lang in target_langs}
        for future in as_completed(futures):
            try:
                translations.append(future.result())
            except Exception as e:
                lang = futures[future]
                logger.error(f"Translation to {lang} failed for message {message_id}: {e}")

    db.expire_all()
    return translations


# ─── CRUD helpers ───

def create_message(db: Session, data: MessageCreate) -> Message:
    message = Message(
        title=data.title,
        body=data.body,
        source_language=data.source_language,
        category=data.category,
        author_name=data.author_name,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_message(db: Session, message_id: int) -> Message | None:
    return db.query(Message).filter(Message.id == message_id).first()


def list_messages(db: Session, category: str | None = None, skip: int = 0, limit: int = 20) -> list[Message]:
    q = db.query(Message)
    if category:
        q = q.filter(Message.category == category)
    return q.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()


def update_message(db: Session, message_id: int, data: MessageUpdate) -> Message | None:
    message = get_message(db, message_id)
    if not message:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(message, field, value)
    db.commit()
    db.refresh(message)
    return message


def delete_message(db: Session, message_id: int) -> bool:
    message = get_message(db, message_id)
    if not message:
        return False
    db.delete(message)
    db.commit()
    return True
