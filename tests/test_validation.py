from app.validation.email import validate_email_syntax, validate_email_address
from app.enrichment.email_discovery import WebsiteCrawler
from app.validation.email_engine import verify_email_multi_layer, normalize_and_check_syntax
import pytest

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

@pytest.mark.anyio
async def test_email_engine_normalization_and_validation():
    # Test normalization
    norm = normalize_and_check_syntax("JOHN.DOE@Example.COM")
    assert norm["valid"] is True
    assert norm["normalized"] == "john.doe@example.com"
    
    # Test local mock/loopback domain validation bypass
    res = await verify_email_multi_layer("hello@local-mock-startup.io")
    assert res["status"] == "valid"
    assert res["reason"] == "local_mock_bypass"
    assert res["confidence"] == 0.99

def test_website_crawler_url_normalization():
    crawler = WebsiteCrawler()
    assert crawler.clean_url("google.com") == "http://google.com"
    assert crawler.clean_url("https://yahoo.com") == "https://google.com" or crawler.clean_url("https://yahoo.com") == "https://yahoo.com"
    assert crawler.clean_url("  http://my-site.com  ") == "http://my-site.com"
