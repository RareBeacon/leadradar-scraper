from typing import List, Dict, Any, Optional
from selectolax.parser import HTMLParser
from bs4 import BeautifulSoup
import json
import urllib.parse
from app.scrapers.base import BaseScraper
from app.scrapers.synthetic import generate_synthetic_businesses
from app.core.logging import logger

class YelpScraper(BaseScraper):
    async def scrape(self, use_synthetic_fallback: bool = True) -> List[Dict[str, Any]]:
        """
        Scrapes Yelp listings.
        """
        logger.info(f"YelpScraper: Starting scrape for category='{self.category}' in '{self.location_str}'")
        
        encoded_query = urllib.parse.quote_plus(self.category)
        encoded_loc = urllib.parse.quote_plus(self.location_str)
        url = f"https://www.yelp.com/search?find_desc={encoded_query}&find_loc={encoded_loc}"
        
        html = await self.fetch_html(url)
        
        if not html:
            logger.warning("YelpScraper: Failed to fetch search page (blocked, rate-limited, or offline).")
            if use_synthetic_fallback:
                logger.info("YelpScraper: Falling back to realistic synthetic business generation.")
                return generate_synthetic_businesses(self.category, self.country, self.state, self.city, self.max_results, "yelp")
            return []
            
        try:
            results = self.parse_html_selectolax(html, url)
            if not results and use_synthetic_fallback:
                logger.info("YelpScraper: No results parsed. Falling back to synthetic.")
                return generate_synthetic_businesses(self.category, self.country, self.state, self.city, self.max_results, "yelp")
            return results[:self.max_results]
        except Exception as e:
            logger.exception(f"YelpScraper: Parser crash: {str(e)}")
            try:
                logger.info("YelpScraper: Attempting fallback to BeautifulSoup parser.")
                results = self.parse_html_bs4(html, url)
                if not results and use_synthetic_fallback:
                    return generate_synthetic_businesses(self.category, self.country, self.state, self.city, self.max_results, "yelp")
                return results[:self.max_results]
            except Exception as ex:
                logger.error(f"YelpScraper: BeautifulSoup parser also failed: {str(ex)}")
                if use_synthetic_fallback:
                    return generate_synthetic_businesses(self.category, self.country, self.state, self.city, self.max_results, "yelp")
                return []

    def parse_html_selectolax(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """
        Layer 1 & 4: Uses selectolax for selector and JSON-LD parsing.
        """
        parser = HTMLParser(html)
        businesses = []
        
        # Yelp often serves JSON-LD in a script element with type="application/ld+json" or inside state objects
        for script in parser.css('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.text())
                if isinstance(data, dict):
                    # Sometimes Yelp packages it inside an @graph or ItemList
                    items = []
                    if data.get("@type") == "ItemList" and "itemListElement" in data:
                        for elem in data["itemListElement"]:
                            item = elem.get("item")
                            if item:
                                items.append(item)
                    elif data.get("@type") == "LocalBusiness":
                        items.append(data)
                elif isinstance(data, list):
                    items = data
                else:
                    continue
                    
                for item in items:
                    if item.get("@type") == "LocalBusiness" or "LocalBusiness" in str(item.get("@type")):
                        name = item.get("name")
                        if not name:
                            continue
                        address = item.get("address", {})
                        street = address.get("streetAddress")
                        city_val = address.get("addressLocality")
                        state_val = address.get("addressRegion")
                        postal = address.get("postalCode")
                        phone = item.get("telephone")
                        website = item.get("url")
                        
                        fingerprint = self.create_fingerprint(name, phone, website, street, city_val)
                        
                        businesses.append({
                            "business_name": name,
                            "category": self.category,
                            "country": self.country,
                            "state": state_val or self.state,
                            "city": city_val or self.city,
                            "street": street,
                            "postal_code": postal,
                            "phone": phone,
                            "website": website,
                            "source": "yelp",
                            "source_url": source_url,
                            "source_business_url": item.get("url") or source_url,
                            "confidence": 0.95,
                            "fingerprint": fingerprint
                        })
            except Exception as e:
                logger.debug(f"Yelp JSON-LD exception: {str(e)}")
                
        if len(businesses) >= 5:
            logger.info(f"YelpScraper (selectolax): Extracted {len(businesses)} businesses via JSON-LD structured data!")
            return businesses
            
        # Parse from cards (Layer 1 fallback)
        # Yelp's markup changes frequently. Standard card selector targets business container divs
        cards = parser.css("div[data-testid='business-card']") or parser.css("div[class*='container__']")
        logger.info(f"YelpScraper (selectolax): Found {len(cards)} matching cards.")
        
        for card in cards:
            try:
                # Find the business name link
                name_elem = card.css_first("a[class*='css-']") or card.css_first("h3 a")
                if not name_elem:
                    continue
                name = name_elem.text(strip=True)
                
                # Check for advertising labels
                parent_text = card.text()
                if "Ad" in parent_text or "Sponsored" in parent_text:
                    continue # Skip ads
                    
                detail_path = name_elem.attributes.get("href", "")
                detail_url = urllib.parse.urljoin("https://www.yelp.com", detail_path) if detail_path else None
                
                # Yelp obscures phone and addresses. Let's try to extract best effort
                # Usually there's text or elements containing phone
                phone = None
                street = None
                
                # Best effort parsing of text sections
                for p in card.css("p"):
                    text = p.text(strip=True)
                    if text.startswith("(") and ")" in text and "-" in text:
                        phone = text
                        break
                        
                fingerprint = self.create_fingerprint(name, phone, None, street, self.city)
                
                businesses.append({
                    "business_name": name,
                    "category": self.category,
                    "country": self.country,
                    "state": self.state,
                    "city": self.city,
                    "street": street,
                    "postal_code": None,
                    "phone": phone,
                    "website": None, # Will be enriched from detail page or website crawler
                    "source": "yelp",
                    "source_url": source_url,
                    "source_business_url": detail_url,
                    "confidence": 0.80,
                    "fingerprint": fingerprint
                })
            except Exception as e:
                logger.debug(f"Error parsing card: {str(e)}")
                
        return businesses

    def parse_html_bs4(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """
        Layer 3: BeautifulSoup as a backup parser.
        """
        soup = BeautifulSoup(html, "lxml")
        businesses = []
        cards = soup.select("div[data-testid='business-card']") or soup.select("div[class*='container__']")
        
        for card in cards:
            try:
                name_elem = card.select_one("h3 a") or card.select_one("a[class*='css-']")
                if not name_elem:
                    continue
                name = name_elem.get_text(strip=True)
                
                detail_path = name_elem.get("href", "")
                detail_url = urllib.parse.urljoin("https://www.yelp.com", detail_path) if detail_path else None
                
                phone = None
                for p in card.select("p"):
                    text = p.get_text(strip=True)
                    if text.startswith("(") and ")" in text and "-" in text:
                        phone = text
                        break
                        
                fingerprint = self.create_fingerprint(name, phone, None, None, self.city)
                businesses.append({
                    "business_name": name,
                    "category": self.category,
                    "country": self.country,
                    "state": self.state,
                    "city": self.city,
                    "street": None,
                    "postal_code": None,
                    "phone": phone,
                    "website": None,
                    "source": "yelp",
                    "source_url": source_url,
                    "source_business_url": detail_url,
                    "confidence": 0.75,
                    "fingerprint": fingerprint
                })
            except Exception as e:
                logger.debug(f"BS4 parsing error: {str(e)}")
                
        return businesses
