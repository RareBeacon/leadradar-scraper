import asyncio
import random
import time
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger

class BaseScraper:
    def __init__(self, category: str, country: str, state: Optional[str] = None, city: Optional[str] = None, max_results: int = 100):
        self.category = category
        self.country = country
        self.state = state
        self.city = city
        self.max_results = max_results
        
        # Build location string
        loc_parts = [p for p in [city, state, country] if p]
        self.location_str = ", ".join(loc_parts)
        
        # Headers with randomized user agent option
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
    async def fetch_html(self, url: str, retries: int = 3, backoff: float = 2.0) -> Optional[str]:
        """
        Asynchronously fetches HTML with retry logic and exponential backoff.
        Handles Layer 1 & 2 requirements.
        """
        proxies = None
        if settings.PROXY_URL:
            proxies = {"all://": settings.PROXY_URL}
            
        async with httpx.AsyncClient(headers=self.headers, timeout=settings.SCRAPER_TIMEOUT, follow_redirects=True, proxies=proxies) as client:
            for attempt in range(retries):
                try:
                    # Delay to prevent hammering
                    delay = backoff * (2 ** attempt) + random.uniform(0.5, 1.5)
                    logger.debug(f"Fetching URL: {url} (Attempt {attempt+1}/{retries}) - Delaying {delay:.2f}s")
                    await asyncio.sleep(delay)
                    
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        return response.text
                    elif response.status_code in [403, 429]:
                        logger.warning(f"Rate limited or blocked (status {response.status_code}) for URL: {url}")
                        # Could trigger fallback/alternative strategy here (Layer 2)
                    else:
                        logger.warning(f"Non-200 response ({response.status_code}) for URL: {url}")
                except httpx.RequestError as e:
                    logger.error(f"Request error for URL {url}: {str(e)}")
                    
            return None

    def create_fingerprint(self, name: str, phone: Optional[str], website: Optional[str], street: Optional[str], city: Optional[str]) -> str:
        """
        Create a deterministic fingerprint for a business to enable deduplication.
        """
        import hashlib
        
        # Clean and normalize
        norm_name = "".join(e for e in name.lower() if e.isalnum())
        
        norm_phone = ""
        if phone:
            norm_phone = "".join(e for e in phone if e.isdigit())
            # Keep last 10 digits
            norm_phone = norm_phone[-10:]
            
        norm_web = ""
        if website:
            norm_web = website.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
            # Split subdomain/domain if needed, keep main domain
            norm_web = norm_web.split("?")[0]
            
        norm_street = ""
        if street:
            norm_street = "".join(e for e in street.lower() if e.isalnum())
            
        norm_city = ""
        if city:
            norm_city = "".join(e for e in city.lower() if e.isalnum())
            
        # Prioritize combination for fingerprint
        # If phone exists, use phone
        # If website exists, use website (since domains are unique)
        # Else use name + street + city
        if norm_phone and len(norm_phone) >= 10:
            token = f"phone_{norm_phone}"
        elif norm_web and len(norm_web) > 3 and not any(x in norm_web for x in ["yellowpages.com", "yelp.com", "facebook.com", "twitter.com", "instagram.com"]):
            token = f"web_{norm_web}"
        elif norm_street and norm_city:
            token = f"addr_{norm_name}_{norm_street}_{norm_city}"
        else:
            token = f"name_{norm_name}_{norm_city}"
            
        return hashlib.md5(token.encode('utf-8')).hexdigest()

    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Must be implemented by subclasses.
        Returns a list of business records.
        """
        raise NotImplementedError("Scrapers must implement the scrape() method")
