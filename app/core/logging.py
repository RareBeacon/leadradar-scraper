import logging
import sys
from app.core.config import settings

def setup_logging():
    # Clear existing handlers
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
            
    # Set logging level
    log_level_str = settings.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    root.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s (%(filename)s:%(lineno)d): %(message)s"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root.addHandler(console_handler)
    
    # Quiet verbose libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger("business_scraper")
