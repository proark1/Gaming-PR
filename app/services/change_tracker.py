"""
Content change tracking service.

Detects when articles are updated and records change history.
"""
import hashlib
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.scraped_article import ScrapedArticle
from app.models.webhook import ContentSnapshot

logger = logging.getLogger(__name__)


def track_change(db: Session, article: ScrapedArticle, new_text: str,
                 new_title: str = "", old_hash_override: str = None) -> bool:
    """
    Compare new content against stored content and record changes.

    Args:
        old_hash_override: If provided, use this as the old hash instead of
            article.content_hash. Needed when the article's hash has already
            been updated before calling this function.

    Returns True if content changed.
    """
    if not new_text:
        return False

    new_hash = hashlib.sha256(new_text.encode()).hexdigest()
    old_hash = old_hash_override or article.content_hash

    if not old_hash:
        # First time tracking - record initial snapshot
        snapshot = ContentSnapshot(
            article_id=article.id,
            content_hash=new_hash,
            word_count=len(new_text.split()),
            title=new_title or article.title,
            change_type="initial",
        )
        db.add(snapshot)
        return False

    if new_hash == old_hash:
        return False  # No change

    # Content changed - determine change type
    change_type = _classify_change(article, new_text, new_title)
    old_word_count = article.word_count or 0
    new_word_count = len(new_text.split())

    diff_parts = []
    if new_title and new_title != article.title:
        diff_parts.append(f"Title: '{article.title}' → '{new_title}'")
    word_diff = new_word_count - old_word_count
    if word_diff != 0:
        diff_parts.append(f"Words: {old_word_count} → {new_word_count} ({'+' if word_diff > 0 else ''}{word_diff})")

    snapshot = ContentSnapshot(
        article_id=article.id,
        content_hash=new_hash,
        word_count=new_word_count,
        title=new_title or article.title,
        change_type=change_type,
        diff_summary="; ".join(diff_parts) if diff_parts else "Content updated",
    )
    db.add(snapshot)

    logger.info(f"Content change detected for article {article.id}: {change_type}")
    return True


def _classify_change(article: ScrapedArticle, new_text: str, new_title: str) -> str:
    """Classify the type of content change."""
    # Title change
    if new_title and new_title != article.title:
        return "title_change"

    # Word count change
    old_wc = article.word_count or 0
    new_wc = len(new_text.split())

    if old_wc == 0:
        return "content_update"

    change_ratio = abs(new_wc - old_wc) / max(old_wc, 1)

    if change_ratio > 0.2:
        return "content_update"  # Major change (>20% word count difference)
    else:
        return "minor_edit"  # Small edit


def get_article_history(db: Session, article_id: int) -> list[dict]:
    """Get the change history for an article."""
    snapshots = (
        db.query(ContentSnapshot)
        .filter(ContentSnapshot.article_id == article_id)
        .order_by(ContentSnapshot.snapshot_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "content_hash": s.content_hash,
            "word_count": s.word_count,
            "title": s.title,
            "change_type": s.change_type,
            "diff_summary": s.diff_summary,
            "snapshot_at": s.snapshot_at.isoformat() if s.snapshot_at else None,
        }
        for s in snapshots
    ]
