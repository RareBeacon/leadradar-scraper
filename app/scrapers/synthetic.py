import random
import os
from typing import List, Dict, Any, Optional

# Sample data pools per industry category
BUSINESS_NAME_PARTS = {
    "roofing": (["Apex", "Lone Star", "Vertex", "Precision", "Quality", "Sunward", "Elite", "Premier", "EcoShield", "Summit"], 
                ["Roofing", "Roofs", "Roofing & Construction", "Roofing Specialists", "Roofing Pros", "Contractors"],
                ["LLC", "Inc.", "Services", "Group"]),
    "dentist": (["Apex", "Bright Smile", "Family", "Gentle", "Downtown", "Metro", "Cornerstone", "Oak Forest", "Pearl"],
                ["Dental", "Dentistry", "Dental Care", "Family Dental", "Orthodontics"],
                ["LLC", "P.C.", "Group", ""]),
    "plumber": (["Rapid Flow", "Emergency", "Metro", "Precision", "A1", "Blue Wave", "Rooter", "ProDrain", "Pioneer"],
                ["Plumbing", "Plumbing & Heating", "Plumbers", "Plumbing Services"],
                ["LLC", "Services", "Inc.", ""]),
    "restaurant": (["The Golden Spoon", "Bella Italia", "Taco Oasis", "Canyon Grill", "Corner Bistro", "Noodle House", "Coastal Catch", "Spice Route"],
                   ["Bistro", "Grill", "Kitchen", "Eatery", "Diner", "Cafe", "House", "Tavern"],
                   []),
    "lawyer": (["Baker & Associates", "Justice", "Sentinel", "Summit", "Vanguard", "Fairpoint", "Stonehenge"],
               ["Law", "Law Firm", "Legal Group", "Defense", "Partners"],
               ["L.L.P.", "P.C.", ""]),
    "med_spa": (["Glow", "Radiant", "Serene", "La Bella", "Revitalize", "Pure", "Aura", "Zen", "Bliss", "Skin & Body", "Youthful", "Aesthetic"],
                ["Med Spa", "Medical Spa", "Aesthetics", "Aesthetics & Wellness", "Skin Clinic", "Laser Center", "Wellness Spa"],
                ["LLC", "Inc.", "Group", ""])
}

# Country data mapping for global telephone formats, zip formats, and street nomenclatures
GLOBAL_COUNTRY_DATA = {
    "united states": {"code": "+1", "zip_prefix": "", "zip_len": 5, "streets": ["Oak St", "Elm Rd", "Broadway Ave", "Main St", "Washington Ave", "Post Oak Blvd"]},
    "usa": {"code": "+1", "zip_prefix": "", "zip_len": 5, "streets": ["Oak St", "Elm Rd", "Broadway Ave", "Main St", "Washington Ave", "Post Oak Blvd"]},
    "us": {"code": "+1", "zip_prefix": "", "zip_len": 5, "streets": ["Oak St", "Elm Rd", "Broadway Ave", "Main St", "Washington Ave", "Post Oak Blvd"]},
    
    "canada": {"code": "+1", "zip_prefix": "K1A ", "zip_len": 3, "streets": ["Yonge St", "King St", "Queen St", "Jasper Ave", "Hastings St", "Robson St"]},
    "ca": {"code": "+1", "zip_prefix": "K1A ", "zip_len": 3, "streets": ["Yonge St", "King St", "Queen St", "Jasper Ave", "Hastings St", "Robson St"]},
    
    "united kingdom": {"code": "+44", "zip_prefix": "SW1A ", "zip_len": 2, "streets": ["High St", "London Rd", "Victoria Rd", "Church St", "Oxford St", "Piccadilly"]},
    "uk": {"code": "+44", "zip_prefix": "SW1A ", "zip_len": 2, "streets": ["High St", "London Rd", "Victoria Rd", "Church St", "Oxford St", "Piccadilly"]},
    "gb": {"code": "+44", "zip_prefix": "SW1A ", "zip_len": 2, "streets": ["High St", "London Rd", "Victoria Rd", "Church St", "Oxford St", "Piccadilly"]},
    
    "australia": {"code": "+61", "zip_prefix": "20", "zip_len": 2, "streets": ["George St", "Collins St", "Bourke St", "Queen St", "Elizabeth St", "Adelaide St"]},
    "au": {"code": "+61", "zip_prefix": "20", "zip_len": 2, "streets": ["George St", "Collins St", "Bourke St", "Queen St", "Elizabeth St", "Adelaide St"]},
    
    "germany": {"code": "+49", "zip_prefix": "10", "zip_len": 3, "streets": ["Hauptstraße", "Bahnhofstraße", "Schillerstraße", "Goethestraße", "Kaiserstraße"]},
    "de": {"code": "+49", "zip_prefix": "10", "zip_len": 3, "streets": ["Hauptstraße", "Bahnhofstraße", "Schillerstraße", "Goethestraße", "Kaiserstraße"]},
    
    "france": {"code": "+33", "zip_prefix": "7500", "zip_len": 1, "streets": ["Rue de la Paix", "Avenue des Champs-Élysées", "Rue de Rivoli", "Rue de la Pompe"]},
    "fr": {"code": "+33", "zip_prefix": "7500", "zip_len": 1, "streets": ["Rue de la Paix", "Avenue des Champs-Élysées", "Rue de Rivoli", "Rue de la Pompe"]},
    
    "nigeria": {"code": "+234", "zip_prefix": "100", "zip_len": 3, "streets": ["Herbert Macaulay Way", "Adeniran Ogunsanya St", "Allen Avenue", "Bode Thomas St"]},
    "ng": {"code": "+234", "zip_prefix": "100", "zip_len": 3, "streets": ["Herbert Macaulay Way", "Adeniran Ogunsanya St", "Allen Avenue", "Bode Thomas St"]},
    
    "india": {"code": "+91", "zip_prefix": "1100", "zip_len": 2, "streets": ["Mahatma Gandhi Rd", "Netaji Subhash Marg", "Connaught Place", "Brigade Rd"]},
    "in": {"code": "+91", "zip_prefix": "1100", "zip_len": 2, "streets": ["Mahatma Gandhi Rd", "Netaji Subhash Marg", "Connaught Place", "Brigade Rd"]},
}

def generate_synthetic_businesses(category: str, country: str, state: Optional[str], city: Optional[str], max_results: int, source: str) -> List[Dict[str, Any]]:
    """
    Generates realistic local business leads dynamically matching ANY country, place, or language.
    """
    results = []
    
    # Normalize inputs
    country_lower = country.lower().strip()
    city_name = city or "Capital City"
    state_code = state or "Reg"
    
    # 1. Resolve Country Calling Code & Postal Layout
    country_meta = GLOBAL_COUNTRY_DATA.get(country_lower, {
        "code": f"+{random.randint(20, 990)}", # Generates logical country codes if not pre-registered
        "zip_prefix": str(random.randint(10, 99)) + " ",
        "zip_len": 3,
        "streets": ["High Street", "Central Ave", "Market St", "Station Road", "Park Lane"]
    })
    
    cc_code = country_meta["code"]
    streets_pool = country_meta["streets"]
    
    # 2. Determine Business Category Keywords
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
    elif "spa" in category_lower or "med" in category_lower or "aesthetic" in category_lower or "skin" in category_lower:
        cat_keyword = "med_spa"
        
    parts = BUSINESS_NAME_PARTS.get(cat_keyword)
    
    # 3. Determine Number of Results
    if max_results >= 50:
        count = max_results
    else:
        count = min(max_results, random.randint(15, 30))
        
    for i in range(count):
        # Generate Name
        p1 = random.choice(parts[0])
        p2 = random.choice(parts[1])
        p3 = random.choice(parts[2]) if parts[2] else ""
        
        name = f"{p1} {p2} {p3}".strip()
        # For high-volume requests, ensure absolute uniqueness by incorporating city names and sequential indices
        if count > 50:
            name = f"{p1} {p2} of {city_name} #{i+1}"
        elif any(r["business_name"] == name for r in results):
            name = f"{p1} {city_name} {p2}"
            
        # Generate Street & Postal
        street_num = random.randint(10, 2500)
        street_name = random.choice(streets_pool)
        street_val = f"{street_num} {street_name}"
        
        # Generate Postal
        postal = f"{country_meta['zip_prefix']}{''.join(str(random.randint(0, 9)) for _ in range(country_meta['zip_len']))}"
        
        # Generate Phone (matching localized country calling codes)
        area = random.randint(100, 999)
        local_part = random.randint(1000, 9999)
        phone_num = f"{cc_code} {area} 555 {local_part}"
        
        # Formulate Loopback URL
        slug = name.lower().replace(" ", "-").replace("&", "and").replace(".", "").replace(",", "")
        port = os.environ.get("PORT", "8000")
        website = f"http://127.0.0.1:{port}/mock-site/{slug}"
        
        # Construct directory reference URLs
        encoded_cat = category.replace(' ', '+')
        encoded_loc = city_name.replace(' ', '+')
        
        if source == "yellowpages":
            source_url = f"https://www.yellowpages.com/search?search_terms={encoded_cat}&geo_location_terms={encoded_loc}"
            source_business_url = f"https://www.yellowpages.com/mip/{slug}-5555"
        else:
            source_url = f"https://www.yelp.com/search?find_desc={encoded_cat}&find_loc={encoded_loc}"
            source_business_url = f"https://www.yelp.com/biz/{slug}"
            
        lat = 30.0 + random.uniform(-10.0, 10.0)
        lon = -40.0 + random.uniform(-40.0, 40.0)
        
        results.append({
            "business_name": name,
            "category": category,
            "country": country.title(),
            "state": state_code.upper(),
            "city": city_name.title(),
            "street": street_val,
            "postal_code": postal,
            "phone": phone_num,
            "website": website,
            "source": source,
            "source_url": source_url,
            "source_business_url": source_business_url,
            "latitude": lat,
            "longitude": lon,
            "confidence": round(random.uniform(0.85, 0.98), 2),
            "email": None,
            "email_source": None,
            "email_type": None,
            "email_status": "unverified"
        })
        
    return results
