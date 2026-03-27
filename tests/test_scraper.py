from unittest.mock import patch, MagicMock
from time import struct_time

from app.models.outlet import GamingOutlet
from app.scrapers.generic_rss import RssScraper
from app.scrapers.content_extractor import _detect_video_platform


def _make_outlet(**kwargs):
    defaults = {
        "id": 1,
        "name": "Test Outlet",
        "url": "https://test.com",
        "rss_feed_url": "https://test.com/feed",
        "language": "en",
        "region": "US",
        "scraper_type": "rss",
        "is_active": True,
    }
    defaults.update(kwargs)
    outlet = MagicMock(spec=GamingOutlet)
    for k, v in defaults.items():
        setattr(outlet, k, v)
    return outlet


def _mock_rss_response(content=b"<rss></rss>"):
    """Create a mock requests.Response for RSS fetch."""
    resp = MagicMock()
    resp.status_code = 200
    resp.content = content
    resp.raise_for_status = MagicMock()
    return resp


def test_rss_scraper_parses_entries():
    outlet = _make_outlet()
    mock_feed = MagicMock()
    entry = MagicMock()
    entry.get = lambda k, d=None: {"title": "Test Title", "link": "https://test.com/article"}.get(k, d)
    entry.published_parsed = struct_time((2026, 1, 15, 12, 0, 0, 0, 1, 0))
    entry.summary = "A test summary"
    entry.updated_parsed = None
    entry.content = []
    entry.media_content = []
    entry.media_thumbnail = []
    entry.enclosures = []
    entry.tags = []
    entry.authors = []
    mock_feed.entries = [entry]

    with patch("app.scrapers.generic_rss.requests.get", return_value=_mock_rss_response()), \
         patch("app.scrapers.generic_rss.feedparser.parse", return_value=mock_feed):
        scraper = RssScraper(outlet)
        results = scraper.scrape()

    assert len(results) == 1
    assert results[0]["title"] == "Test Title"
    assert results[0]["url"] == "https://test.com/article"
    assert results[0]["summary"] == "A test summary"


def test_rss_scraper_no_feed_url():
    outlet = _make_outlet(rss_feed_url=None)
    scraper = RssScraper(outlet)
    results = scraper.scrape()
    assert results == []


def test_rss_scraper_handles_parse_error():
    outlet = _make_outlet()
    with patch("app.scrapers.generic_rss.requests.get", side_effect=Exception("Network error")):
        scraper = RssScraper(outlet)
        results = scraper.scrape()
    assert results == []


def test_rss_extracts_tags_and_categories():
    outlet = _make_outlet()
    mock_feed = MagicMock()
    entry = MagicMock()
    entry.get = lambda k, d=None: {"title": "Tagged Article", "link": "https://test.com/tagged", "author": "John"}.get(k, d)
    entry.published_parsed = None
    entry.updated_parsed = None
    entry.summary = "Summary text"
    entry.content = []
    entry.media_content = []
    entry.media_thumbnail = []
    entry.enclosures = []
    entry.tags = [
        {"term": "PS5", "scheme": ""},
        {"term": "Reviews", "scheme": "category"},
    ]
    entry.authors = [{"name": "Jane Doe", "href": "https://test.com/jane"}]
    mock_feed.entries = [entry]

    with patch("app.scrapers.generic_rss.requests.get", return_value=_mock_rss_response()), \
         patch("app.scrapers.generic_rss.feedparser.parse", return_value=mock_feed):
        results = RssScraper(outlet).scrape()

    assert results[0]["tags"] == ["PS5"]
    assert results[0]["categories"] == ["Reviews"]
    assert results[0]["authors"][0]["name"] == "Jane Doe"


def test_video_platform_detection():
    assert _detect_video_platform("https://www.youtube.com/embed/xyz") == "youtube"
    assert _detect_video_platform("https://player.twitch.tv/abc") == "twitch"
    assert _detect_video_platform("https://player.vimeo.com/123") == "vimeo"
    assert _detect_video_platform("https://example.com/page") is None


def test_content_extractor_extract_full_article():
    """Test the full article extractor with mocked HTTP."""
    from app.scrapers.content_extractor import extract_full_article

    html = """
    <html>
    <head>
        <title>Test Game Review</title>
        <meta name="description" content="A review of Test Game" />
        <meta property="og:title" content="Test Game Review - IGN" />
        <meta property="og:image" content="https://img.com/game.jpg" />
        <meta property="og:type" content="article" />
        <meta name="twitter:card" content="summary_large_image" />
        <script type="application/ld+json">
        {"@type": "Review", "headline": "Test Game Review", "author": {"@type": "Person", "name": "John"}, "reviewRating": {"ratingValue": 8.5, "bestRating": 10}}
        </script>
    </head>
    <body>
        <article>
            <div class="article-body">
                <p>This is a comprehensive review of Test Game. The gameplay is excellent with many features that make it stand out from the competition. It runs great on PS5 and PC.</p>
                <p>The graphics are stunning and the story is compelling. Overall a must-play title for RPG fans.</p>
            </div>
        </article>
    </body>
    </html>
    """

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = html
    mock_response.raise_for_status = MagicMock()

    with patch("app.scrapers.content_extractor.requests.get", return_value=mock_response):
        result = extract_full_article("https://test.com/review")

    assert result["og_title"] == "Test Game Review - IGN"
    assert result["og_image"] == "https://img.com/game.jpg"
    assert result["twitter_card"] == "summary_large_image"
    assert result["author"] == "John"
    assert result["rating_score"] == 8.5
    assert result["rating_max"] == 10
    assert result["is_full_content"] is True
    assert result["word_count"] > 0
    assert result["reading_time_minutes"] >= 1
    assert result["content_hash"] is not None
    assert "PS5" in result["platforms"]
    assert "PC" in result["platforms"]
    assert result["article_type"] == "review"
