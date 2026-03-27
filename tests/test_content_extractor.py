from app.scrapers.content_extractor import (
    _parse_date_string,
    _get_best_srcset,
    _detect_video_platform,
    _clean_text,
)


def test_parse_date_iso():
    assert _parse_date_string("2026-03-15T10:30:00Z") is not None


def test_parse_date_human():
    result = _parse_date_string("March 15, 2026")
    assert result is not None
    assert "2026" in result


def test_parse_date_invalid():
    assert _parse_date_string("not a date") is None


def test_parse_date_empty():
    assert _parse_date_string("") is None
    assert _parse_date_string(None) is None


def test_get_best_srcset():
    srcset = "small.jpg 320w, medium.jpg 768w, large.jpg 1200w"
    assert _get_best_srcset(srcset) == "large.jpg"


def test_get_best_srcset_empty():
    assert _get_best_srcset("") is None


def test_clean_text():
    text = "  Hello  \n\n  World  \n\n  "
    result = _clean_text(text)
    assert result == "Hello\nWorld"


def test_video_platforms():
    assert _detect_video_platform("https://www.youtube.com/embed/abc") == "youtube"
    assert _detect_video_platform("https://youtu.be/abc") == "youtube"
    assert _detect_video_platform("https://player.twitch.tv/abc") == "twitch"
    assert _detect_video_platform("https://vimeo.com/123") == "vimeo"
    assert _detect_video_platform("https://www.dailymotion.com/video/x") == "dailymotion"
    assert _detect_video_platform("https://streamable.com/abc") == "streamable"
    assert _detect_video_platform("https://example.com") is None
