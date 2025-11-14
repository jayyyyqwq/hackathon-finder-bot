# scrapers.py
# ---------------------------------------------------------
# This file collects ALL scrapers (Govt + Corporate + News)
# Each scraper returns a list of dicts:
# { "title": "...", "url": "...", "deadline": "YYYY-MM-DD" or None }
# ---------------------------------------------------------

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

HEADERS = {"User-Agent": "Mozilla/5.0 HackFinder/6.0"}

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def fetch_html(url):
    try:
        return requests.get(url, headers=HEADERS, timeout=15).text
    except:
        return ""

def clean(text):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = " ".join(text.split())
    return text

def extract_deadline_from_text(text):
    """
    Try to extract a date in formats like:
    - 12 Jan 2025
    - Jan 12, 2025
    - 2025-01-22
    - 01/12/2025
    If nothing found -> return None
    """
    if not text:
        return None

    patterns = [
        r"(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})",  # 12 Jan 2025
        r"([A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})", # Jan 12, 2025
        r"(\d{4}-\d{2}-\d{2})",                # 2025-01-22
        r"(\d{1,2}/\d{1,2}/\d{4})"             # 01/12/2025
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            date_str = m.group(1)
            try:
                return str(parse_any_date(date_str))
            except:
                pass

    return None

def parse_any_date(s):
    """
    Try multiple formats until one matches.
    Returns a datetime.date object.
    """
    fmts = [
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y"
    ]
    for f in fmts:
        try:
            return datetime.strptime(s, f).date()
        except:
            pass
    raise ValueError("Unknown date format: " + s)


# ---------------------------------------------------------
# SCRAPER TEMPLATE
# ---------------------------------------------------------

def make_item(title, url, deadline=None):
    return {
        "title": clean(title),
        "url": url,
        "deadline": deadline
    }

# ---------------------------------------------------------
# A) GOVERNMENT SOURCES
# ---------------------------------------------------------

# ---- MyGov ----
def scrape_mygov():
    url = "https://www.mygov.in/homepage/"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for a in soup.select("a"):
        t = clean(a.get_text())
        if "challenge" in t.lower() or "hackathon" in t.lower():
            items.append(make_item(t, a.get("href", "")))
    return items


# ---- MeitY ----
def scrape_meity():
    url = "https://www.meity.gov.in/press-releases"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for a in soup.select("a"):
        t = clean(a.get_text())
        if any(k in t.lower() for k in ["challenge", "hackathon", "innovation"]):
            items.append(make_item(t, "https://www.meity.gov.in" + a.get("href", "")))
    return items


# ---- Digital India ----
def scrape_digital_india():
    url = "https://www.digitalindia.gov.in/news"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for a in soup.select("a"):
        t = clean(a.get_text())
        if "hackathon" in t.lower():
            items.append(make_item(t, "https://www.digitalindia.gov.in" + a.get("href", "")))
    return items


# ---- RBI Press ----
def scrape_rbi():
    url = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for a in soup.select("a"):
        t = clean(a.get_text())
        if "harbinger" in t.lower() or "hackathon" in t.lower():
            items.append(make_item(t, "https://www.rbi.org.in" + a.get("href", "")))
    return items


# ---- ISRO ----
def scrape_isro():
    url = "https://www.isro.gov.in/Updates.html"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for a in soup.select("a"):
        t = clean(a.get_text())
        if any(k in t.lower() for k in ["hackathon", "challenge"]):
            items.append(make_item(t, "https://www.isro.gov.in" + a.get("href", "")))
    return items


# ---- NIC ----
def scrape_nic():
    url = "https://www.nic.in/news/"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for h in soup.select("h2, h3"):
        t = clean(h.get_text())
        if "challenge" in t.lower() or "hackathon" in t.lower():
            items.append(make_item(t, url))
    return items


# ---------------------------------------------------------
# B) CORPORATE / TECH
# ---------------------------------------------------------

# ---- NVIDIA ----
def scrape_nvidia():
    url = "https://developer.nvidia.com/community/events"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for h in soup.select("h3, h2"):
        t = clean(h.get_text())
        if "challenge" in t.lower() or "hackathon" in t.lower():
            items.append(make_item(t, url))
    return items


# ---- Meta ----
def scrape_meta():
    url = "https://developers.facebook.com/blog/"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for h in soup.select("h2"):
        t = clean(h.get_text())
        if "challenge" in t.lower() or "hackathon" in t.lower():
            items.append(make_item(t, url))
    return items


# ---- Google Developer ----
def scrape_google_dev():
    url = "https://developers.google.com/events"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for a in soup.select("a"):
        t = clean(a.get_text())
        if any(k in t.lower() for k in ["challenge", "hackathon"]):
            items.append(make_item(t, "https://developers.google.com" + a.get("href", "")))
    return items


# ---- Microsoft ----
def scrape_microsoft():
    url = "https://developer.microsoft.com/en-us/events/"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for h in soup.select("h3, h2"):
        t = clean(h.get_text())
        if "challenge" in t.lower() or "hackathon" in t.lower():
            items.append(make_item(t, url))
    return items


# ---- Apple ----
def scrape_apple():
    url = "https://developer.apple.com/news/"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for h in soup.select("h2, h3"):
        t = clean(h.get_text())
        if "challenge" in t.lower():
            items.append(make_item(t, url))
    return items


# ---- AWS ----
def scrape_aws():
    url = "https://aws.amazon.com/events/"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for h in soup.select("h2, h3"):
        t = clean(h.get_text())
        if any(k in t.lower() for k in ["challenge", "hackathon"]):
            items.append(make_item(t, url))
    return items


# ---- Kaggle ----
def scrape_kaggle():
    url = "https://www.kaggle.com/competitions"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for link in soup.select("a.sc-bYoBruce"):
        t = clean(link.get_text())
        if t:
            items.append(make_item(t, "https://www.kaggle.com" + link.get("href", "")))
    return items


# ---- AIcrowd ----
def scrape_aicrowd():
    url = "https://www.aicrowd.com/challenges"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for a in soup.select("a.challenge-list-item__link"):
        t = clean(a.get("title", ""))
        if t:
            items.append(make_item(t, "https://www.aicrowd.com" + a.get("href", "")))
    return items


# ---- Devfolio ----
def scrape_devfolio():
    url = "https://devfolio.co/hackathons"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for h in soup.select("h3"):
        t = clean(h.get_text())
        if "hackathon" in t.lower():
            items.append(make_item(t, url))
    return items


# ---------------------------------------------------------
# C) Google News
# ---------------------------------------------------------

def scrape_google_news():
    url = "https://news.google.com/search?q=hackathon&hl=en-IN&gl=IN&ceid=IN:en"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for h in soup.select("h3"):
        t = clean(h.get_text())
        if "hackathon" in t.lower() or "challenge" in t.lower():
            items.append(make_item(t, url))
    return items


# ---------------------------------------------------------
# MASTER SCRAPER
# ---------------------------------------------------------

SITES_INFO = {
    "mygov": scrape_mygov,
    "meity": scrape_meity,
    "digital_india": scrape_digital_india,
    "rbi": scrape_rbi,
    "isro": scrape_isro,
    "nic": scrape_nic,
    "nvidia": scrape_nvidia,
    "meta": scrape_meta,
    "google_dev": scrape_google_dev,
    "microsoft": scrape_microsoft,
    "apple": scrape_apple,
    "aws": scrape_aws,
    "kaggle": scrape_kaggle,
    "aicrowd": scrape_aicrowd,
    "devfolio": scrape_devfolio,
    "google_news": scrape_google_news,
}


def scrape_all():
    all_results = {}
    for name, fn in SITES_INFO.items():
        try:
            items = fn()
        except Exception as ex:
            print(f"[ERROR] scraper {name} → {ex}")
            items = []
        all_results[name] = items
    return all_results
