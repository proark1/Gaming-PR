from unittest.mock import patch, MagicMock
from time import struct_time

from app.models.outlet import GamingOutlet
from app.scrapers.generic_rss import RssScraper


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


def test_rss_scraper_parses_entries():
    outlet = _make_outlet()
    mock_feed = MagicMock()
    entry = MagicMock()
    entry.get = lambda k, d=None: {"title": "Test Title", "link": "https://test.com/article"}.get(k, d)
    entry.published_parsed = struct_time((2026, 1, 15, 12, 0, 0, 0, 1, 0))
    entry.summary = "A test summary"
    mock_feed.entries = [entry]

    with patch("app.scrapers.generic_rss.feedparser.parse", return_value=mock_feed):
        scraper = RssScraper(outlet)
        results = scraper.scrape()

    assert len(results) == 1
    assert results[0]["title"] == "Test Title"
    assert results[0]["url"] == "https://test.com/article"


def test_rss_scraper_no_feed_url():
    outlet = _make_outlet(rss_feed_url=None)
    scraper = RssScraper(outlet)
    results = scraper.scrape()
    assert results == []


def test_rss_scraper_handles_parse_error():
    outlet = _make_outlet()
    with patch("app.scrapers.generic_rss.feedparser.parse", side_effect=Exception("Network error")):
        scraper = RssScraper(outlet)
        results = scraper.scrape()
    assert results == []
