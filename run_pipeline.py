import os
from database import fetch_job_urls, store_job_page
from scraper import download_job_page, parse_requirements
from resume_parser import load_resume
from resume_generator import generate_resume

RESUME_PATH = os.getenv("RESUME_PATH", "resume.txt")


def main():
    resume_text = load_resume(RESUME_PATH)
    jobs = fetch_job_urls(limit=1)
    for job_id, url in jobs:
        html = download_job_page(url)
        reqs = parse_requirements(html)
        new_resume = generate_resume(resume_text, reqs)
        store_job_page(job_id, html, reqs)
        out_file = f"resume_{job_id}.txt"
        with open(out_file, "w") as f:
            f.write(new_resume)
        print(f"Generated resume for job {job_id} -> {out_file}")


if __name__ == "__main__":
    main()
