import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import Job, Business, JobLog
from app.core.logging import logger

def create_job(db: Session, job_id: str, category: str, country: str, state: Optional[str], city: Optional[str], max_results: int, sources: List[str], enrich_website: bool, enrich_email: bool, enrich_contact: bool, enrich_validate: bool, enrich_dedupe: bool) -> Job:
    job = Job(
        id=job_id,
        category=category,
        country=country,
        state=state,
        city=city,
        max_results=max_results,
        sources=",".join(sources),
        enrich_website=enrich_website,
        enrich_email=enrich_email,
        enrich_contact=enrich_contact,
        enrich_validate=enrich_validate,
        enrich_dedupe=enrich_dedupe,
        status="queued",
        progress=0,
        created_at=datetime.datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_job(db: Session, job_id: str) -> Optional[Job]:
    return db.query(Job).filter(Job.id == job_id).first()

def get_jobs(db: Session, limit: int = 100) -> List[Job]:
    return db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()

def update_job_status(db: Session, job_id: str, status: str) -> Optional[Job]:
    job = get_job(db, job_id)
    if job:
        job.status = status
        if status == "running" and not job.started_at:
            job.started_at = datetime.datetime.utcnow()
        elif status in ["completed", "failed", "cancelled"]:
            job.completed_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(job)
    return job

def update_job_progress(db: Session, job_id: str, progress: int, total_results: int = None, websites_found: int = None, emails_found: int = None, validated_emails: int = None, duplicates_found: int = None, errors_count: int = None) -> Optional[Job]:
    job = get_job(db, job_id)
    if job:
        job.progress = progress
        if total_results is not None:
            job.total_results = total_results
        if websites_found is not None:
            job.websites_found = websites_found
        if emails_found is not None:
            job.emails_found = emails_found
        if validated_emails is not None:
            job.validated_emails = validated_emails
        if duplicates_found is not None:
            job.duplicates_found = duplicates_found
        if errors_count is not None:
            job.errors_count = errors_count
        db.commit()
        db.refresh(job)
    return job

def add_job_log(db: Session, job_id: str, level: str, message: str) -> JobLog:
    # Print to standard console too
    if level.upper() == "ERROR":
        logger.error(f"[Job {job_id}] {message}")
    elif level.upper() == "WARNING":
        logger.warning(f"[Job {job_id}] {message}")
    else:
        logger.info(f"[Job {job_id}] {message}")
        
    job_log = JobLog(
        job_id=job_id,
        level=level.upper(),
        message=message,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(job_log)
    db.commit()
    return job_log

def get_logs_for_job(db: Session, job_id: str, limit: int = 500) -> List[JobLog]:
    return db.query(JobLog).filter(JobLog.job_id == job_id).order_by(JobLog.timestamp.asc()).limit(limit).all()

def add_business(db: Session, job_id: str, data: dict) -> Business:
    # Ensure keys exist or set default
    business = Business(
        job_id=job_id,
        business_name=data.get("business_name"),
        category=data.get("category"),
        country=data.get("country"),
        state=data.get("state"),
        city=data.get("city"),
        street=data.get("street"),
        postal_code=data.get("postal_code"),
        phone=data.get("phone"),
        website=data.get("website"),
        email=data.get("email"),
        email_source=data.get("email_source"),
        email_type=data.get("email_type"),
        email_status=data.get("email_status"),
        source=data.get("source"),
        source_url=data.get("source_url"),
        source_business_url=data.get("source_business_url"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        scraped_at=datetime.datetime.utcnow(),
        confidence=data.get("confidence", 1.0),
        fingerprint=data.get("fingerprint")
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business

def get_businesses_for_job(db: Session, job_id: str) -> List[Business]:
    return db.query(Business).filter(Business.job_id == job_id).all()

def check_duplicate_in_job(db: Session, job_id: str, fingerprint: str) -> bool:
    exists = db.query(Business.id).filter(Business.job_id == job_id, Business.fingerprint == fingerprint).first()
    return exists is not None
