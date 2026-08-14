from typing import Optional
from app.core.logging import logger

class BrowserRenderer:
    _playwright_available = None

    @classmethod
    def is_available(cls) -> bool:
        if cls._playwright_available is not None:
            return cls._playwright_available
            
        try:
            from playwright.async_api import async_playwright
            cls._playwright_available = True
        except ImportError:
            cls._playwright_available = False
            
        return cls._playwright_available

    async def render_page(self, url: str, wait_selector: Optional[str] = None) -> Optional[str]:
        """
        Layer 3: Playwright-based browser rendering.
        Attempts to boot up a browser instance to fetch and render dynamic javascript content,
        falling back to standard fetch if playwright is unavailable.
        """
        if not self.is_available():
            logger.warning(f"Playwright browser automation requested for URL {url} but 'playwright' is not installed/available. Skipping.")
            return None
            
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                logger.info(f"Launching Playwright browser to fetch dynamic content: {url}")
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                if wait_selector:
                    try:
                        await page.wait_for_selector(wait_selector, timeout=5000)
                    except Exception:
                        logger.warning(f"Playwright wait_for_selector '{wait_selector}' timed out. Capturing current DOM anyway.")
                        
                content = await page.content()
                await browser.close()
                return content
        except Exception as e:
            logger.error(f"Playwright render failed for URL {url}: {str(e)}")
            return None
