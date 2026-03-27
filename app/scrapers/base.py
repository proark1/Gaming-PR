from abc import ABC, abstractmethod

from app.models.outlet import GamingOutlet


class BaseScraper(ABC):
    def __init__(self, outlet: GamingOutlet):
        self.outlet = outlet

    @abstractmethod
    def scrape(self) -> list[dict]:
        """
        Return list of dicts with all available article data.

        Minimum keys: title, url
        Optional keys: summary, author, author_url, authors, published_at,
            updated_at, featured_image_url, thumbnail_url, images, video_url,
            videos, categories, tags, article_type, full_body_html,
            full_body_text, word_count, reading_time_minutes,
            og_title, og_description, og_image, og_type,
            meta_title, meta_description, structured_data,
            comment_count, rating_score, rating_max,
            raw_rss_entry, platforms, game_titles
        """
        ...
