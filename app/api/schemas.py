from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class JobCreate(BaseModel):
    category: str = Field(..., example="Roofing companies")
    country: str = Field(..., example="United States")
    state: Optional[str] = Field(None, example="Texas")
    city: Optional[str] = Field(None, example="Houston")
    sources: List[str] = Field(default=["yellowpages", "yelp"])
    max_results: int = Field(default=100, ge=1, le=1000)
    enrich_website: bool = True
    enrich_email: bool = True
    enrich_contact: bool = True
    enrich_validate: bool = True
    enrich_dedupe: bool = True

class JobResponse(BaseModel):
    id: str
    category: str
    country: str
    state: Optional[str]
    city: Optional[str]
    sources: str
    max_results: int
    enrich_website: bool
    enrich_email: bool
    enrich_contact: bool
    enrich_validate: bool
    enrich_dedupe: bool
    status: str
    progress: int
    total_results: int
    websites_found: int
    emails_found: int
    validated_emails: int
    duplicates_found: int
    errors_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BusinessResponse(BaseModel):
    id: int
    job_id: str
    business_name: str
    category: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    email_source: Optional[str] = None
    email_type: Optional[str] = None
    email_status: Optional[str] = None
    source: str
    source_url: Optional[str] = None
    source_business_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    scraped_at: datetime
    confidence: float
    fingerprint: str

    class Config:
        from_attributes = True

class JobLogResponse(BaseModel):
    id: int
    job_id: str
    timestamp: datetime
    level: str
    message: str

    class Config:
        from_attributes = True
