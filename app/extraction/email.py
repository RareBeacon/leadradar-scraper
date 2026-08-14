import re
import urllib.parse
from typing import List, Dict, Set, Any
from selectolax.parser import HTMLParser
import json

# Regex pattern for normal email address extraction
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# Obfuscated patterns
OBFUSCATED_PATTERNS = [
    # E.g., name [at] domain [dot] com
    re.compile(r'([a-zA-Z0-9._%+-]+)\s*\[\s*at\s*\]\s*([a-zA-Z0-9.-]+)\s*\[\s*dot\s*\]\s*([a-zA-Z]{2,})', re.IGNORECASE),
    # E.g., name (at) domain (dot) com
    re.compile(r'([a-zA-Z0-9._%+-]+)\s*\(\s*at\s*\)\s*([a-zA-Z0-9.-]+)\s*\(\s*dot\s*\)\s*([a-zA-Z]{2,})', re.IGNORECASE),
    # E.g., name at domain.com
    re.compile(r'([a-zA-Z0-9._%+-]+)\s+at\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE)
]

def clean_email(email: str) -> str:
    """
    Cleans up any surrounding noise from parsed email.
    """
    if not email:
        return ""
    email = email.lower().strip()
    # Remove common junk endings/startings
    email = re.sub(r'^(mailto:|email:)', '', email)
    # Remove trailing/leading periods, quotes or braces
    email = email.strip('.\'"`<>(){}[]')
    return email

def extract_mailto_links(html: str) -> List[Dict[str, str]]:
    """
    Method 1: Extracts emails from mailto: links in HTML
    """
    emails = []
    parser = HTMLParser(html)
    for a in parser.css('a[href^="mailto:"]'):
        href = a.attributes.get("href", "")
        parsed_url = urllib.parse.urlparse(href)
        # Mailto emails can contain queries like ?subject=...
        email_part = parsed_url.path
        if "?" in email_part:
            email_part = email_part.split("?")[0]
            
        email_part = urllib.parse.unquote(email_part)
        cleaned = clean_email(email_part)
        if EMAIL_REGEX.match(cleaned):
            emails.append({
                "email": cleaned,
                "type": "mailto",
                "source": href
            })
    return emails

def extract_regex_emails(text: str) -> List[Dict[str, str]]:
    """
    Method 2: Extracts normal emails using regex.
    """
    emails = []
    matches = EMAIL_REGEX.findall(text)
    for match in matches:
        cleaned = clean_email(match)
        if cleaned:
            # Skip obvious static assets / common extensions in emails
            if not any(cleaned.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]):
                emails.append({
                    "email": cleaned,
                    "type": "regex",
                    "source": "text_match"
                })
    return emails

def extract_obfuscated_emails(text: str) -> List[Dict[str, str]]:
    """
    Method 3: Normalizes common obfuscation techniques.
    """
    emails = []
    for pattern in OBFUSCATED_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            if len(match) == 3:
                # Group 1: username, Group 2: domain, Group 3: TLD (e.g. com)
                normalized = f"{match[0]}@{match[1]}.{match[2]}"
                cleaned = clean_email(normalized)
                if EMAIL_REGEX.match(cleaned):
                    emails.append({
                        "email": cleaned,
                        "type": "obfuscated",
                        "source": "obfuscation_normalized"
                    })
            elif len(match) == 2:
                # Group 1: username, Group 2: domain.TLD
                normalized = f"{match[0]}@{match[1]}"
                cleaned = clean_email(normalized)
                if EMAIL_REGEX.match(cleaned):
                    emails.append({
                        "email": cleaned,
                        "type": "obfuscated",
                        "source": "obfuscation_normalized"
                    })
    return emails

def extract_jsonld_emails(html: str) -> List[Dict[str, str]]:
    """
    Method 4: Extracts emails from JSON-LD schema blocks.
    """
    emails = []
    parser = HTMLParser(html)
    for script in parser.css('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.text())
            
            def find_emails(obj):
                if isinstance(obj, dict):
                    email_val = obj.get("email")
                    if email_val and isinstance(email_val, str):
                        cleaned = clean_email(email_val)
                        if EMAIL_REGEX.match(cleaned):
                            emails.append({
                                "email": cleaned,
                                "type": "schema",
                                "source": "jsonld_localbusiness"
                            })
                    for key, val in obj.items():
                        find_emails(val)
                elif isinstance(obj, list):
                    for item in obj:
                        find_emails(item)
                        
            find_emails(data)
        except Exception:
            pass
    return emails

def extract_attributes_emails(html: str) -> List[Dict[str, str]]:
    """
    Method 5: Extracts emails from standard HTML element attributes.
    """
    emails = []
    parser = HTMLParser(html)
    for tag in parser.css('*'):
        for attr in ["title", "placeholder", "value", "content", "data-email", "data-contact"]:
            val = tag.attributes.get(attr, "")
            if val and "@" in val:
                matches = EMAIL_REGEX.findall(val)
                for m in matches:
                    cleaned = clean_email(m)
                    if cleaned:
                        emails.append({
                            "email": cleaned,
                            "type": "attribute",
                            "source": f"attr_{attr}"
                        })
    return emails

def extract_all_emails(html: str) -> List[Dict[str, Any]]:
    """
    Aggregates all email extraction methods and removes exact duplicates,
    returning a normalized list of dictionary elements.
    """
    all_extracted = []
    seen_emails: Set[str] = set()
    
    # Run all extraction methods
    mailto = extract_mailto_links(html)
    jsonld = extract_jsonld_emails(html)
    regex = extract_regex_emails(html)
    obfuscated = extract_obfuscated_emails(html)
    attributes = extract_attributes_emails(html)
    
    # Prioritize mailto and jsonld over raw text regex, obfuscation and attributes
    for item in mailto + jsonld + obfuscated + attributes + regex:
        email_addr = item["email"]
        if email_addr not in seen_emails:
            seen_emails.add(email_addr)
            all_extracted.append(item)
            
    return all_extracted
