from fastapi import APIRouter
from app.models.job_posting import JobPosting
from app.database import get_database
import os

router = APIRouter(prefix="/api/v1/job-posting", tags=["Fiche de poste"])

DEFAULT_FICHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fiche-de-poste.md")

@router.get("", response_model=JobPosting)
async def get_job_posting():
    db = get_database()
    doc = await db.job_postings.find_one({"is_active": True})
    if doc:
        return JobPosting(**doc)
        
    # Initialisation par défaut
    job = JobPosting()
    if os.path.exists(DEFAULT_FICHE_PATH):
        try:
            with open(DEFAULT_FICHE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
                job.description = content
        except Exception:
            pass
            
    await db.job_postings.update_one(
        {"is_active": True},
        {"$set": {**job.model_dump(), "is_active": True}},
        upsert=True
    )
    return job

@router.put("", response_model=JobPosting)
async def update_job_posting(job: JobPosting):
    db = get_database()
    await db.job_postings.update_one(
        {"is_active": True},
        {"$set": {**job.model_dump(), "is_active": True}},
        upsert=True
    )
    return job
