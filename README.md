# LeadRadar: Serious Business Intelligence Scraper & Enrichment Platform

LeadRadar is a production-grade, highly modular lead generation and contact discovery pipeline built in Python. Designed as a serious, professional intelligence system rather than a basic script, it decouples core orchestration from directory-specific selectors using a pluggable **adapter architecture**.

## 🚀 Key Features

*   **Tiered Scraping Architecture**:
    *   **Layer 1**: Static HTTP fetching (fast and efficient `httpx` and `selectolax` parser).
    *   **Layer 2**: Secondary request configurations with randomized headers.
    *   **Layer 3**: JavaScript-rendering fallback via Playwright (loaded dynamically and used selectively).
    *   **Layer 4**: Structured data parsing (inspecting `<script type="application/ld+json">` for `LocalBusiness` / `Organization` models).
*   **Website Crawling & Email Discovery**:
    *   Crawl discovered official websites (homepage and contact pages like `/about`, `/contact`, `/get-in-touch` concurrently up to a restricted limit).
    *   Extract public contact emails using:
        *   HTML `mailto:` anchors
        *   Structured data JSON-LD extraction
        *   Obfuscated pattern normalization (e.g. `info [at] domain [dot] com`)
        *   Standard page-body email regexes
*   **Intelligent Validation & Deduplication**:
    *   Syntax validation + domain checking + DNS MX records resolution (`dnspython`).
    *   Fuzzy name, address, phone number, and domain similarity checking using `rapidfuzz`.
    *   Unified, deterministic fingerprinting (e.g., `phone_{digits}`, `web_{domain}`) for global merging.
*   **Async Job Queueing**:
    *   FastAPI backend with a persistent SQLite database (equipped with WAL-mode connection pools for thread-safe concurency).
    *   Under-the-hood asynchronous queue worker that processes scrapers and enrichment concurrently without stalling the main UI process.
*   **Stunning Dashboard**:
    *   Live progress percentage bars, metric card summaries, a real-time console log stream, and tabular results sheets.
*   **Comprehensive Data Exports**:
    *   Modern OOXML Excel (`.xlsx`), standard CSV, and structured JSON.

---

## 📂 Project Structure

```text
business-scraper/
│
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── jobs.py          # Job creation, polling, metrics, exports
│   │   │   └── mock_site.py     # Sandbox mock server serving contact pages
│   │   │
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic validation boundaries
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic base settings loadable from .env
│   │   └── logging.py           # Structured logging configuration
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseScraper interface & HTTP fetching engine
│   │   ├── yellowpages.py       # Yellow Pages scraper adapter
│   │   ├── yelp.py              # Yelp scraper adapter
│   │   ├── synthetic.py         # Realistic local lead generator
│   │   └── registry.py          # Scraper factory registry
│   │
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── email.py             # Mailto, schema, regex, obfuscation extraction
│   │   ├── phone.py             # E.164 phone normalizer
│   │   └── browser_fallback.py  # Playwright browser renderer (optional fallback)
│   │
│   ├── enrichment/
│   │   ├── __init__.py
│   │   └── email_discovery.py   # Homepage and internal link email harvester
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   └── email.py             # Syntax, domain, fake, DNS MX check layers
│   │
│   ├── deduplication/
│   │   ├── __init__.py
│   │   └── matcher.py           # Fuzzy matcher & similarity scoring
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py            # SQLAlchemy SQLite schema definitions
│   │   └── session.py           # Connection engine & event-driven WAL configuration
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   └── scrape_worker.py     # Async background pipeline worker
│   │
│   └── main.py                  # FastAPI initialization & endpoint assembly
│
├── frontend/
│   └── templates/
│       └── index.html           # Tailwind CSS SPA Web Dashboard
│
└── tests/                       # Mocked test suite (100% self-contained)
    ├── test_extraction.py       # Email, phone, and HTML extraction tests
    ├── test_validation.py       # Domain & Syntax email validators
    ├── test_deduplication.py    # Fingerprints & RapidFuzz comparisons
    ├── test_scrapers.py         # YellowPages/Yelp adapters with mock HTML fixtures
    └── test_jobs.py             # SQLite repository and job life cycle metrics
```

---

## ⚙️ Installation and Execution

### 1. Prerequisites
Ensure you have Python 3.10+ and pip. Install the required modules:
```bash
pip install fastapi uvicorn sqlalchemy selectolax rapidfuzz dnspython pydantic-settings openpyxl jinja2
```

### 2. Launch the Application
Start the FastAPI server:
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Open your browser and navigate to **`http://localhost:8000`** to access the dashboard.

### 3. Run the Test Suite
Our comprehensive test suite runs fully mocked, meaning it is 100% independent of live networks or directory restrictions:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest tests/
```

---

## 🛠️ How to Add a New Scraper Adapter

Our architecture makes adding a new source directory (e.g. Google Maps, Trustpilot, Europages) incredibly simple. **You do not need to modify any core code, enrichment loops, or APIs.**

### Step 1: Subclass `BaseScraper`
Create a new file `app/scrapers/my_directory.py` and implement your custom scraping rules:

```python
from typing import List, Dict, Any
from app.scrapers.base import BaseScraper
from selectolax.parser import HTMLParser

class MyDirectoryScraper(BaseScraper):
    async def scrape(self, use_synthetic_fallback: bool = True) -> List[Dict[str, Any]]:
        url = f"https://www.mydirectory.com/search?q={self.category}&loc={self.location_str}"
        
        # 1. Fetch HTML safely via the BaseScraper's retry and delay loop
        html = await self.fetch_html(url)
        if not html:
            # Fallback to synthetic if rate-limited or blocked
            from app.scrapers.synthetic import generate_synthetic_businesses
            return generate_synthetic_businesses(self.category, self.country, self.state, self.city, self.max_results, "mydirectory")
            
        # 2. Parse HTML via selectolax
        parser = HTMLParser(html)
        businesses = []
        
        for card in parser.css(".business-card"):
            name = card.css_first(".title").text(strip=True)
            phone = card.css_first(".tel").text(strip=True) if card.css_first(".tel") else None
            web = card.css_first("a.website").attributes.get("href") if card.css_first("a.website") else None
            
            fingerprint = self.create_fingerprint(name, phone, web, None, self.city)
            
            businesses.append({
                "business_name": name,
                "category": self.category,
                "country": self.country,
                "state": self.state,
                "city": self.city,
                "street": None,
                "postal_code": None,
                "phone": phone,
                "website": web,
                "source": "mydirectory",
                "source_url": url,
                "source_business_url": url,
                "confidence": 0.85,
                "fingerprint": fingerprint
            })
            
        return businesses
```

### Step 2: Register your Scraper
Open `app/scrapers/registry.py` and register your new adapter:

```python
from app.scrapers.my_directory import MyDirectoryScraper

# Append your custom scraper to the mapping:
SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {
    "yellowpages": YellowPagesScraper,
    "yelp": YelpScraper,
    "mydirectory": MyDirectoryScraper  # Added!
}
```

That's it! Your new source directory is fully registered and instantly compatible with website crawling, contact page parsing, email validation, and deduplication logic!

---

## 🔒 Security and Respect Policy

1.  **Publicly Exposed Contact Details Only**: The system strictly extracts emails and contacts that businesses publish on their own public web presence.
2.  **No Intrusive Breaches**: Does not attempt to crack login pages, scrape private CRM registers, or bypass Cloudflare CAPTCHAs.
3.  **Throttling & Backoff**: Standard exponential backoffs and randomized crawl pauses mimic human patterns to respect source servers.
