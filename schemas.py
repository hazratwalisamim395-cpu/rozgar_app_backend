from typing import Optional

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):

    id: int

    title: Optional[str] = None
    company: Optional[str] = None
    employment_type: Optional[str] = None

    location: Optional[str] = None
    posted: Optional[str] = None
    deadline: Optional[str] = None

    badge: Optional[str] = None

    job_url: Optional[str] = None
    logo_url: Optional[str] = None

    category: Optional[str] = None

    published: Optional[str] = None
    nationality: Optional[str] = None
    gender: Optional[str] = None

    salary: Optional[str] = None
    contract_duration: Optional[str] = None

    vacancy_number: Optional[str] = None
    number_of_jobs: Optional[str] = None

    education: Optional[str] = None
    experience: Optional[str] = None

    about_company: Optional[str] = None
    job_summary: Optional[str] = None
    job_requirements: Optional[str] = None
    submission_guideline: Optional[str] = None

    application_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):

    jobs: list[JobResponse]

    page: int
    limit: int

    total: int
    total_pages: int