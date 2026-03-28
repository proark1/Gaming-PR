"""
Gaming streamer scraper for Twitch channels, YouTube Gaming channels,
and streamer personal websites.

Scrapes publicly available content: video uploads (via YouTube RSS),
stream announcements, clips, VODs, and social posts. Extracts streamer
activity as articles within the existing ScrapedArticle schema.
"""
import logging
import re
from urllib.parse import urljoin, urlparse

import requests
import feedparser
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper
from app.scrapers.stealth import get_session_headers

logger = logging.getLogger(__name__)

FALLBACK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# YouTube RSS feed template
YOUTUBE_RSS_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


class StreamerScraper(BaseScraper):
    """Scraper for gaming streamer channels (Twitch, YouTube, personal sites)."""

    def scrape(self) -> list[dict]:
        config = self.outlet.scraper_config or {}
        platform = config.get("platform", self._detect_platform())

        if platform == "youtube":
            return self._scrape_youtube()
        elif platform == "twitch":
            return self._scrape_twitch()
        else:
            return self._scrape_generic_site()

    def _detect_platform(self) -> str:
        """Detect platform from outlet URL."""
        url = self.outlet.url.lower()
        if "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        elif "twitch.tv" in url:
            return "twitch"
        return "generic"

    # ═══════════════════════════════════════════
    # YouTube scraping via RSS feeds
    # ═══════════════════════════════════════════

    def _scrape_youtube(self) -> list[dict]:
        """Scrape YouTube channel via RSS feed."""
        config = self.outlet.scraper_config or {}
        feed_url = self.outlet.rss_feed_url

        # Build RSS URL from channel_id if no feed URL provided
        if not feed_url:
            channel_id = config.get("channel_id")
            if channel_id:
                feed_url = YOUTUBE_RSS_TEMPLATE.format(channel_id=channel_id)
            else:
                # Try to discover channel ID from the page
                channel_id = self._discover_youtube_channel_id()
                if channel_id:
                    feed_url = YOUTUBE_RSS_TEMPLATE.format(channel_id=channel_id)

        if not feed_url:
            logger.warning(f"No YouTube feed URL for {self.outlet.name}, falling back to HTML")
            return self._scrape_youtube_html()

        try:
            domain = urlparse(feed_url).netloc
            headers = get_session_headers(domain, language=self.outlet.language)
        except Exception:
            headers = FALLBACK_HEADERS

        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch YouTube RSS for {self.outlet.name}: {e}")
            return self._scrape_youtube_html()

        feed = feedparser.parse(response.text)
        articles = []

        for entry in feed.entries[:50]:
            video_id = entry.get("yt_videoid", "")
            video_url = entry.get("link", "")
            if not video_url and video_id:
                video_url = f"https://www.youtube.com/watch?v={video_id}"

            title = entry.get("title", "")
            if not title or not video_url:
                continue

            # Extract thumbnail
            thumbnail = None
            if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                thumbnail = entry.media_thumbnail[0].get("url")
            elif video_id:
                thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

            # Published date
            published = entry.get("published", entry.get("updated"))

            # Summary/description
            summary = None
            if hasattr(entry, "media_group") and entry.media_group:
                for mg in entry.media_group:
                    if hasattr(mg, "media_description"):
                        summary = mg.media_description[:500]
                        break
            if not summary and entry.get("summary"):
                summary = BeautifulSoup(entry.summary, "html.parser").get_text(strip=True)[:500]

            # Author
            author = entry.get("author", self.outlet.name)

            # Detect article type from title
            article_type = self._classify_video(title)

            # Extract game titles from title
            game_titles = self._extract_game_mentions(title, summary)

            articles.append({
                "title": title,
                "url": video_url,
                "summary": summary,
                "author": author,
                "published_at": published,
                "featured_image_url": thumbnail,
                "thumbnail_url": thumbnail,
                "video_url": video_url,
                "videos": [{"url": video_url, "platform": "youtube", "embed_url": f"https://www.youtube.com/embed/{video_id}"}] if video_id else [],
                "categories": ["gaming", "youtube"],
                "article_type": article_type,
                "tags": self._extract_tags(title),
                "game_titles": game_titles,
            })

        logger.info(f"Scraped {len(articles)} videos from {self.outlet.name} (YouTube RSS)")
        return articles

    def _scrape_youtube_html(self) -> list[dict]:
        """Fallback: scrape YouTube channel page HTML for video links."""
        try:
            domain = urlparse(self.outlet.url).netloc
            headers = get_session_headers(domain, language=self.outlet.language)
        except Exception:
            headers = FALLBACK_HEADERS

        try:
            response = requests.get(self.outlet.url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch YouTube page for {self.outlet.name}: {e}")
            return []

        # YouTube pages are JS-heavy; extract what we can from initial HTML
        articles = []
        # Look for video IDs in the page source
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', response.text)
        seen = set()
        for vid in video_ids[:30]:
            if vid in seen:
                continue
            seen.add(vid)
            articles.append({
                "title": f"Video by {self.outlet.name}",
                "url": f"https://www.youtube.com/watch?v={vid}",
                "video_url": f"https://www.youtube.com/watch?v={vid}",
                "featured_image_url": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "thumbnail_url": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "videos": [{"url": f"https://www.youtube.com/watch?v={vid}", "platform": "youtube", "embed_url": f"https://www.youtube.com/embed/{vid}"}],
                "categories": ["gaming", "youtube"],
                "article_type": "stream",
            })

        logger.info(f"Scraped {len(articles)} videos from {self.outlet.name} (YouTube HTML)")
        return articles

    def _discover_youtube_channel_id(self) -> str | None:
        """Try to discover YouTube channel ID from channel page."""
        try:
            headers = FALLBACK_HEADERS.copy()
            response = requests.get(self.outlet.url, headers=headers, timeout=15)
            response.raise_for_status()
            # Look for channel ID in meta tags or page source
            match = re.search(r'"channelId":"(UC[a-zA-Z0-9_-]{22})"', response.text)
            if match:
                return match.group(1)
            match = re.search(r'channel_id=([a-zA-Z0-9_-]+)', response.text)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    # ═══════════════════════════════════════════
    # Twitch scraping via public pages
    # ═══════════════════════════════════════════

    def _scrape_twitch(self) -> list[dict]:
        """Scrape Twitch channel public pages for clips, VODs, and schedule."""
        config = self.outlet.scraper_config or {}
        channel_name = config.get("channel_name") or self._extract_twitch_channel()

        if not channel_name:
            logger.warning(f"No Twitch channel name for {self.outlet.name}")
            return []

        articles = []

        # Scrape clips page
        clips = self._scrape_twitch_page(
            f"https://www.twitch.tv/{channel_name}/clips",
            channel_name,
            "clip",
        )
        articles.extend(clips)

        # Scrape videos/VODs page
        vods = self._scrape_twitch_page(
            f"https://www.twitch.tv/{channel_name}/videos",
            channel_name,
            "vod",
        )
        articles.extend(vods)

        # Scrape schedule page
        schedule = self._scrape_twitch_schedule(channel_name)
        articles.extend(schedule)

        logger.info(f"Scraped {len(articles)} items from {self.outlet.name} (Twitch)")
        return articles

    def _extract_twitch_channel(self) -> str | None:
        """Extract Twitch channel name from URL."""
        parsed = urlparse(self.outlet.url)
        path = parsed.path.strip("/").split("/")[0] if parsed.path else ""
        return path if path and path not in {"clips", "videos", "schedule"} else None

    def _scrape_twitch_page(self, url: str, channel_name: str, content_type: str) -> list[dict]:
        """Scrape a Twitch page for content links."""
        try:
            headers = FALLBACK_HEADERS.copy()
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.debug(f"Failed to fetch Twitch page {url}: {e}")
            return []

        articles = []

        # Twitch is JS-heavy; extract clip/video IDs from page source
        if content_type == "clip":
            clip_slugs = re.findall(r'"slug":"([a-zA-Z0-9_-]+)"', response.text)
            seen = set()
            for slug in clip_slugs[:20]:
                if slug in seen or len(slug) < 5:
                    continue
                seen.add(slug)
                clip_url = f"https://clips.twitch.tv/{slug}"
                articles.append({
                    "title": f"Clip: {slug} - {self.outlet.name}",
                    "url": clip_url,
                    "video_url": clip_url,
                    "videos": [{"url": clip_url, "platform": "twitch"}],
                    "categories": ["gaming", "twitch", "clip"],
                    "article_type": "clip",
                    "author": channel_name,
                })
        elif content_type == "vod":
            video_ids = re.findall(r'"id":"(\d{8,})"', response.text)
            seen = set()
            for vid in video_ids[:20]:
                if vid in seen:
                    continue
                seen.add(vid)
                vod_url = f"https://www.twitch.tv/videos/{vid}"
                articles.append({
                    "title": f"VOD: {self.outlet.name} - #{vid}",
                    "url": vod_url,
                    "video_url": vod_url,
                    "videos": [{"url": vod_url, "platform": "twitch"}],
                    "categories": ["gaming", "twitch", "vod"],
                    "article_type": "vod",
                    "author": channel_name,
                })

        return articles

    def _scrape_twitch_schedule(self, channel_name: str) -> list[dict]:
        """Scrape Twitch schedule page for upcoming streams."""
        url = f"https://www.twitch.tv/{channel_name}/schedule"
        try:
            headers = FALLBACK_HEADERS.copy()
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException:
            return []

        articles = []

        # Extract schedule data from page (JSON embedded in script tags)
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            # Look for schedule items in structured data
            for script in soup.find_all("script", type="application/ld+json"):
                import json
                try:
                    data = json.loads(script.string or "")
                    if isinstance(data, dict) and data.get("@type") == "Event":
                        articles.append({
                            "title": data.get("name", f"Scheduled Stream - {self.outlet.name}"),
                            "url": url,
                            "summary": data.get("description"),
                            "published_at": data.get("startDate"),
                            "categories": ["gaming", "twitch", "schedule"],
                            "article_type": "stream",
                            "author": channel_name,
                        })
                except (json.JSONDecodeError, TypeError):
                    continue
        except Exception:
            pass

        return articles

    # ═══════════════════════════════════════════
    # Generic site scraping (personal websites)
    # ═══════════════════════════════════════════

    def _scrape_generic_site(self) -> list[dict]:
        """Scrape a streamer's personal website for posts and updates."""
        try:
            domain = urlparse(self.outlet.url).netloc
            headers = get_session_headers(domain, language=self.outlet.language)
        except Exception:
            headers = FALLBACK_HEADERS

        # If RSS feed is available, use it
        if self.outlet.rss_feed_url:
            return self._scrape_rss(headers)

        try:
            response = requests.get(self.outlet.url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {self.outlet.name}: {e}")
            return []

        try:
            soup = BeautifulSoup(response.text, "lxml")
        except Exception:
            soup = BeautifulSoup(response.text, "html.parser")

        articles = []
        seen_urls = set()
        base_domain = urlparse(self.outlet.url).netloc

        for container in soup.select("article, .article, .post, .blog-post, .news-item, .card, .video-item"):
            link = container.find("a", href=True)
            if not link:
                continue

            url = urljoin(self.outlet.url, link["href"])
            parsed = urlparse(url)
            if parsed.netloc and parsed.netloc != base_domain and not parsed.netloc.endswith("." + base_domain):
                continue

            title = None
            heading = container.find(["h1", "h2", "h3", "h4"])
            if heading:
                title = heading.get_text(strip=True)
            if not title:
                title = link.get_text(strip=True)
            if not title or len(title) < 8:
                continue

            if url in seen_urls:
                continue
            seen_urls.add(url)

            img = container.find("img", src=True)
            image_url = None
            if img:
                src = img.get("data-src") or img.get("src", "")
                if src and not src.startswith("data:"):
                    image_url = urljoin(self.outlet.url, src)

            summary = None
            for sel in [".summary", ".excerpt", ".description", "p"]:
                desc = container.select_one(sel)
                if desc and desc != heading:
                    text = desc.get_text(strip=True)
                    if len(text) > 20:
                        summary = text[:500]
                        break

            published_at = None
            time_el = container.find("time", attrs={"datetime": True})
            if time_el:
                published_at = time_el["datetime"]

            articles.append({
                "title": title,
                "url": url,
                "summary": summary,
                "published_at": published_at,
                "featured_image_url": image_url,
                "author": self.outlet.name,
                "categories": ["gaming", "streamer"],
                "article_type": self._classify_video(title),
            })

        logger.info(f"Scraped {len(articles)} posts from {self.outlet.name} (generic site)")
        return articles[:50]

    def _scrape_rss(self, headers: dict) -> list[dict]:
        """Scrape via RSS feed for streamer content."""
        try:
            response = requests.get(self.outlet.rss_feed_url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch RSS for {self.outlet.name}: {e}")
            return []

        feed = feedparser.parse(response.text)
        articles = []

        for entry in feed.entries[:50]:
            title = entry.get("title", "")
            url = entry.get("link", "")
            if not title or not url:
                continue

            summary = None
            if entry.get("summary"):
                summary = BeautifulSoup(entry.summary, "html.parser").get_text(strip=True)[:500]

            thumbnail = None
            if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                thumbnail = entry.media_thumbnail[0].get("url")

            articles.append({
                "title": title,
                "url": url,
                "summary": summary,
                "author": entry.get("author", self.outlet.name),
                "published_at": entry.get("published", entry.get("updated")),
                "featured_image_url": thumbnail,
                "categories": ["gaming", "streamer"],
                "article_type": self._classify_video(title),
                "tags": self._extract_tags(title),
            })

        logger.info(f"Scraped {len(articles)} entries from {self.outlet.name} (RSS)")
        return articles

    # ═══════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════

    def _classify_video(self, title: str) -> str:
        """Classify video/content type from title."""
        title_lower = title.lower()
        if any(w in title_lower for w in ["stream", "live", "streaming", "going live"]):
            return "stream"
        if any(w in title_lower for w in ["vod", "full stream", "past broadcast"]):
            return "vod"
        if any(w in title_lower for w in ["clip", "highlight", "best of", "montage"]):
            return "clip"
        if any(w in title_lower for w in ["review", "análisis"]):
            return "review"
        if any(w in title_lower for w in ["guide", "tutorial", "how to", "tips"]):
            return "guide"
        if any(w in title_lower for w in ["update", "patch", "news"]):
            return "news"
        if any(w in title_lower for w in ["let's play", "gameplay", "playthrough", "walkthrough"]):
            return "feature"
        if any(w in title_lower for w in ["unboxing", "merch", "giveaway"]):
            return "announcement"
        return "stream"

    def _extract_tags(self, title: str) -> list[str]:
        """Extract relevant tags from a title."""
        tags = []
        title_lower = title.lower()

        # Platform tags
        platform_map = {
            "ps5": "PS5", "playstation": "PS5", "ps4": "PS4",
            "xbox": "Xbox", "series x": "Xbox Series X",
            "switch": "Nintendo Switch", "nintendo": "Nintendo Switch",
            "pc": "PC", "steam": "Steam",
            "vr": "VR", "quest": "Meta Quest",
        }
        for keyword, tag in platform_map.items():
            if keyword in title_lower:
                tags.append(tag)

        # Content type tags
        if "ranked" in title_lower:
            tags.append("competitive")
        if "collab" in title_lower or "ft." in title_lower or "with" in title_lower:
            tags.append("collaboration")

        return tags

    def _extract_game_mentions(self, title: str, summary: str | None) -> list[str]:
        """Extract game title mentions from text (basic heuristic)."""
        # This is a simplified approach; the content extractor handles
        # deeper game title extraction during full content phase
        games = []
        text = title + " " + (summary or "")

        # Look for common game title patterns (capitalized multi-word sequences
        # that aren't common English phrases)
        common_words = {
            "the", "a", "an", "is", "are", "was", "were", "new", "best",
            "top", "how", "why", "what", "when", "live", "stream", "video",
            "part", "episode", "season", "day", "night", "game", "games",
            "gaming", "play", "playing", "with", "and", "for", "from",
        }

        # Look for text in quotes or after common patterns
        quoted = re.findall(r'"([^"]+)"', text)
        games.extend(quoted[:5])

        # Look for text after "playing" or "streaming"
        playing_match = re.findall(r'(?:playing|streaming|in)\s+([A-Z][A-Za-z0-9:.\s]{2,30}?)(?:\s*[-|!?]|\s*$)', text)
        for match in playing_match[:3]:
            cleaned = match.strip()
            if cleaned.lower() not in common_words and len(cleaned) > 2:
                games.append(cleaned)

        return list(set(games))[:10]
