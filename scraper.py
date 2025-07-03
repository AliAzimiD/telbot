import requests
from bs4 import BeautifulSoup
from typing import Tuple

HEADERS = {"User-Agent": "Mozilla/5.0"}

def download_job_page(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.text

def parse_requirements(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Simple heuristic: extract bullet lists under sections containing 'requirement'
    sections = soup.find_all(text=lambda t: t and 'require' in t.lower())
    if not sections:
        return ""
    # Gather sibling lists or paragraphs
    requirements = []
    for s in sections:
        parent = s.parent
        ul = parent.find_next("ul")
        if ul:
            items = [li.get_text(" ", strip=True) for li in ul.find_all("li")]
            requirements.extend(items)
    return "\n".join(requirements)
