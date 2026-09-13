import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time
import os
import re
from urllib.parse import urljoin


# ==========================================================
# SETTINGS
# ==========================================================

csv_file = "acbar_jobs.csv"

base_url = "https://www.acbar.org/en/jobs?page={}"
base_domain = "https://www.acbar.org"

MAX_PAGES = 100
REQUEST_TIMEOUT = 30
SLEEP_TIME = 0.5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


# ==========================================================
# TODAY
# ==========================================================

today_date = datetime.date.today()

print("=" * 70)
print("ACBAR JOB SCRAPER")
print("=" * 70)

print(f"Today's date: {today_date}")


# ==========================================================
# STATISTICS
# ==========================================================

new_count = 0
existing_count = 0
expired_count = 0
error_count = 0
total_cards = 0
pages_scraped = 0


# ==========================================================
# NORMALIZE URL
# ==========================================================
def normalize_url(url):

    if pd.isna(url):
        return None

    url = str(url).strip()

    if not url:
        return None

    return urljoin(
        base_domain,
        url
    ).strip()


# ==========================================================
# LOAD EXISTING CSV
# ==========================================================

if os.path.exists(csv_file):

    try:

        old_df = pd.read_csv(csv_file)

        print(
            f"Existing CSV found: "
            f"{len(old_df)} jobs"
        )

    except Exception as e:

        print(
            f"Error reading CSV: {e}"
        )

        old_df = pd.DataFrame()

else:

    old_df = pd.DataFrame()

    print("No existing CSV found.")


# ==========================================================
# NORMALIZE OLD URLS
# ==========================================================

if (
    not old_df.empty
    and
    "Job URL" in old_df.columns
):

    old_df["Job URL"] = (
        old_df["Job URL"]
        .apply(normalize_url)
    )


# ==========================================================
# REMOVE EXPIRED JOBS FROM OLD CSV
# ==========================================================

if (
    not old_df.empty
    and
    "Deadline" in old_df.columns
):

    old_df["Deadline"] = pd.to_datetime(
        old_df["Deadline"],
        errors="coerce"
    )

    before_count = len(old_df)

    old_df = old_df[
        old_df["Deadline"].isna()
        |
        (
            old_df["Deadline"].dt.date
            >=
            today_date
        )
    ].copy()

    removed_count = (
        before_count
        -
        len(old_df)
    )

    print(
        f"Expired jobs removed from old CSV: "
        f"{removed_count}"
    )

    old_df["Deadline"] = (
        old_df["Deadline"]
        .dt.strftime("%Y-%m-%d")
    )


# ==========================================================
# EXISTING JOB URLS
# ==========================================================

existing_urls = set()

if (
    not old_df.empty
    and
    "Job URL" in old_df.columns
):

    existing_urls = set(
        old_df["Job URL"]
        .dropna()
        .astype(str)
        .str.strip()
    )


print(
    f"Active jobs already in CSV: "
    f"{len(existing_urls)}"
)


# ==========================================================
# NEW JOBS
# ==========================================================

jobs = []


# ==========================================================
# SECTION TEXT FUNCTION
# ==========================================================

def get_section_text(
    soup,
    heading_text
):

    heading = soup.find(
        string=lambda text:
        text
        and
        text.strip()
        == heading_text
    )

    if not heading:
        return None

    parent = heading.parent

    if not parent:
        return None

    section = parent.find_next()

    if not section:
        return None

    text = section.get_text(
        "\n",
        strip=True
    )

    return text if text else None


# ==========================================================
# CONVERT POSTED TEXT TO SORT DATE
# ==========================================================

def get_posted_datetime(value):

    """
    Converts:

        5 hours ago
        2 days ago
        1 week ago
        today
        yesterday

    into an actual datetime for sorting.
    """

    if pd.isna(value):
        return pd.Timestamp.min

    value = str(value).strip().lower()

    now = pd.Timestamp.now()


    # ------------------------------------------------------
    # JUST NOW
    # ------------------------------------------------------

    if "just now" in value:

        return now


    # ------------------------------------------------------
    # TODAY
    # ------------------------------------------------------

    if value == "today":

        return now


    # ------------------------------------------------------
    # MINUTES
    # ------------------------------------------------------

    match = re.search(
        r"(\d+)\s*minute",
        value
    )

    if match:

        minutes = int(
            match.group(1)
        )

        return (
            now
            -
            pd.Timedelta(
                minutes=minutes
            )
        )


    # ------------------------------------------------------
    # HOURS
    # ------------------------------------------------------

    match = re.search(
        r"(\d+)\s*hour",
        value
    )

    if match:

        hours = int(
            match.group(1)
        )

        return (
            now
            -
            pd.Timedelta(
                hours=hours
            )
        )


    # ------------------------------------------------------
    # DAYS
    # ------------------------------------------------------

    match = re.search(
        r"(\d+)\s*day",
        value
    )

    if match:

        days = int(
            match.group(1)
        )

        return (
            now
            -
            pd.Timedelta(
                days=days
            )
        )


    # ------------------------------------------------------
    # WEEKS
    # ------------------------------------------------------

    match = re.search(
        r"(\d+)\s*week",
        value
    )

    if match:

        weeks = int(
            match.group(1)
        )

        return (
            now
            -
            pd.Timedelta(
                weeks=weeks
            )
        )


    # ------------------------------------------------------
    # MONTHS
    # ------------------------------------------------------

    match = re.search(
        r"(\d+)\s*month",
        value
    )

    if match:

        months = int(
            match.group(1)
        )

        return (
            now
            -
            pd.DateOffset(
                months=months
            )
        )


    # ------------------------------------------------------
    # NORMAL DATE
    # ------------------------------------------------------

    parsed = pd.to_datetime(
        value,
        errors="coerce"
    )

    if pd.notna(parsed):

        return parsed


    return pd.Timestamp.min


# ==========================================================
# START PAGINATION
# ==========================================================

page = 1


while page <= MAX_PAGES:

    print()
    print("=" * 70)

    print(
        f"Fetching page {page}..."
    )

    print("=" * 70)


    # ======================================================
    # PAGE URL
    # ======================================================

    url = base_url.format(page)


    # ======================================================
    # REQUEST PAGE
    # ======================================================

    try:

        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS
        )

        response.raise_for_status()

    except requests.RequestException as e:

        error_count += 1

        print(
            f"Error fetching page {page}: {e}"
        )

        break


    # ======================================================
    # BEAUTIFULSOUP
    # ======================================================

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    # ======================================================
    # FIND JOB CARDS
    # ======================================================

    job_cards = soup.find_all(
        "div",
        class_="job-card"
    )


    print(
        f"Found {len(job_cards)} job cards "
        f"on page {page}"
    )


    # ======================================================
    # NO MORE JOBS
    # ======================================================

    if not job_cards:

        print()
        print(
            "No more jobs found."
        )

        print(
            "Pagination finished."
        )

        break


    pages_scraped += 1

    total_cards += len(job_cards)


    # ======================================================
    # LOOP THROUGH JOB CARDS
    # ======================================================

    for job in job_cards:


        # ==================================================
        # TITLE
        # ==================================================

        title_tag = job.find(
            "a",
            class_="job-card__title"
        )

        title = (
            title_tag.get_text(
                " ",
                strip=True
            )
            if title_tag
            else None
        )


        # ==================================================
        # JOB URL
        # ==================================================

        job_url = (
            title_tag.get("href")
            if title_tag
            else None
        )

        if not job_url:

            print(
                f"Skipping job without URL: "
                f"{title}"
            )

            continue


        job_url = normalize_url(
            job_url
        )


        # ==================================================
        # EXISTING JOB?
        # ==================================================

        if job_url in existing_urls:

            existing_count += 1

            print(
                f"Already exists → SKIP: "
                f"{title}"
            )

            continue


        # ==================================================
        # BADGE
        # ==================================================

        badge_tag = job.find(
            "span",
            class_="job-badge"
        )

        badge = (
            badge_tag.get_text(
                " ",
                strip=True
            )
            if badge_tag
            else None
        )


        # ==================================================
        # COMPANY
        # ==================================================

        company_div = job.find(
            "div",
            class_="job-card__company"
        )

        if company_div:

            company_text = (
                company_div.get_text(
                    " ",
                    strip=True
                )
            )

            company = (
                company_text
                .split("•")[0]
                .strip()
            )

        else:

            company = None


        # ==================================================
        # EMPLOYMENT TYPE
        # ==================================================

        employment_type = None

        if company_div:

            company_pills = (
                company_div.find_all(
                    "span",
                    class_="job-pill"
                )
            )

            if company_pills:

                employment_type = (
                    company_pills[0]
                    .get_text(
                        " ",
                        strip=True
                    )
                )


        # ==================================================
        # LOCATION / POSTED / DEADLINE
        # ==================================================

        meta = job.find(
            "div",
            class_="job-card__meta"
        )

        location = None
        posted = None
        deadline = None


        if meta:

            pills = meta.find_all(
                "span",
                class_="job-pill"
            )

            locations = []


            for pill in pills:

                icon = pill.find("i")

                if not icon:
                    continue

                icon_classes = icon.get(
                    "class",
                    []
                )


                # ------------------------------------------
                # LOCATION
                # ------------------------------------------

                if "fa-map-marker" in icon_classes:

                    text = pill.get_text(
                        " ",
                        strip=True
                    )

                    if text:

                        locations.append(
                            text
                        )


                # ------------------------------------------
                # POSTED
                # ------------------------------------------

                elif "fa-clock-o" in icon_classes:

                    posted = pill.get_text(
                        " ",
                        strip=True
                    )


                # ------------------------------------------
                # DEADLINE
                # ------------------------------------------

                elif "fa-calendar" in icon_classes:

                    deadline = pill.get_text(
                        " ",
                        strip=True
                    )


            location = ", ".join(
                locations
            )


        # ==================================================
        # CHECK DEADLINE
        # ==================================================

        if deadline:

            try:

                deadline_date = (
                    datetime.datetime.strptime(
                        deadline,
                        "%Y-%m-%d"
                    ).date()
                )


                if deadline_date < today_date:

                    expired_count += 1

                    print(
                        f"Expired → SKIP: "
                        f"{title} | "
                        f"Deadline: {deadline}"
                    )

                    continue


            except ValueError:

                print(
                    f"Could not parse deadline: "
                    f"{deadline}"
                )


        # ==================================================
        # LOGO
        # ==================================================

        logo_div = job.find(
            "div",
            class_="job-card__logo"
        )

        logo_tag = (
            logo_div.find("img")
            if logo_div
            else None
        )

        logo_url = (
            logo_tag.get("src")
            if logo_tag
            else None
        )

        if logo_url:

            logo_url = urljoin(
                base_domain,
                logo_url
            )


        # ==================================================
        # FETCH DETAIL PAGE
        # ==================================================

        print(
            f"NEW JOB → Fetching details: "
            f"{title}"
        )


        try:

            detail_response = requests.get(
                job_url,
                timeout=REQUEST_TIMEOUT,
                headers=HEADERS
            )

            detail_response.raise_for_status()

        except requests.RequestException as e:

            error_count += 1

            print(
                f"Error fetching detail page: "
                f"{title}"
            )

            print(e)

            continue


        # ==================================================
        # DETAIL SOUP
        # ==================================================

        detail_soup = BeautifulSoup(
            detail_response.text,
            "html.parser"
        )


        # ==================================================
        # DEFAULT VALUES
        # ==================================================

        category = None
        published = None
        nationality = None
        gender = None
        salary = None
        contract_duration = None
        vacancy_number = None
        number_of_jobs = None


        # ==================================================
        # QUICK SUMMARY
        # ==================================================

        quick_summary = detail_soup.find(
            string=lambda text:
            text
            and
            "Quick Summary"
            in text
        )


        if quick_summary:

            parent = quick_summary.parent

            if parent and parent.parent:

                summary_text = (
                    parent.parent.get_text(
                        "\n",
                        strip=True
                    )
                )

                lines = [
                    line.strip()
                    for line
                    in summary_text.split("\n")
                    if line.strip()
                ]


                for i, line in enumerate(lines):

                    if (
                        line == "Category"
                        and
                        i + 1 < len(lines)
                    ):

                        category = lines[i + 1]


                    elif (
                        line == "Published"
                        and
                        i + 1 < len(lines)
                    ):

                        published = lines[i + 1]


                    elif (
                        line == "Nationality"
                        and
                        i + 1 < len(lines)
                    ):

                        nationality = lines[i + 1]


                    elif (
                        line == "Gender"
                        and
                        i + 1 < len(lines)
                    ):

                        gender = lines[i + 1]


                    elif (
                        line == "Salary"
                        and
                        i + 1 < len(lines)
                    ):

                        salary = lines[i + 1]


                    elif (
                        line == "Contract Duration"
                        and
                        i + 1 < len(lines)
                    ):

                        contract_duration = (
                            lines[i + 1]
                        )


                    elif (
                        line == "Vacancy Number"
                        and
                        i + 1 < len(lines)
                    ):

                        vacancy_number = (
                            lines[i + 1]
                        )


                    elif (
                        line == "No of Job"
                        and
                        i + 1 < len(lines)
                    ):

                        number_of_jobs = (
                            lines[i + 1]
                        )


        # ==================================================
        # DETAIL SECTIONS
        # ==================================================

        education = get_section_text(
            detail_soup,
            "Education"
        )

        experience = get_section_text(
            detail_soup,
            "Experience"
        )

        about_company = get_section_text(
            detail_soup,
            "About the Company"
        )

        job_summary = get_section_text(
            detail_soup,
            "Job Summary"
        )

        job_requirements = get_section_text(
            detail_soup,
            "Job Requirements"
        )

        submission_guideline = get_section_text(
            detail_soup,
            "Submission Guideline"
        )


        # ==================================================
        # APPLICATION EMAIL
        # ==================================================

        application_email = None

        email_text = detail_soup.find(
            string=lambda text:
            text
            and
            "Email / Application Form"
            in text
        )

        if email_text:

            email_tag = email_text.parent

            if email_tag:

                application_email = (
                    email_tag.get_text(
                        " ",
                        strip=True
                    )
                )


        # ==================================================
        # SAVE JOB
        # ==================================================

        jobs.append({

            "Title": title,

            "Company": company,

            "Employment Type":
                employment_type,

            "Location": location,

            "Posted": posted,

            "Deadline": deadline,

            "Badge": badge,

            "Job URL": job_url,

            "Logo URL": logo_url,

            "Category": category,

            "Published": published,

            "Nationality": nationality,

            "Gender": gender,

            "Salary": salary,

            "Contract Duration":
                contract_duration,

            "Vacancy Number":
                vacancy_number,

            "Number of Jobs":
                number_of_jobs,

            "Education": education,

            "Experience": experience,

            "About Company":
                about_company,

            "Job Summary":
                job_summary,

            "Job Requirements":
                job_requirements,

            "Submission Guideline":
                submission_guideline,

            "Application Email/Form":
                application_email
        })


        # ==================================================
        # MARK AS SEEN
        # ==================================================

        existing_urls.add(
            job_url
        )

        new_count += 1


        # ==================================================
        # WAIT
        # ==================================================

        time.sleep(
            SLEEP_TIME
        )


    # ======================================================
    # NEXT PAGE
    # ======================================================

    page += 1


# ==========================================================
# CREATE NEW DATAFRAME
# ==========================================================

new_df = pd.DataFrame(
    jobs
)


# ==========================================================
# IMPORTANT:
# SCRAPING IS COMPLETELY FINISHED HERE
# ==========================================================

print()
print("=" * 70)
print("ALL PAGES HAVE BEEN SCRAPED")
print("=" * 70)

print(
    f"Pages scraped: {pages_scraped}"
)

print(
    f"Total job cards found: {total_cards}"
)

print(
    f"New jobs scraped: {new_count}"
)

print(
    f"Existing jobs skipped: {existing_count}"
)

print(
    f"Expired jobs skipped: {expired_count}"
)

print(
    f"Request errors: {error_count}"
)


# ==========================================================
# COMBINE OLD + NEW
# ==========================================================

if (
    not old_df.empty
    and
    not new_df.empty
):

    df = pd.concat(
        [
            old_df,
            new_df
        ],
        ignore_index=True
    )

elif not old_df.empty:

    df = old_df.copy()

else:

    df = new_df.copy()


# ==========================================================
# NORMALIZE ALL URLS
# ==========================================================

if "Job URL" in df.columns:

    df["Job URL"] = (
        df["Job URL"]
        .apply(normalize_url)
    )


# ==========================================================
# REMOVE DUPLICATES
# ==========================================================

if "Job URL" in df.columns:

    before_duplicates = len(df)

    df = df.drop_duplicates(
        subset=["Job URL"],
        keep="first"
    ).copy()

    duplicate_count = (
        before_duplicates
        -
        len(df)
    )

    print(
        f"Duplicate jobs removed: "
        f"{duplicate_count}"
    )


# ==========================================================
# REMOVE ALL EXPIRED JOBS
# ==========================================================

if "Deadline" in df.columns:

    df["Deadline"] = pd.to_datetime(
        df["Deadline"],
        errors="coerce"
    )

    before_expired = len(df)


    # Keep:
    # Deadline is empty
    # OR
    # Deadline is today
    # OR
    # Deadline is in future

    df = df[
        df["Deadline"].isna()
        |
        (
            df["Deadline"]
            >=
            pd.Timestamp.today().normalize()
        )
    ].copy()


    final_expired_count = (
        before_expired
        -
        len(df)
    )

    print(
        f"Final expired jobs removed: "
        f"{final_expired_count}"
    )


# ==========================================================
# CREATE SORT DATE
# ==========================================================

df["_sort_date"] = pd.Timestamp.min


# ==========================================================
# USE PUBLISHED DATE FIRST
# ==========================================================

if "Published" in df.columns:

    published_dates = (
        df["Published"]
        .apply(
            get_posted_datetime
        )
    )

    df["_sort_date"] = (
        published_dates
    )


# ==========================================================
# IF PUBLISHED IS EMPTY,
# USE POSTED
# ==========================================================

if "Posted" in df.columns:

    posted_dates = (
        df["Posted"]
        .apply(
            get_posted_datetime
        )
    )

    df["_sort_date"] = (
        df["_sort_date"]
        .where(
            df["_sort_date"]
            !=
            pd.Timestamp.min,
            posted_dates
        )
    )


# ==========================================================
# NEWEST FIRST
# ==========================================================

df = df.sort_values(
    by="_sort_date",
    ascending=False
).copy()


# ==========================================================
# REMOVE SORT COLUMN
# ==========================================================

df.drop(
    columns=["_sort_date"],
    inplace=True
)


# ==========================================================
# RESET INDEX
# ==========================================================

df.reset_index(
    drop=True,
    inplace=True
)


# ==========================================================
# FORMAT DEADLINE
# ==========================================================

if "Deadline" in df.columns:

    df["Deadline"] = (
        df["Deadline"]
        .dt.strftime("%Y-%m-%d")
    )


# ==========================================================
# SAVE ONLY NOW
# ==========================================================

df.to_csv(
    csv_file,
    index=False,
    encoding="utf-8-sig"
)


# ==========================================================
# FINAL RESULT
# ==========================================================

print()
print("=" * 70)
print("FINAL RESULT")
print("=" * 70)

print(
    f"Total active jobs in CSV: "
    f"{len(df)}"
)

print(
    f"CSV saved successfully: "
    f"{csv_file}"
)


# ==========================================================
# SHOW NEWEST 10
# ==========================================================

print()
print("=" * 70)
print("NEWEST 10 JOBS")
print("=" * 70)

if not df.empty:

    columns_to_show = [
        "Title",
        "Company",
        "Posted",
        "Deadline"
    ]

    available_columns = [
        column
        for column in columns_to_show
        if column in df.columns
    ]

    print(
        df[available_columns]
        .head(10)
        .to_string(index=False)
    )

else:

    print("No active jobs found.")


print()
print("=" * 70)
print("DONE")
print("=" * 70)