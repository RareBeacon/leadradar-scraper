import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.database.session import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True) # E.g., short UUID or hex ID like 8F29A1
    category = Column(String, nullable=False)
    country = Column(String, nullable=False)
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)
    max_results = Column(Integer, default=100)
    sources = Column(String, nullable=False) # Comma-separated like "yellowpages,yelp"
    
    # Enrichment configurations
    enrich_website = Column(Boolean, default=True)
    enrich_email = Column(Boolean, default=True)
    enrich_contact = Column(Boolean, default=True)
    enrich_validate = Column(Boolean, default=True)
    enrich_dedupe = Column(Boolean, default=True)
    
    # Live stats
    status = Column(String, default="queued") # "queued", "running", "completed", "failed", "cancelled"
    progress = Column(Integer, default=0) # 0 to 100
    total_results = Column(Integer, default=0)
    websites_found = Column(Integer, default=0)
    emails_found = Column(Integer, default=0)
    validated_emails = Column(Integer, default=0)
    duplicates_found = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    businesses = relationship("Business", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")


class Business(Base):
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    
    business_name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)
    street = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Email discovery fields
    email = Column(String, nullable=True)
    email_source = Column(String, nullable=True) # e.g. URL of contact page where email was found
    email_type = Column(String, nullable=True) # e.g. "contact", "support", "generic", "mailto"
    email_status = Column(String, nullable=True) # e.g. "valid", "invalid", "unverified"
    
    # Scraper sources
    source = Column(String, nullable=False) # "yellowpages", "yelp"
    source_url = Column(String, nullable=True) # Search list page URL
    source_business_url = Column(String, nullable=True) # Detail profile URL
    
    # Geospatial
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    scraped_at = Column(DateTime, default=datetime.datetime.utcnow)
    confidence = Column(Float, default=1.0)
    fingerprint = Column(String, nullable=False, index=True) # Unique ID per business to help deduplicate
    
    # Relationships
    job = relationship("Job", back_populates="businesses")
    
    __table_args__ = (
        Index("idx_job_fingerprint", "job_id", "fingerprint"),
    )


class JobLog(Base):
    __tablename__ = "job_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    level = Column(String, nullable=False) # "INFO", "WARNING", "ERROR", etc.
    message = Column(Text, nullable=False)
    
    # Relationships
    job = relationship("Job", back_populates="logs")
