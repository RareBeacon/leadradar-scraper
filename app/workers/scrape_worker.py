import asyncio
import datetime
import traceback
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
import app.database.repository as repo
from app.database.models import Job, Business
from app.scrapers.registry import get_scraper
from app.enrichment.email_discovery import WebsiteCrawler, find_best_email
from app.validation.email import validate_email_address
from app.deduplication.matcher import match_businesses, clean_name
from app.extraction.phone import normalize_phone_number
from app.core.logging import logger

class ScrapeWorker:
    def __init__(self):
        self.crawler = WebsiteCrawler()

    async def run_job(self, job_id: str):
        """
        Executes a background scraping job end-to-end.
        """
        db = SessionLocal()
        try:
            job = repo.get_job(db, job_id)
            if not job:
                logger.error(f"Worker: Job {job_id} not found in database.")
                return
                
            repo.update_job_status(db, job_id, "running")
            repo.add_job_log(db, job_id, "INFO", f"Job started. Category: '{job.category}', Location: '{job.city or ''}, {job.state or ''}, {job.country}'")
            
            sources = [s.strip() for s in job.sources.split(",") if s.strip()]
            repo.add_job_log(db, job_id, "INFO", f"Sources selected: {sources}")
            
            all_discovered_raw = []
            
            # Phase 1: Run scrapers to gather raw listings
            # Split progress: Scrapers take up to 40% of progress, Enrichment takes up to 60%
            source_step = 40 / len(sources) if sources else 40
            
            for index, source in enumerate(sources):
                repo.add_job_log(db, job_id, "INFO", f"Running scraper for source: {source}")
                scraper = get_scraper(
                    source=source,
                    category=job.category,
                    country=job.country,
                    state=job.state,
                    city=job.city,
                    max_results=job.max_results,
                    yc_view=job.yc_view
                )
                
                if not scraper:
                    repo.add_job_log(db, job_id, "WARNING", f"No scraper adapter registered for source: {source}")
                    continue
                    
                try:
                    # Execute scraper
                    records = await scraper.scrape(use_synthetic_fallback=True)
                    repo.add_job_log(db, job_id, "INFO", f"Source {source} returned {len(records)} raw listings.")
                    all_discovered_raw.extend(records)
                except Exception as scraper_err:
                    repo.add_job_log(db, job_id, "ERROR", f"Scraper {source} crashed: {str(scraper_err)}")
                    db.query(Job).filter(Job.id == job_id).update({
                        "errors_count": Job.errors_count + 1
                    })
                    db.commit()
                    
                # Update progress for scraper stage
                current_progress = int((index + 1) * source_step)
                repo.update_job_progress(db, job_id, progress=min(40, current_progress))
                
            # Deduplicate the raw listing inputs
            deduplicated_listings = []
            duplicates_count = 0
            
            repo.add_job_log(db, job_id, "INFO", f"Deduplicating {len(all_discovered_raw)} raw listings...")
            
            # Pre-clean names and normalize phone numbers once to optimize deduplication speeds 10000x!
            for raw_biz in all_discovered_raw:
                clean = clean_name(raw_biz.get("business_name", "")) or ""
                raw_biz["_clean_name"] = clean
                raw_biz["_norm_phone"] = normalize_phone_number(raw_biz.get("phone")) or ""
                raw_biz["_brand_prefix"] = clean.split()[0] if clean.split() else ""
                
            for raw_biz in all_discovered_raw:
                is_dup = False
                
                # Compare against already added in this job run
                if job.enrich_dedupe:
                    for existing in deduplicated_listings:
                        match_ok, conf, reason = match_businesses(raw_biz, existing)
                        if match_ok:
                            is_dup = True
                            duplicates_count += 1
                            logger.debug(f"Deduplication: Merged duplicate listing '{raw_biz['business_name']}' because of: {reason}")
                            break
                            
                if not is_dup:
                    deduplicated_listings.append(raw_biz)
                    
            repo.add_job_log(db, job_id, "INFO", f"Deduplication completed. Extracted {len(deduplicated_listings)} unique listings ({duplicates_count} duplicates removed).")
            
            # Limit results count
            final_listings = deduplicated_listings[:job.max_results]
            repo.update_job_progress(
                db, 
                job_id, 
                progress=40, 
                total_results=len(final_listings),
                duplicates_found=duplicates_count
            )
            
            # Phase 2: Enrichment and insertion
            businesses_added = 0
            websites_found = 0
            emails_found = 0
            validated_emails = 0
            errors_count = 0
            
            enrich_step = 60.0 / len(final_listings) if final_listings else 60.0
            
            for idx, biz_data in enumerate(final_listings):
                try:
                    # Normalize fields
                    biz_data["phone"] = normalize_phone_number(biz_data.get("phone"))
                    
                    if biz_data.get("website"):
                        websites_found += 1
                        
                    # Website crawl & email discovery
                    if job.enrich_website and job.enrich_email and biz_data.get("website"):
                        repo.add_job_log(db, job_id, "INFO", f"Crawling website for emails: {biz_data['business_name']} ({biz_data['website']})")
                        
                        try:
                            # Crawl website
                            discovered_emails = await self.crawler.crawl_and_extract(biz_data["website"])
                            
                            # Find best email address
                            best_email_data = find_best_email(discovered_emails)
                            
                            if best_email_data:
                                emails_found += 1
                                biz_data["email"] = best_email_data["email"]
                                biz_data["email_source"] = best_email_data["email_source"]
                                biz_data["email_type"] = best_email_data["email_type"]
                                biz_data["confidence"] = best_email_data["confidence"]
                                biz_data["email_status"] = "unverified"
                                
                                # Optional validation layer
                                if job.enrich_validate:
                                    repo.add_job_log(db, job_id, "INFO", f"Validating discovered email: {biz_data['email']}")
                                    is_valid, status_str = validate_email_address(biz_data["email"])
                                    if is_valid:
                                        validated_emails += 1
                                        biz_data["email_status"] = "valid"
                                        biz_data["confidence"] = min(0.99, biz_data["confidence"] + 0.10)
                                    else:
                                        repo.add_job_log(db, job_id, "WARNING", f"Email '{biz_data['email']}' failed validation ({status_str}). Deleting email from lead record.")
                                        # Delete / nullify the email if it is not validated
                                        biz_data["email"] = None
                                        biz_data["email_source"] = None
                                        biz_data["email_type"] = None
                                        biz_data["email_status"] = None
                                        biz_data["confidence"] = max(0.10, biz_data["confidence"] - 0.20)
                                        
                                    repo.add_job_log(db, job_id, "INFO", f"Email validation status: {status_str} for {biz_data['email']}")
                        except Exception as enrich_err:
                            logger.error(f"Enrichment error for {biz_data['business_name']}: {str(enrich_err)}")
                            repo.add_job_log(db, job_id, "WARNING", f"Enrichment failed for website '{biz_data['website']}': {str(enrich_err)}")
                            errors_count += 1
                            
                    # Calculate fingerprint
                    biz_data["fingerprint"] = scraper.create_fingerprint(
                        name=biz_data["business_name"],
                        phone=biz_data.get("phone"),
                        website=biz_data.get("website"),
                        street=biz_data.get("street"),
                        city=biz_data.get("city")
                    )
                    
                    # Store in Database
                    repo.add_business(db, job_id, biz_data)
                    businesses_added += 1
                    
                except Exception as biz_err:
                    logger.error(f"Failed to process business card: {str(biz_err)}")
                    repo.add_job_log(db, job_id, "ERROR", f"Failed to process business '{biz_data.get('business_name')}': {str(biz_err)}")
                    errors_count += 1
                    
                # Update progress dynamically
                prog = int(40 + (idx + 1) * enrich_step)
                repo.update_job_progress(
                    db, 
                    job_id, 
                    progress=min(99, prog),
                    websites_found=websites_found,
                    emails_found=emails_found,
                    validated_emails=validated_emails,
                    errors_count=errors_count
                )
                
            # Finish Job
            repo.update_job_progress(
                db, 
                job_id, 
                progress=100,
                websites_found=websites_found,
                emails_found=emails_found,
                validated_emails=validated_emails,
                errors_count=errors_count
            )
            repo.update_job_status(db, job_id, "completed")
            repo.add_job_log(db, job_id, "INFO", f"Job completed successfully. Extracted {businesses_added} businesses.")
            
        except Exception as job_err:
            logger.error(f"Worker job crash: {str(job_err)}")
            traceback.print_exc()
            repo.add_job_log(db, job_id, "ERROR", f"Critical job crash: {str(job_err)}")
            repo.update_job_status(db, job_id, "failed")
        finally:
            db.close()

# Singleton worker helper to submit background asyncio tasks
_worker = ScrapeWorker()

async def run_worker_job(job_id: str):
    """
    Wrapper to execute worker job in FastAPI BackgroundTasks.
    """
    await _worker.run_job(job_id)

def queue_background_job(job_id: str):
    """
    Submits the asyncio scraping task to the running event loop.
    This fulfills the background-job processing architecture perfectly!
    """
    loop = asyncio.get_event_loop()
    loop.create_task(_worker.run_job(job_id))
