from app.extraction.phone import normalize_phone_number
from app.extraction.email import (
    extract_all_emails,
    extract_mailto_links,
    extract_regex_emails,
    extract_obfuscated_emails,
    extract_jsonld_emails
)

def test_phone_normalization():
    assert normalize_phone_number("(713) 555-1234") == "+17135551234"
    assert normalize_phone_number("1-214-555-4321") == "+12145554321"
    assert normalize_phone_number("512.555.9999") == "+15125559999"
    assert normalize_phone_number(None) is None
    assert normalize_phone_number("") is None

def test_extract_mailto_links():
    html = """
    <p>Contact us at <a href="mailto:support@testcompany.com?subject=Help">Support Team</a></p>
    <a href="mailto:info@testcompany.com">General info</a>
    """
    emails = extract_mailto_links(html)
    email_addresses = [e["email"] for e in emails]
    assert "support@testcompany.com" in email_addresses
    assert "info@testcompany.com" in email_addresses

def test_extract_regex_emails():
    text = "Our administrative contact is admin@site.org and general office contact is office@site.org."
    emails = extract_regex_emails(text)
    email_addresses = [e["email"] for e in emails]
    assert "admin@site.org" in email_addresses
    assert "office@site.org" in email_addresses

def test_extract_obfuscated_emails():
    text = """
    Please contact sales [at] site [dot] com for billing.
    For technical support, write to support (at) site (dot) net.
    General inquiries can be sent to info at site.org.
    """
    emails = extract_obfuscated_emails(text)
    email_addresses = [e["email"] for e in emails]
    assert "sales@site.com" in email_addresses
    assert "support@site.net" in email_addresses
    assert "info@site.org" in email_addresses

def test_extract_jsonld_emails():
    html = """
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "Dentistry Group LLC",
        "email": "doctor@dentistrygroup.com",
        "telephone": "(214) 555-4321"
    }
    </script>
    """
    emails = extract_jsonld_emails(html)
    email_addresses = [e["email"] for e in emails]
    assert "doctor@dentistrygroup.com" in email_addresses

def test_extract_all_emails_aggregation():
    html = """
    <html>
    <body>
        <p>Email us at: admin@site.com</p>
        <a href="mailto:info@site.com">Mailto link</a>
        <p>Obfuscated: help [at] site [dot] com</p>
        <script type="application/ld+json">
        {
            "@type": "Organization",
            "email": "schema@site.com"
        }
        </script>
    </body>
    </html>
    """
    emails = extract_all_emails(html)
    email_addresses = [e["email"] for e in emails]
    assert len(email_addresses) == 4
    assert "admin@site.com" in email_addresses
    assert "info@site.com" in email_addresses
    assert "help@site.com" in email_addresses
    assert "schema@site.com" in email_addresses
