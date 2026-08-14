import re
from typing import Optional

def normalize_phone_number(phone: Optional[str]) -> Optional[str]:
    """
    Normalizes a phone number to standard E.164 format best-effort or 10-digit digits.
    Example:
        "(713) 555-1234" -> "+17135551234"
        "1-214-555-4321" -> "+12145554321"
        "512.555.9999" -> "+15125559999"
    """
    if not phone:
        return None
        
    # Remove all non-digit characters
    digits = "".join(c for e in phone for c in e if c.isdigit())
    
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    elif len(digits) > 11:
        # Assume it's already an international number
        return f"+{digits}"
    elif len(digits) > 0:
        # Just return digits if not standard
        return digits
        
    return None
