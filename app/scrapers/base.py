from abc import ABC, abstractmethod

from app.models.outlet import GamingOutlet


class BaseScraper(ABC):
    def __init__(self, outlet: GamingOutlet):
        self.outlet = outlet

    @abstractmethod
    def scrape(self) -> list[dict]:
        """Return list of dicts with keys: title, url, summary, author, published_at"""
        ...
