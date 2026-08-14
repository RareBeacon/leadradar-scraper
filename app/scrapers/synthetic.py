import random
from typing import List, Dict, Any, Optional

# Sample data pools
BUSINESS_NAME_PARTS = {
    "roofing": (["Apex", "Lone Star", "Houston", "Vertex", "Precision", "Quality", "Sunward", "Elite", "Premier", "EcoShield"], 
                ["Roofing", "Roofs", "Roofing & Construction", "Roofing Specialists", "Roofing Pros", "Contractors"],
                ["LLC", "Inc.", "Services", "Group"]),
    "dentist": (["Apex", "Bright Smile", "Family", "Gentle", "Downtown", "Metro", "Cornerstone", "Oak Forest", "Pearl"],
                ["Dental", "Dentistry", "Dental Care", "Family Dental", "Orthodontics"],
                ["LLC", "P.C.", "Group"]),
    "plumber": (["Rapid Flow", "Emergency", "Metro", "Precision", "A1", "Blue Wave", "Rooter", "ProDrain", "Pioneer"],
                ["Plumbing", "Plumbing & Heating", "Plumbers", "Plumbing Services"],
                ["LLC", "Services", "Inc."]),
    "restaurant": (["The Golden Spoon", "Bella Italia", "Taco Oasis", "Canyon Grill", "Corner Bistro", "Noodle House", "Coastal Catch", "Spice Route"],
                   ["Bistro", "Grill", "Kitchen", "Eatery", "Diner", "Cafe", "House", "Tavern"],
                   []),
    "lawyer": (["Baker & Associates", "Justice", "Sentinel", "Summit", "Vanguard", "Fairpoint", "Stonehenge"],
               ["Law", "Law Firm", "Legal Group", "Defense", "Partners"],
               ["L.L.P.", "P.C."])
}

STREET_NAMES = ["Oak St", "Elm Road", "Westheimer Rd", "Broadway Ave", "Main St", "Washington Ave", "Post Oak Blvd", "Richmond Ave", "Memorial Dr", "Shepherd Dr"]
CITIES_DATA = {
    "houston": {"state": "TX", "zip": "77001", "area_code": "713"},
    "dallas": {"state": "TX", "zip": "75201", "area_code": "214"},
    "austin": {"state": "TX", "zip": "78701", "area_code": "512"},
    "san antonio": {"state": "TX", "zip": "78201", "area_code": "210"},
    "new york": {"state": "NY", "zip": "10001", "area_code": "212"},
    "los angeles": {"state": "CA", "zip": "90001", "area_code": "213"},
    "chicago": {"state": "IL", "zip": "60601", "area_code": "312"},
    "miami": {"state": "FL", "zip": "33101", "area_code": "305"}
}

def get_city_info(city: Optional[str]) -> Dict[str, str]:
    if not city:
        return {"state": "TX", "zip": "77002", "area_code": "713"}
    city_lower = city.lower().strip()
    return CITIES_DATA.get(city_lower, {"state": "TX", "zip": "77002", "area_code": "713"})

def generate_synthetic_businesses(category: str, country: str, state: Optional[str], city: Optional[str], max_results: int, source: str) -> List[Dict[str, Any]]:
    """
    Generates extremely realistic, mock local business records for testing and fallback.
    """
    results = []
    
    # Determine the primary category keyword
    cat_keyword = "roofing"
    category_lower = category.lower()
    if "dent" in category_lower:
        cat_keyword = "dentist"
    elif "plumb" in category_lower:
        cat_keyword = "plumber"
    elif "food" in category_lower or "rest" in category_lower or "eat" in category_lower:
        cat_keyword = "restaurant"
    elif "law" in category_lower or "legal" in category_lower or "attorney" in category_lower:
        cat_keyword = "lawyer"
        
    parts = BUSINESS_NAME_PARTS.get(cat_keyword)
    
    city_name = city or "Houston"
    city_info = get_city_info(city_name)
    state_code = state or city_info["state"]
    zip_code_start = int(city_info["zip"])
    area_code = city_info["area_code"]
    
    # Generate seed-based random to have consistent results per category/city if desired
    # We will use normal random for now
    
    count = min(max_results, random.randint(15, 30)) # Limit to a reasonable number for demo/tests
    
    for i in range(count):
        # Build business name
        p1 = random.choice(parts[0])
        p2 = random.choice(parts[1])
        p3 = random.choice(parts[2]) if parts[2] else ""
        name = f"{p1} {p2} {p3}".strip()
        
        # Avoid duplicate names in the same generation
        if any(r["business_name"] == name for r in results):
            name = f"{p1} & Co. {p2}"
            
        street_num = random.randint(100, 9999)
        street_name = random.choice(STREET_NAMES)
        street = f"{street_num} {street_name}"
        postal = str(zip_code_start + random.randint(0, 50))
        
        phone_num = f"({area_code}) 555-{random.randint(1000, 9999)}"
        
        slug = name.lower().replace(" ", "-").replace("&", "and").replace(".", "").replace(",", "")
        # The official website will point to our FastAPI local web server!
        # This will allow our enrichment worker to crawl actual mock HTML pages on our server!
        website = f"http://127.0.0.1:8000/mock-site/{slug}"
        
        # Source URLs
        if source == "yellowpages":
            source_url = f"https://www.yellowpages.com/search?search_terms={category.replace(' ', '+')}&geo_location_terms={city_name.replace(' ', '+')}%2C+{state_code}"
            source_business_url = f"https://www.yellowpages.com/houston-tx/mip/{slug}-5555555"
        else:
            source_url = f"https://www.yelp.com/search?find_desc={category.replace(' ', '+')}&find_loc={city_name.replace(' ', '+')}%2C+{state_code}"
            source_business_url = f"https://www.yelp.com/biz/{slug}"
            
        # Latitude / Longitude
        lat = 29.7604 + random.uniform(-0.1, 0.1) # Center on Houston approx
        lon = -95.3698 + random.uniform(-0.1, 0.1)
        
        # Build a record
        record = {
            "business_name": name,
            "category": category,
            "country": country,
            "state": state_code,
            "city": city_name,
            "street": street,
            "postal_code": postal,
            "phone": phone_num,
            "website": website,
            "source": source,
            "source_url": source_url,
            "source_business_url": source_business_url,
            "latitude": lat,
            "longitude": lon,
            "confidence": round(random.uniform(0.85, 0.98), 2),
            "email": None, # Will be enriched
            "email_source": None,
            "email_type": None,
            "email_status": "unverified"
        }
        
        results.append(record)
        
    return results
