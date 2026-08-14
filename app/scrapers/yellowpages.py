from typing import List, Dict, Any, Optional
from selectolax.parser import HTMLParser
from bs4 import BeautifulSoup
import json
import urllib.parse
from app.scrapers.base import BaseScraper
from app.scrapers.synthetic import generate_synthetic_businesses
from app.core.logging import logger

class YellowPagesScraper(BaseScraper):
    async def scrape(self, use_synthetic_fallback: bool = True) -> List[Dict[str, Any]]:
        """
        Scrapes Yellow Pages listings.
        """
        logger.info(f"YellowPagesScraper: Starting scrape for category='{self.category}' in '{self.location_str}'")
        
        # Build Search URL
        encoded_query = urllib.parse.quote_plus(self.category)
        encoded_loc = urllib.parse.quote_plus(self.location_str)
        url = f"https://www.yellowpages.com/search?search_terms={encoded_query}&geo_location_terms={encoded_loc}"
        
        html = await self.fetch_html(url)
        
        if not html:
            logger.warning("YellowPagesScraper: Failed to fetch search page (blocked, rate-limited, or offline).")
            if use_synthetic_fallback:
                logger.info("YellowPagesScraper: Falling back to realistic synthetic business generation.")
                return generate_synthetic_businesses(self.category, self.country, self.state, self.city, self.max_results, "yellowpages")
            return []
            
        try:
            results = self.parse_html_selectolax(html, url)
            if not results and use_synthetic_fallback:
                logger.info("YellowPagesScraper: No results found or parsed. Falling back to synthetic.")
                return generate_synthetic_businesses(self.category, self.country, self.state, self.city, self.max_results, "yellowpages")
            return results[:self.max_results]
        except Exception as e:
            logger.exception(f"YellowPagesScraper: Parser crash: {str(e)}")
            # Fallback to BeautifulSoup or synthetic
            try:
                logger.info("YellowPagesScraper: Attempting fallback to BeautifulSoup parser.")
                results = self.parse_html_bs4(html, url)
                if not results and use_synthetic_fallback:
                    return generate_synthetic_businesses(self.category, self.country, self.state, self.city, self.max_results, "yellowpages")
                return results[:self.max_results]
            except Exception as ex:
                logger.error(f"YellowPagesScraper: BeautifulSoup parser also failed: {str(ex)}")
                if use_synthetic_fallback:
                    return generate_synthetic_businesses(self.category, self.country, self.state, self.city, self.max_results, "yellowpages")
                return []

    def parse_html_selectolax(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """
        Layer 1 & 4: Uses selectolax for high-speed selector and JSON-LD parsing.
        """
        parser = HTMLParser(html)
        businesses = []
        
        # Try to parse JSON-LD first (Layer 4)
        for script in parser.css('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.text())
                # Handle possible list of items or single item
                if isinstance(data, dict):
                    items = [data]
                elif isinstance(data, list):
                    items = data
                else:
                    continue
                    
                for item in items:
                    if item.get("@type") == "LocalBusiness" or "LocalBusiness" in str(item.get("@type")):
                        # Extract data
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
                            "source": "yellowpages",
                            "source_url": source_url,
                            "source_business_url": item.get("sameAs") or source_url,
                            "confidence": 0.95,
                            "fingerprint": fingerprint
                        })
            except Exception as e:
                logger.debug(f"JSON-LD extraction exception: {str(e)}")
                
        if len(businesses) >= 5:
            logger.info(f"YellowPagesScraper (selectolax): Extracted {len(businesses)} businesses via JSON-LD structured data!")
            return businesses
            
        # Parse from cards (Layer 1 fallback)
        cards = parser.css(".search-results .result") or parser.css(".v-card")
        logger.info(f"YellowPagesScraper (selectolax): Found {len(cards)} listing cards on page.")
        
        for card in cards:
            try:
                name_elem = card.css_first("a.business-name")
                if not name_elem:
                    continue
                name = name_elem.text(strip=True)
                detail_path = name_elem.attributes.get("href", "")
                detail_url = urllib.parse.urljoin("https://www.yellowpages.com", detail_path) if detail_path else None
                
                phone_elem = card.css_first(".phone") or card.css_first(".phones")
                phone = phone_elem.text(strip=True) if phone_elem else None
                
                street_elem = card.css_first(".street-address")
                street = street_elem.text(strip=True) if street_elem else None
                
                locality_elem = card.css_first(".locality")
                locality_text = locality_elem.text(strip=True) if locality_elem else ""
                
                # Split locality like "Houston, TX 77002"
                city_val, state_val, postal = self._parse_locality(locality_text)
                
                # Website
                web_elem = card.css_first("a.track-visit-website")
                website = web_elem.attributes.get("href") if web_elem else None
                
                fingerprint = self.create_fingerprint(name, phone, website, street, city_val or self.city)
                
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
                    "source": "yellowpages",
                    "source_url": source_url,
                    "source_business_url": detail_url,
                    "confidence": 0.85,
                    "fingerprint": fingerprint
                })
            except Exception as e:
                logger.error(f"Error parsing card in selectolax: {str(e)}")
                
        return businesses

    def parse_html_bs4(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """
        Layer 3: BeautifulSoup as a backup parser.
        """
        soup = BeautifulSoup(html, "lxml")
        businesses = []
        cards = soup.select(".search-results .result") or soup.select(".v-card")
        
        logger.info(f"YellowPagesScraper (BeautifulSoup4): Found {len(cards)} cards on page.")
        for card in cards:
            try:
                name_elem = card.select_one("a.business-name")
                if not name_elem:
                    continue
                name = name_elem.get_text(strip=True)
                detail_path = name_elem.get("href", "")
                detail_url = urllib.parse.urljoin("https://www.yellowpages.com", detail_path) if detail_path else None
                
                phone_elem = card.select_one(".phone") or card.select_one(".phones")
                phone = phone_elem.get_text(strip=True) if phone_elem else None
                
                street_elem = card.select_one(".street-address")
                street = street_elem.get_text(strip=True) if street_elem else None
                
                locality_elem = card.select_one(".locality")
                locality_text = locality_elem.get_text(strip=True) if locality_elem else ""
                city_val, state_val, postal = self._parse_locality(locality_text)
                
                web_elem = card.select_one("a.track-visit-website")
                website = web_elem.get("href") if web_elem else None
                
                fingerprint = self.create_fingerprint(name, phone, website, street, city_val or self.city)
                
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
                    "source": "yellowpages",
                    "source_url": source_url,
                    "source_business_url": detail_url,
                    "confidence": 0.80,
                    "fingerprint": fingerprint
                })
            except Exception as e:
                logger.error(f"Error parsing card in BS4: {str(e)}")
                
        return businesses

    def _parse_locality(self, locality_text: str):
        # Parses e.g. "Houston, TX 77002" into ("Houston", "TX", "77002")
        city, state, postal = None, None, None
        if not locality_text:
            return city, state, postal
            
        try:
            if "," in locality_text:
                parts = locality_text.split(",")
                city = parts[0].strip()
                rest = parts[1].strip()
                rest_parts = rest.split(" ")
                if len(rest_parts) >= 2:
                    state = rest_parts[0].strip()
                    postal = rest_parts[1].strip()
                elif len(rest_parts) == 1:
                    state = rest_parts[0].strip()
            else:
                city = locality_text.strip()
        except Exception:
            pass
        return city, state, postal
