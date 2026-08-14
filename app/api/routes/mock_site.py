from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/mock-site", tags=["mock-site"])

@router.get("/{slug}", response_class=HTMLResponse)
def get_mock_homepage(slug: str):
    domain = slug.replace("-", "") + ".com"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{slug.replace('-', ' ').title()} - Professional Services</title>
        <script type="application/ld+json">
        {{
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "{slug.replace('-', ' ').title()} LLC",
            "telephone": "(713) 555-1234",
            "url": "http://127.0.0.1:8000/mock-site/{slug}",
            "email": "schema-contact@{domain}",
            "address": {{
                "@type": "PostalAddress",
                "streetAddress": "1204 Elm St",
                "addressLocality": "Houston",
                "addressRegion": "TX",
                "postalCode": "77002",
                "addressCountry": "US"
            }}
        }}
        </script>
    </head>
    <body>
        <header>
            <h1>Welcome to {slug.replace('-', ' ').title()}</h1>
            <nav>
                <a href="/mock-site/{slug}/about">About Us</a> | 
                <a href="/mock-site/{slug}/contact">Contact Us</a>
            </nav>
        </header>
        <main>
            <p>We are the leading local business provider. Delivering top tier quality and satisfaction guaranteed.</p>
            <p>Our phone is (713) 555-1234.</p>
        </main>
        <footer>
            <p>&copy; 2026 {slug.replace('-', ' ').title()}. Email us at homepage-footer@{domain} or find us on social media.</p>
        </footer>
    </body>
    </html>
    """
    return Response(content=html, media_type="text/html")

@router.get("/{slug}/about", response_class=HTMLResponse)
def get_mock_about(slug: str):
    domain = slug.replace("-", "") + ".com"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>About Us - {slug.replace('-', ' ').title()}</title>
    </head>
    <body>
        <h1>About Our Organization</h1>
        <p>Established in 2012, we serve the local region with passion and professional integrity.</p>
        <p>To reach our sales team, please email: <strong>sales [at] {domain} [dot] com</strong> (obfuscated for spam protection).</p>
        <p>Alternative email: support at {domain}</p>
        <p><a href="/mock-site/{slug}">Back to Homepage</a></p>
    </body>
    </html>
    """
    return Response(content=html, media_type="text/html")

@router.get("/{slug}/contact", response_class=HTMLResponse)
def get_mock_contact(slug: str):
    domain = slug.replace("-", "") + ".com"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Contact Us - {slug.replace('-', ' ').title()}</title>
    </head>
    <body>
        <h1>Contact Us today!</h1>
        <p>Our staff is standing by to answer your inquiries.</p>
        
        <div class="contact-methods">
            <p>Send us a direct email at: <a href="mailto:hello@{domain}?subject=Inquiry">hello@{domain}</a></p>
            <p>For support, click: <a href="mailto:support@{domain}">support@{domain}</a></p>
        </div>
        
        <p><a href="/mock-site/{slug}">Back to Homepage</a></p>
    </body>
    </html>
    """
    return Response(content=html, media_type="text/html")
