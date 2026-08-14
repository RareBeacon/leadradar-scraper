import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base, Job, Business, JobLog
import app.database.repository as repo

# Setup in-memory database for testing
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()
    try:
        yield session
    finally:
        session.close()

def test_job_repository_operations(db_session):
    job_id = "TEST01"
    
    # Create Job
    job = repo.create_job(
        db=db_session,
        job_id=job_id,
        category="Dentist",
        country="United States",
        state="TX",
        city="Houston",
        max_results=50,
        sources=["yellowpages"],
        enrich_website=True,
        enrich_email=True,
        enrich_contact=True,
        enrich_validate=True,
        enrich_dedupe=True
    )
    
    assert job.id == job_id
    assert job.category == "Dentist"
    assert job.status == "queued"
    assert job.progress == 0
    
    # Get Job
    retrieved = repo.get_job(db_session, job_id)
    assert retrieved is not None
    assert retrieved.id == job_id
    
    # Update Status
    repo.update_job_status(db_session, job_id, "running")
    assert retrieved.status == "running"
    assert retrieved.started_at is not None
    
    # Update Progress and live counters
    repo.update_job_progress(
        db_session, 
        job_id, 
        progress=45, 
        total_results=20, 
        websites_found=18, 
        emails_found=10, 
        validated_emails=8, 
        duplicates_found=2, 
        errors_count=0
    )
    assert retrieved.progress == 45
    assert retrieved.total_results == 20
    assert retrieved.websites_found == 18
    assert retrieved.emails_found == 10
    assert retrieved.validated_emails == 8
    assert retrieved.duplicates_found == 2
    
    # Add Log
    repo.add_job_log(db_session, job_id, "INFO", "Scraping test business cards")
    logs = repo.get_logs_for_job(db_session, job_id)
    assert len(logs) == 1
    assert logs[0].message == "Scraping test business cards"
    assert logs[0].level == "INFO"
    
    # Add Business record
    biz_data = {
        "business_name": "Test Dentistry",
        "category": "Dentist",
        "country": "United States",
        "state": "TX",
        "city": "Houston",
        "street": "1200 Elm St",
        "postal_code": "77002",
        "phone": "+17135550000",
        "website": "https://testdentistry.com",
        "source": "yellowpages",
        "source_url": "https://yellowpages.com/search...",
        "source_business_url": "https://yellowpages.com/biz...",
        "latitude": 29.7,
        "longitude": -95.3,
        "confidence": 0.90,
        "fingerprint": "test_fingerprint_01"
    }
    
    repo.add_business(db_session, job_id, biz_data)
    
    businesses = repo.get_businesses_for_job(db_session, job_id)
    assert len(businesses) == 1
    assert businesses[0].business_name == "Test Dentistry"
    assert businesses[0].fingerprint == "test_fingerprint_01"
    
    # Check duplicate
    is_dup = repo.check_duplicate_in_job(db_session, job_id, "test_fingerprint_01")
    assert is_dup is True
    
    is_dup_fake = repo.check_duplicate_in_job(db_session, job_id, "fake_fingerprint")
    assert is_dup_fake is False
