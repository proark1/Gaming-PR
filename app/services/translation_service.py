import logging
import time

from deep_translator import GoogleTranslator
from sqlalchemy.orm import Session

from app.config import SUPPORTED_LANGUAGES
from app.models.article import Article, ArticleTranslation

logger = logging.getLogger(__name__)

MAX_CHUNK_SIZE = 4500


def _split_text(text: str) -> list[str]:
    """Split text into chunks that fit within the translation API limit."""
    if len(text) <= MAX_CHUNK_SIZE:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 > MAX_CHUNK_SIZE:
            if current_chunk:
                chunks.append(current_chunk)
            if len(para) > MAX_CHUNK_SIZE:
                for i in range(0, len(para), MAX_CHUNK_SIZE):
                    chunks.append(para[i:i + MAX_CHUNK_SIZE])
                current_chunk = ""
            else:
                current_chunk = para
        else:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def translate_text(text: str, source: str, target: str, retries: int = 3) -> str:
    """Translate text with chunking and retry logic."""
    if not text or not text.strip():
        return text

    chunks = _split_text(text)
    translated_chunks = []

    for chunk in chunks:
        for attempt in range(retries):
            try:
                translator = GoogleTranslator(source=source, target=target)
                result = translator.translate(chunk)
                translated_chunks.append(result or "")
                break
            except Exception as e:
                logger.warning(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    return "\n\n".join(translated_chunks)


def translate_article(db: Session, article_id: int, retry_only: bool = False) -> list[ArticleTranslation]:
    """Translate an article into all supported languages.

    If retry_only=True, only retranslate failed/pending translations
    and create missing ones — skip already completed translations.
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise ValueError(f"Article {article_id} not found")

    translations = []
    for lang_code in SUPPORTED_LANGUAGES:
        if lang_code == article.source_language:
            continue

        if retry_only:
            existing = (
                db.query(ArticleTranslation)
                .filter(
                    ArticleTranslation.article_id == article.id,
                    ArticleTranslation.language == lang_code,
                )
                .first()
            )
            if existing and existing.status == "completed":
                translations.append(existing)
                continue

        translation = translate_article_to_language(db, article, lang_code)
        translations.append(translation)

    return translations


def translate_article_to_language(
    db: Session, article: Article, target_language: str
) -> ArticleTranslation:
    """Translate a single article to a specific language."""
    existing = (
        db.query(ArticleTranslation)
        .filter(
            ArticleTranslation.article_id == article.id,
            ArticleTranslation.language == target_language,
        )
        .first()
    )

    if existing:
        translation = existing
    else:
        translation = ArticleTranslation(
            article_id=article.id,
            language=target_language,
            status="pending",
        )
        db.add(translation)
        db.flush()

    try:
        translated_title = translate_text(
            article.title, article.source_language, target_language
        )
        translated_body = translate_text(
            article.body, article.source_language, target_language
        )
        translation.translated_title = translated_title
        translation.translated_body = translated_body
        translation.status = "completed"
    except Exception as e:
        logger.error(f"Translation to {target_language} failed for article {article.id}: {e}")
        translation.status = "failed"

    db.commit()
    return translation
