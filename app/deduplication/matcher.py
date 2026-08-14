from typing import Dict, Any, Optional, Tuple
from rapidfuzz import fuzz
from app.extraction.phone import normalize_phone_number
import urllib.parse

def clean_name(name: str) -> str:
    """
    Cleans up business name for comparison (remove LLC, Inc, Corporation, etc.)
    """
    if not name:
        return ""
    name = name.lower().strip()
    # Remove punctuation
    name = re_sub_punc = "".join(c for c in name if c.isalnum() or c.isspace())
    # Remove common corporate suffixes
    suffixes = ["llc", "inc", "corp", "corporation", "ltd", "co", "company", "services", "group", "pros", "specialists"]
    words = name.split()
    filtered_words = [w for r in words if (w := r.strip()) not in suffixes]
    return " ".join(filtered_words)

def extract_domain(url: Optional[str]) -> Optional[str]:
    """
    Extracts the main registered domain from a website URL.
    """
    if not url:
        return None
    try:
        url_lower = url.lower().strip()
        if not url_lower.startswith(("http://", "https://")):
            url_lower = "http://" + url_lower
        parsed = urllib.parse.urlparse(url_lower)
        netloc = parsed.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
        # Skip some directory sites & localhost/loopback addresses
        if any(x in netloc for x in ["yellowpages.com", "yelp.com", "facebook.com", "twitter.com", "instagram.com", "127.0.0.1", "localhost", "0.0.0.0"]):
            return None
        return netloc
    except Exception:
        return None

def match_businesses(b1: Dict[str, Any], b2: Dict[str, Any]) -> Tuple[bool, float, str]:
    """
    Compares two businesses and decides if they are the same entity.
    Returns: (is_match, confidence, match_reason)
    """
    # 1. Check phone number (very strong match)
    phone1 = normalize_phone_number(b1.get("phone"))
    phone2 = normalize_phone_number(b2.get("phone"))
    if phone1 and phone2 and phone1 == phone2:
        return True, 0.98, "phone_match"
        
    # 2. Check website domain (very strong match)
    domain1 = extract_domain(b1.get("website"))
    domain2 = extract_domain(b2.get("website"))
    if domain1 and domain2 and domain1 == domain2:
        return True, 0.95, "website_domain_match"
        
    # 3. Check name similarity and city/address
    name1 = clean_name(b1.get("business_name", ""))
    name2 = clean_name(b2.get("business_name", ""))
    
    name_similarity = fuzz.token_sort_ratio(name1, name2) / 100.0
    
    # Check street address (if exists)
    street1 = b1.get("street", "")
    street2 = b2.get("street", "")
    has_street = bool(street1 and street2)
    
    if has_street:
        street_sim = fuzz.token_sort_ratio(street1.lower(), street2.lower()) / 100.0
        if name_similarity >= 0.80 and street_sim >= 0.80:
            return True, 0.92, f"name_and_street_match (name_sim={name_similarity:.2f}, street_sim={street_sim:.2f})"
            
    # Check city match (if exists)
    city1 = b1.get("city", "")
    city2 = b2.get("city", "")
    has_city = bool(city1 and city2)
    
    if has_city and city1.lower() == city2.lower():
        if name_similarity >= 0.90:
            return True, 0.85, f"name_and_city_match (name_sim={name_similarity:.2f})"
            
    # Absolute name identity
    if name_similarity >= 0.95:
        # If they have different phone numbers, they are distinct branches/entities, not duplicates
        if phone1 and phone2 and phone1 != phone2:
            return False, 0.0, "different_phones_distinct_listings"
        return True, 0.80, f"high_name_similarity_match (name_sim={name_similarity:.2f})"
        
    return False, 0.0, "no_match"
