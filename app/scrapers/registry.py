from typing import Dict, Type, Optional
from app.scrapers.base import BaseScraper
from app.scrapers.yellowpages import YellowPagesScraper
from app.scrapers.yelp import YelpScraper
from app.scrapers.ycombinator import YCombinatorScraper

SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {
    "yellowpages": YellowPagesScraper,
    "yelp": YelpScraper,
    "ycombinator": YCombinatorScraper
}

def get_scraper(source: str, category: str, country: str, state: Optional[str] = None, city: Optional[str] = None, max_results: int = 100, yc_view: Optional[str] = None) -> Optional[BaseScraper]:
    """
    Returns an instantiated scraper adapter for the given source name.
    """
    scraper_cls = SCRAPER_REGISTRY.get(source.lower().strip())
    if scraper_cls:
        if scraper_cls == YCombinatorScraper:
            return scraper_cls(
                category=category,
                country=country,
                state=state,
                city=city,
                max_results=max_results,
                yc_view=yc_view
            )
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
