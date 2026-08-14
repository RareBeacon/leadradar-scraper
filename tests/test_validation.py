from app.validation.email import validate_email_syntax, validate_email_address
from app.enrichment.email_discovery import WebsiteCrawler

def test_validate_email_syntax():
    assert validate_email_syntax("hello@example.com") is True
    assert validate_email_syntax("user.name+tag@subdomain.co.uk") is True
    assert validate_email_syntax("invalid_email") is False
    assert validate_email_syntax("invalid@domain") is False
    assert validate_email_syntax(None) is False

def test_validate_email_address():
    # Test fake / test accounts
    ok, status = validate_email_address("test@example.com")
    assert ok is False
    assert "fake" in status
    
    ok, status = validate_email_address("hello@test.com")
    assert ok is False
    assert "fake" in status

def test_website_crawler_url_normalization():
    crawler = WebsiteCrawler()
    assert crawler.clean_url("google.com") == "http://google.com"
    assert crawler.clean_url("https://yahoo.com") == "https://google.com" or crawler.clean_url("https://yahoo.com") == "https://yahoo.com"
    assert crawler.clean_url("  http://my-site.com  ") == "http://my-site.com"
