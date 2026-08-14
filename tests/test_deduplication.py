from app.deduplication.matcher import clean_name, extract_domain, match_businesses
from app.scrapers.base import BaseScraper

def test_clean_name():
    assert clean_name("ABC Roofing LLC") == "abc roofing"
    assert clean_name("Vertex Dental, Inc.") == "vertex dental"
    assert clean_name("Precision Plumbing Group") == "precision plumbing"

def test_extract_domain():
    assert extract_domain("https://www.houstonroofing.com/contact-us") == "houstonroofing.com"
    assert extract_domain("http://lone-star-roofs.net?ref=test") == "lone-star-roofs.net"
    assert extract_domain("www.brightsmile.org/about") == "brightsmile.org"
    # Scraping directories shouldn't be parsed as business domains
    assert extract_domain("https://www.yellowpages.com/houston-tx/mip/test") is None

def test_match_businesses_phone():
    b1 = {"business_name": "ABC Roofing", "phone": "(713) 555-1111", "website": None}
    b2 = {"business_name": "ABC Roofing LLC", "phone": "+1-713-555-1111", "website": "https://abcroofing.com"}
    is_match, conf, reason = match_businesses(b1, b2)
    assert is_match is True
    assert reason == "phone_match"

def test_match_businesses_domain():
    b1 = {"business_name": "Apex Dental Group", "phone": None, "website": "https://www.apexdental.com"}
    b2 = {"business_name": "Apex Dental Services", "phone": None, "website": "http://apexdental.com/contact"}
    is_match, conf, reason = match_businesses(b1, b2)
    assert is_match is True
    assert reason == "website_domain_match"

def test_match_businesses_name_street():
    b1 = {"business_name": "Lone Star Plumbers", "street": "4509 Westheimer Rd", "city": "Houston"}
    b2 = {"business_name": "Lone Star Plumbing LLC", "street": "4509 Westheimer Road", "city": "Houston"}
    is_match, conf, reason = match_businesses(b1, b2)
    assert is_match is True
    assert "name_and_street_match" in reason

def test_match_businesses_no_match():
    b1 = {"business_name": "First Dentist", "city": "Houston"}
    b2 = {"business_name": "Second Dentist LLC", "city": "Houston"}
    is_match, conf, reason = match_businesses(b1, b2)
    assert is_match is False

def test_base_scraper_create_fingerprint():
    scraper = BaseScraper("roofing", "United States")
    fp1 = scraper.create_fingerprint("ABC Roofing LLC", "(713) 555-1111", "https://abcroofing.com", "1204 Elm St", "Houston")
    fp2 = scraper.create_fingerprint("ABC Roofing Services", "+1-713-555-1111", "http://abcroofing.com", "1204 Elm Rd", "Houston")
    # They should have the same phone-based fingerprint
    assert fp1 == fp2
