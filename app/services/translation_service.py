import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        # Create translator once per chunk, not per retry attempt
        translator = GoogleTranslator(source=source, target=target)
        for attempt in range(retries):
            try:
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


def translate_article(db: Session, article_id: int) -> list[ArticleTranslation]:
    """Translate an article into all supported languages (parallel per language)."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise ValueError(f"Article {article_id} not found")

    source_lang = article.source_language
    target_langs = [lang for lang in SUPPORTED_LANGUAGES if lang != source_lang]

    def _translate_in_thread(target_lang: str) -> ArticleTranslation:
        # Each thread uses its own DB session for thread safety
        from app.database import SessionLocal
        thread_db = SessionLocal()
        try:
            thread_article = thread_db.query(Article).filter(Article.id == article_id).first()
            return translate_article_to_language(thread_db, thread_article, target_lang)
        finally:
            thread_db.close()

    translations = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_translate_in_thread, lang): lang for lang in target_langs}
        for future in as_completed(futures):
            try:
                translations.append(future.result())
            except Exception as e:
                lang = futures[future]
                logger.error(f"Translation to {lang} failed for article {article_id}: {e}")

    # Refresh original session's view of the translations
    db.expire_all()
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
