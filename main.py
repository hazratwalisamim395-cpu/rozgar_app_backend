from dataclasses import Field
from datetime import datetime, timedelta, timezone
from math import ceil
from typing import List, Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from openai import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from database import engine, get_db, Base
from models import Job
from schemas import JobResponse, JobListResponse
from recommendation import RecommendationEngine

# ==========================================================
# CREATE DATABASE TABLES
# ==========================================================

Base.metadata.create_all(bind=engine)


# ==========================================================
# FASTAPI APP
# ==========================================================

app = FastAPI(
    title="Rozgar API",
    description="Job search API for Rozgar",
    version="1.0.0",
)


# ==========================================================
# HOME
# ==========================================================

@app.get("/")
def home():
    return {
        "message": "Welcome to Rozgar API",
        "version": "1.0.0",
        "status": "running",
    }


# ==========================================================
# GET ALL JOBS
# SEARCH + FILTER + SORT + PAGINATION
# ==========================================================

@app.get(
    "/api/jobs",
    response_model=JobListResponse,
)
def get_jobs(

    # ------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------

    q: Optional[str] = Query(
        default=None,
        description="Search jobs by title, company, skills, education, experience, etc."
    ),

    # ------------------------------------------------------
    # FILTERS
    # ------------------------------------------------------

    location: Optional[str] = Query(
        default=None
    ),

    employment_type: Optional[str] = Query(
        default=None
    ),

    category: Optional[str] = Query(
        default=None
    ),

    nationality: Optional[str] = Query(
        default=None
    ),

    gender: Optional[str] = Query(
        default=None
    ),

    # ------------------------------------------------------
    # SORT
    # ------------------------------------------------------

    sort: str = Query(
        default="newest",
        description="newest, oldest"
    ),

    # ------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------

    page: int = Query(
        default=1,
        ge=1
    ),

    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),

    db: Session = Depends(get_db),
):

    # ======================================================
    # BASE QUERY
    # ======================================================

    query = db.query(Job)


    # ======================================================
    # SEARCH
    # ======================================================

    if q:

        search = f"%{q.strip()}%"

        query = query.filter(
            or_(
                Job.title.ilike(search),
                Job.company.ilike(search),
                Job.location.ilike(search),
                Job.category.ilike(search),
                Job.education.ilike(search),
                Job.experience.ilike(search),
                Job.about_company.ilike(search),
                Job.job_summary.ilike(search),
                Job.job_requirements.ilike(search),
                Job.submission_guideline.ilike(search),
                Job.salary.ilike(search),
                Job.contract_duration.ilike(search),
                Job.nationality.ilike(search),
                Job.gender.ilike(search),
            )
        )


    # ======================================================
    # LOCATION FILTER
    # ======================================================

    if location:

        query = query.filter(
            Job.location.ilike(
                f"%{location.strip()}%"
            )
        )


    # ======================================================
    # EMPLOYMENT TYPE FILTER
    # ======================================================

    if employment_type:

        query = query.filter(
            Job.employment_type.ilike(
                f"%{employment_type.strip()}%"
            )
        )


    # ======================================================
    # CATEGORY FILTER
    # ======================================================

    if category:

        query = query.filter(
            Job.category.ilike(
                f"%{category.strip()}%"
            )
        )


    # ======================================================
    # NATIONALITY FILTER
    # ======================================================

    if nationality:

        query = query.filter(
            Job.nationality.ilike(
                f"%{nationality.strip()}%"
            )
        )


    # ======================================================
    # GENDER FILTER
    # ======================================================

    if gender:

        query = query.filter(
            Job.gender.ilike(
                f"%{gender.strip()}%"
            )
        )


    # ======================================================
    # TOTAL BEFORE PAGINATION
    # ======================================================

    total = query.count()


    # ======================================================
    # SORTING
    # ======================================================

    if sort == "oldest":

        query = query.order_by(
            Job.id.asc()
        )

    elif sort == "deadline":

        query = query.order_by(
            Job.deadline.asc()
        )

    else:

        # newest
        query = query.order_by(
            Job.id.desc()
        )


    # ======================================================
    # PAGINATION
    # ======================================================

    offset = (page - 1) * limit

    jobs = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )


    # ======================================================
    # TOTAL PAGES
    # ======================================================

    total_pages = ceil(
        total / limit
    ) if total else 0


    # ======================================================
    # RESPONSE
    # ======================================================

    return {
        "jobs": jobs,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
    }

# ==========================================================
# GET SINGLE JOB
# ==========================================================

@app.get(
    "/api/jobs/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):

    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


# ==========================================================
# FEATURED JOBS
# ==========================================================

@app.get(
    "/api/jobs/featured",
    response_model=list[JobResponse],
)
def get_featured_jobs(
    limit: int = Query(
        default=10,
        ge=1,
        le=50
    ),
    db: Session = Depends(get_db),
):

    jobs = (
        db.query(Job)
        .filter(
            Job.badge.isnot(None)
        )
        .filter(
            Job.badge.ilike("%featured%")
        )
        .order_by(
            Job.id.desc()
        )
        .limit(limit)
        .all()
    )

    return jobs


# ==========================================================
# CATEGORIES
# ==========================================================

@app.get("/api/categories")
def get_categories(
    db: Session = Depends(get_db),
):

    results = (
        db.query(
            Job.category,
            func.count(Job.id).label("count")
        )
        .filter(
            Job.category.isnot(None)
        )
        .group_by(
            Job.category
        )
        .order_by(
            func.count(Job.id).desc()
        )
        .all()
    )

    return [
        {
            "name": category,
            "count": count,
        }
        for category, count in results
    ]


# ==========================================================
# LOCATIONS
# ==========================================================

@app.get("/api/locations")
def get_locations(
    db: Session = Depends(get_db),
):

    results = (
        db.query(
            Job.location,
            func.count(Job.id).label("count")
        )
        .filter(
            Job.location.isnot(None)
        )
        .group_by(
            Job.location
        )
        .order_by(
            func.count(Job.id).desc()
        )
        .all()
    )

    return [
        {
            "name": location,
            "count": count,
        }
        for location, count in results
    ]


# ==========================================================
# EMPLOYMENT TYPES
# ==========================================================

@app.get("/api/employment-types")
def get_employment_types(
    db: Session = Depends(get_db),
):

    results = (
        db.query(
            Job.employment_type,
            func.count(Job.id).label("count")
        )
        .filter(
            Job.employment_type.isnot(None)
        )
        .group_by(
            Job.employment_type
        )
        .order_by(
            func.count(Job.id).desc()
        )
        .all()
    )

    return [
        {
            "name": employment_type,
            "count": count,
        }
        for employment_type, count in results
    ]


# ==========================================================
# JOB STATISTICS
# ==========================================================

@app.get("/api/statistics")
def get_statistics(
    db: Session = Depends(get_db),
):

    total_jobs = db.query(Job).count()

    total_companies = (
        db.query(
            func.count(
                func.distinct(Job.company)
            )
        )
        .scalar()
    )

    total_categories = (
        db.query(
            func.count(
                func.distinct(Job.category)
            )
        )
        .scalar()
    )

    total_locations = (
        db.query(
            func.count(
                func.distinct(Job.location)
            )
        )
        .scalar()
    )

    return {
        "total_jobs": total_jobs,
        "total_companies": total_companies,
        "total_categories": total_categories,
        "total_locations": total_locations,
    }


class UserProfile(BaseModel):

    education: Optional[str] = ""

    skills: List[str] = Field(
        default_factory=list
    )

    experience: Optional[str] = ""

    category: Optional[str] = ""

    location: Optional[str] = ""

    employment_type: Optional[str] = ""

    top_n: int = Field(
        default=10,
        ge=1,
        le=50
    )

# ==========================================================
# RECOMMENDATION ENDPOINT
# ==========================================================

@app.post("/api/recommend")
def recommend_jobs(profile: UserProfile):

    # ------------------------------------------------------
    # Create user profile text
    # ------------------------------------------------------

    profile_parts = []

    if profile.education:
        profile_parts.append(
            f"Education: {profile.education}"
        )

    if profile.skills:

        profile_parts.append(
            "Skills: " + ", ".join(profile.skills)
        )

    if profile.experience:
        profile_parts.append(
            f"Experience: {profile.experience}"
        )

    if profile.category:
        profile_parts.append(
            f"Category: {profile.category}"
        )

    if profile.location:
        profile_parts.append(
            f"Location: {profile.location}"
        )

    if profile.employment_type:
        profile_parts.append(
            f"Employment Type: {profile.employment_type}"
        )


    # ------------------------------------------------------
    # Combine everything
    # ------------------------------------------------------

    user_profile = " ".join(profile_parts)


    # ------------------------------------------------------
    # Check empty profile
    # ------------------------------------------------------

    if not user_profile.strip():

        raise HTTPException(
            status_code=400,
            detail="User profile is empty."
        )


    # ------------------------------------------------------
    # Get recommendations
    # ------------------------------------------------------

    recommendations = RecommendationEngine.recommend(
        user_profile=user_profile,
        top_n=profile.top_n
    )


    # ------------------------------------------------------
    # Return response
    # ------------------------------------------------------

    return {
        "success": True,
        "count": len(recommendations),
        "recommendations": recommendations
    }