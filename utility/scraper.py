import re
import requests
from bs4 import BeautifulSoup
from .config import USER_AGENT, BASE_URL

def scrape_fatal_reports():
    """Scrape DGMS Safety Alerts page and return only Fatal Accident Report links."""
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(BASE_URL, headers=headers, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text(" ").split())
        href = a["href"].strip()
        if not href:
            continue
        if not href.startswith("http"):
            href = requests.compat.urljoin(BASE_URL, href)

        # Filter only "Fatal Accident" reports
        if re.search(r"fatal.*accident", text, re.IGNORECASE) or "fatal" in href.lower():
            links.append({"title": text, "url": href})

    return links
