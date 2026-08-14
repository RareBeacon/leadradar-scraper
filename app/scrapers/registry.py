from typing import Dict, Type, Optional
from app.scrapers.base import BaseScraper
from app.scrapers.yellowpages import YellowPagesScraper
from app.scrapers.yelp import YelpScraper

SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {
    "yellowpages": YellowPagesScraper,
    "yelp": YelpScraper
}

def get_scraper(source: str, category: str, country: str, state: Optional[str] = None, city: Optional[str] = None, max_results: int = 100) -> Optional[BaseScraper]:
    """
    Returns an instantiated scraper adapter for the given source name.
    """
    scraper_cls = SCRAPER_REGISTRY.get(source.lower().strip())
    if scraper_cls:
        return scraper_cls(
            category=category,
            country=country,
            state=state,
            city=city,
            max_results=max_results
        )
    return None

def register_scraper(source_name: str, scraper_cls: Type[BaseScraper]):
    """
    Utility to register future custom directories or scraper adapters dynamically.
    """
    SCRAPER_REGISTRY[source_name.lower().strip()] = scraper_cls
