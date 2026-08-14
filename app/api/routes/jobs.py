import csv
import io
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import Workbook

from app.database.session import get_db
import app.database.repository as repo
from app.api.schemas import JobCreate, JobResponse, BusinessResponse, JobLogResponse
from app.workers.scrape_worker import queue_background_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_scraping_job(payload: JobCreate, db: Session = Depends(get_db)):
    """
    Submits a new business scraping and enrichment job.
    """
    # Generate unique 6-character hex string as Job ID (e.g. 8F29A1)
    job_id = uuid.uuid4().hex[:6].upper()
    
    # Store in DB
    job = repo.create_job(
        db=db,
        job_id=job_id,
        category=payload.category,
        country=payload.country,
        state=payload.state,
        city=payload.city,
        max_results=payload.max_results,
        sources=payload.sources,
        enrich_website=payload.enrich_website,
        enrich_email=payload.enrich_email,
        enrich_contact=payload.enrich_contact,
        enrich_validate=payload.enrich_validate,
        enrich_dedupe=payload.enrich_dedupe
    )
    
    # Dispatch background task asynchronously
    repo.add_job_log(db, job_id, "INFO", "Scrape job successfully queued in background worker.")
    queue_background_job(job_id)
    
    return job

@router.get("/", response_model=List[JobResponse])
def list_scraping_jobs(limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves all scraper jobs.
    """
    return repo.get_jobs(db, limit=limit)

@router.get("/{job_id}", response_model=JobResponse)
def get_scraping_job(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a single job status and its metrics.
    """
    job = repo.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{job_id}/logs", response_model=List[JobLogResponse])
def get_job_logs(job_id: str, limit: int = 500, db: Session = Depends(get_db)):
    """
    Retrieves live log statements for a job.
    """
    job = repo.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return repo.get_logs_for_job(db, job_id, limit=limit)

@router.get("/{job_id}/businesses", response_model=List[BusinessResponse])
def get_job_businesses(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the parsed business records collected by a job.
    """
    job = repo.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return repo.get_businesses_for_job(db, job_id)

@router.get("/{job_id}/export/{export_format}")
def export_job_results(job_id: str, export_format: str, db: Session = Depends(get_db)):
    """
    Exports a scraping job's discovered business dataset as CSV, XLSX, or JSON.
    """
    job = repo.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    businesses = repo.get_businesses_for_job(db, job_id)
    export_format = export_format.lower().strip()
    
    filename = f"scraper_results_{job_id}_{job.category.lower().replace(' ', '_')}"
    
    # Header names for exported reports
    headers_list = [
        "Business Name", "Category", "Country", "State/Region", "City", 
        "Street", "Postal Code", "Phone", "Website", "Email", 
        "Email Source URL", "Email Type", "Email Status", "Source Directory", 
        "Source Category URL", "Source Business Detail URL", "Latitude", "Longitude", 
        "Scraped At", "Confidence Score"
    ]
    
    def format_row(b) -> list:
        return [
            b.business_name, b.category, b.country, b.state, b.city,
            b.street, b.postal_code, b.phone, b.website, b.email,
            b.email_source, b.email_type, b.email_status, b.source,
            b.source_url, b.source_business_url, b.latitude, b.longitude,
            b.scraped_at.strftime("%Y-%m-%d %H:%M:%S") if b.scraped_at else "",
            b.confidence
        ]
        
    if export_format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers_list)
        for b in businesses:
            writer.writerow(format_row(b))
            
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
        
    elif export_format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = "Scrape Results"
        
        # Style headings
        ws.append(headers_list)
        for b in businesses:
            ws.append(format_row(b))
            
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
        
    elif export_format == "json":
        data = []
        for b in businesses:
            data.append({
                "business_name": b.business_name,
                "category": b.category,
                "country": b.country,
                "state": b.state,
                "city": b.city,
                "street": b.street,
                "postal_code": b.postal_code,
                "phone": b.phone,
                "website": b.website,
                "email": b.email,
                "email_source": b.email_source,
                "email_type": b.email_type,
                "email_status": b.email_status,
                "source": b.source,
                "source_url": b.source_url,
                "source_business_url": b.source_business_url,
                "latitude": b.latitude,
                "longitude": b.longitude,
                "scraped_at": b.scraped_at.strftime("%Y-%m-%d %H:%M:%S") if b.scraped_at else None,
                "confidence": b.confidence
            })
            
        import json
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}.json"}
        )
        
    else:
        raise HTTPException(status_code=400, detail="Invalid export format. Supported: csv, xlsx, json")
