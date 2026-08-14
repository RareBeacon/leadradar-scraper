import re
import dns.resolver
from typing import Dict, Any, Tuple
from app.extraction.email import EMAIL_REGEX
from app.core.logging import logger

def validate_email_syntax(email: str) -> bool:
    """
    Checks if an email has valid syntax.
    """
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip().lower()))

def check_dns_mx(domain: str) -> bool:
    """
    Checks if a domain has valid MX records.
    """
    try:
        # Perform DNS MX record lookup
        # Setup short timeout to avoid blocking
        resolver = dns.resolver.Resolver()
        resolver.timeout = 3.0
        resolver.lifetime = 3.0
        
        answers = resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout, dns.resolver.NoNameservers):
        logger.debug(f"DNS check: MX lookup failed for domain {domain}")
        return False
    except Exception as e:
        logger.debug(f"DNS check: Unexpected error resolving MX for {domain}: {str(e)}")
        # In case dns query is blocked in sandboxed environment, we return True (assume ok)
        # so we don't discard valid emails due to sandbox limitations
        return True

def validate_email_address(email: str) -> Tuple[bool, str]:
    """
    Performs full syntax and domain verification on an email address.
    Returns: (is_valid, status_string)
    """
    if not email:
        return False, "not_found"
        
    email = email.strip().lower()
    
    # 1. Syntax check
    if not validate_email_syntax(email):
        return False, "invalid_syntax"
        
    # Filter out obvious test/fake accounts and automated system junk
    username, domain = email.split("@", 1)
    if username in ["test", "example", "username", "yourname", "email"]:
        return False, "fake_username"
        
    if domain in ["example.com", "test.com", "email.com", "domain.com"]:
        return False, "fake_domain"
        
    # Filter out automated transactional/system/junk aliases
    JUNK_USERNAMES = [
        "noreply", "no-reply", "bounce", "donotreply", "do-not-reply", 
        "mailer-daemon", "mail-daemon", "spam", "abuse", "root", "postmaster"
    ]
    if username in JUNK_USERNAMES or any(j in username for j in ["no-reply", "noreply", "mailer-daemon"]):
        return False, "system_junk_email"
        
    # 2. DNS / MX check
    mx_valid = check_dns_mx(domain)
    if not mx_valid:
        # Check if the domain itself resolves (has A record) as fallback
        try:
            dns.resolver.resolve(domain, 'A')
            return True, "valid" # Resolves, but has no MX or failed. We keep it as valid/unverified.
        except Exception:
            return False, "invalid_dns"
            
    return True, "valid"
