import pandas as pd
import time

from database import SessionLocal, engine, Base
from models import Job


# ==========================================================
# CREATE TABLE
# ==========================================================

Base.metadata.create_all(bind=engine)

def sync_jobs():

    # ==========================================================
    # READ CSV
    # ==========================================================

    df = pd.read_csv("acbar_jobs.csv")

    # ==========================================================
    # REPLACE NaN WITH NONE
    # ==========================================================

    df = df.where(
        pd.notna(df),
        None
    )

    # ==========================================================
    # DATABASE
    # ==========================================================

    db = SessionLocal()

    try:

        added = 0
        skipped = 0

        for _, row in df.iterrows():

            job_url = row.get("Job URL")

            # --------------------------------------------------
            # SKIP WITHOUT URL
            # --------------------------------------------------

            if not job_url:

                skipped += 1
                continue

            # --------------------------------------------------
            # CHECK DUPLICATE
            # --------------------------------------------------

            existing = (
                db.query(Job)
                .filter(
                    Job.job_url == str(job_url)
                )
                .first()
            )

            if existing:

                skipped += 1
                continue

            # --------------------------------------------------
            # CREATE JOB
            # --------------------------------------------------

            job = Job(

                title=row.get("Title"),
                company=row.get("Company"),
                employment_type=row.get("Employment Type"),
                location=row.get("Location"),
                posted=row.get("Posted"),
                deadline=row.get("Deadline"),
                badge=row.get("Badge"),
                job_url=row.get("Job URL"),
                logo_url=row.get("Logo URL"),
                category=row.get("Category"),
                published=row.get("Published"),
                nationality=row.get("Nationality"),
                gender=row.get("Gender"),
                salary=row.get("Salary"),
                contract_duration=row.get("Contract Duration"),
                vacancy_number=row.get("Vacancy Number"),
                number_of_jobs=row.get("Number of Jobs"),
                education=row.get("Education"),
                experience=row.get("Experience"),
                about_company=row.get("About Company"),
                job_summary=row.get("Job Summary"),
                job_requirements=row.get("Job Requirements"),
                submission_guideline=row.get("Submission Guideline"),
                application_email=row.get("Application Email/Form"),
            )

            db.add(job)

            added += 1

        db.commit()

        print(f"Jobs added: {added}")
        print(f"Jobs skipped: {skipped}")

    except Exception as e:

        db.rollback()

        print("Error:", e)

    finally:

        db.close()


# ==========================================================
# RUN EVERY 5 HOURS
# ==========================================================

while True:

    print("===================================")
    print("Starting job database synchronization...")
    print("===================================")
    sync_jobs()
    print("Next synchronization in 5 hours...")

    time.sleep(3 * 60 * 60)


sync_jobs()