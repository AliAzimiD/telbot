import os
from contextlib import contextmanager
import psycopg2
from psycopg2.pool import SimpleConnectionPool

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

pool = SimpleConnectionPool(minconn=1, maxconn=5, dsn=DATABASE_URL)

@contextmanager
def get_conn():
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)

def fetch_job_urls(limit=10):
    """Return a list of (id, url) tuples from the jobs table."""
    query = "SELECT id, url FROM jobs WHERE url IS NOT NULL LIMIT %s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            return cur.fetchall()

def store_job_page(job_id, html, requirements_text):
    """Store downloaded HTML and extracted requirements for a job."""
    query = "UPDATE jobs SET page_html=%s, requirements=%s WHERE id=%s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (html, requirements_text, job_id))
            conn.commit()
