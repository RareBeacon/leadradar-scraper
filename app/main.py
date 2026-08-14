import os
from fastapi import FastAPI, Depends, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database.session import init_db
from app.api.routes import jobs, mock_site
from app.core.logging import logger

# Initialize Database on boot
logger.info("Initializing SQLite Scraper Database tables...")
init_db()

app = FastAPI(
    title="Business Intelligence Scraper & Lead Enrichment Platform",
    description="A professional, modular local lead generation and contact discovery pipeline.",
    version="1.0"
)

# Enable CORS for cross-origin local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(jobs.router)
app.include_router(mock_site.router)

@app.get("/", response_class=HTMLResponse)
def read_root():
    """
    Renders the web-based visual dashboard.
    """
    try:
        template_path = "/home/user/business-scraper/frontend/templates/index.html"
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            return Response(content=html_content, media_type="text/html")
        else:
            return HTMLResponse("<h1>LeadRadar Dashboard File Not Found</h1><p>Please check the project structure.</p>")
    except Exception as e:
        logger.error(f"Error serving dashboard template: {str(e)}")
        return HTMLResponse(f"<h1>Internal Server Error</h1><p>{str(e)}</p>")
