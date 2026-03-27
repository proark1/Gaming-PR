"""Bulk export API - CSV, JSON, and RSS feed generation."""
import csv
import io
import json
from datetime import datetime, timezone
from typing import Optional
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.scraped_article import ScrapedArticle

router = APIRouter(prefix="/api/export", tags=["export"])


def _build_query(db: Session, language: str = None, outlet_id: int = None,
                 article_type: str = None, days: int = None, limit: int = 1000):
    """Build a filtered query for exports."""
    query = db.query(ScrapedArticle)
    if language:
        query = query.filter(ScrapedArticle.language == language)
    if outlet_id:
        query = query.filter(ScrapedArticle.outlet_id == outlet_id)
    if article_type:
        query = query.filter(ScrapedArticle.article_type == article_type)
    if days:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(ScrapedArticle.scraped_at >= cutoff)
    return query.order_by(ScrapedArticle.scraped_at.desc()).limit(limit)


@router.get("/json")
def export_json(
    language: Optional[str] = None,
    outlet_id: Optional[int] = None,
    article_type: Optional[str] = None,
    days: Optional[int] = None,
    limit: int = Query(default=500, le=5000),
    include_body: bool = False,
    db: Session = Depends(get_db),
):
    """Export articles as JSON."""
    articles = _build_query(db, language, outlet_id, article_type, days, limit).all()

    data = []
    for a in articles:
        item = {
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "author": a.author,
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "language": a.language,
            "article_type": a.article_type,
            "summary": a.summary,
            "word_count": a.word_count,
            "tags": a.tags,
            "categories": a.categories,
            "platforms": a.platforms,
            "game_titles": a.game_titles,
            "featured_image_url": a.featured_image_url,
            "outlet_id": a.outlet_id,
            "scraped_at": a.scraped_at.isoformat() if a.scraped_at else None,
        }
        if include_body:
            item["full_body_text"] = a.full_body_text
        data.append(item)

    return Response(
        content=json.dumps({"articles": data, "count": len(data)}, default=str, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=gaming_articles.json"},
    )


@router.get("/csv")
def export_csv(
    language: Optional[str] = None,
    outlet_id: Optional[int] = None,
    article_type: Optional[str] = None,
    days: Optional[int] = None,
    limit: int = Query(default=500, le=5000),
    db: Session = Depends(get_db),
):
    """Export articles as CSV."""
    articles = _build_query(db, language, outlet_id, article_type, days, limit).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "id", "title", "url", "author", "published_at", "language",
        "article_type", "word_count", "tags", "platforms", "game_titles",
        "featured_image_url", "outlet_id", "scraped_at",
    ])

    for a in articles:
        writer.writerow([
            a.id, a.title, a.url, a.author or "",
            a.published_at.isoformat() if a.published_at else "",
            a.language, a.article_type or "", a.word_count or "",
            "|".join(a.tags or []), "|".join(a.platforms or []),
            "|".join(a.game_titles or []),
            a.featured_image_url or "", a.outlet_id,
            a.scraped_at.isoformat() if a.scraped_at else "",
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=gaming_articles.csv"},
    )


@router.get("/rss")
def export_rss(
    language: Optional[str] = None,
    outlet_id: Optional[int] = None,
    article_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """Generate an RSS 2.0 feed of scraped articles."""
    articles = _build_query(db, language, outlet_id, article_type, days=7, limit=limit).all()

    rss = Element("rss", version="2.0")
    rss.set("xmlns:media", "http://search.yahoo.com/mrss/")
    rss.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")

    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "Gaming PR - Aggregated Gaming News"
    SubElement(channel, "description").text = "Latest gaming news from 80+ outlets in 10 languages"
    SubElement(channel, "language").text = language or "en"
    SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    for a in articles:
        item = SubElement(channel, "item")
        SubElement(item, "title").text = a.title or "Untitled"
        SubElement(item, "link").text = a.url
        SubElement(item, "guid", isPermaLink="true").text = a.url

        if a.summary:
            SubElement(item, "description").text = a.summary[:500]
        if a.author:
            SubElement(item, "dc:creator").text = a.author
        if a.published_at:
            try:
                SubElement(item, "pubDate").text = a.published_at.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
            except Exception:
                pass
        if a.featured_image_url:
            SubElement(item, "media:content", url=a.featured_image_url, medium="image")
        if a.categories:
            for cat in (a.categories or [])[:5]:
                SubElement(item, "category").text = cat
        if a.tags:
            for tag in (a.tags or [])[:10]:
                SubElement(item, "category").text = tag

    xml_bytes = tostring(rss, encoding="unicode", xml_declaration=False)
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes

    return Response(
        content=xml_str,
        media_type="application/rss+xml",
        headers={"Content-Disposition": "inline; filename=gaming_news.xml"},
    )
