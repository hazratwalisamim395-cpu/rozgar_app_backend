from sqlalchemy import Column, Integer, Text
from database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(Text, index=True)
    company = Column(Text, index=True)
    employment_type = Column(Text, index=True)

    location = Column(Text, index=True)
    posted = Column(Text)
    deadline = Column(Text, index=True)

    badge = Column(Text)

    job_url = Column(Text, unique=True, index=True)
    logo_url = Column(Text)

    category = Column(Text, index=True)

    published = Column(Text)
    nationality = Column(Text)
    gender = Column(Text)

    salary = Column(Text)
    contract_duration = Column(Text)

    vacancy_number = Column(Text)
    number_of_jobs = Column(Text)

    education = Column(Text)
    experience = Column(Text)

    about_company = Column(Text)
    job_summary = Column(Text)
    job_requirements = Column(Text)
    submission_guideline = Column(Text)

    application_email = Column(Text)