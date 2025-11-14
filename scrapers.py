# scrapers.py
# Rewritten scrapers using RSS / JSON / static HTML endpoints only
# Fixed URL normalization, dedupe and safer parsing
# Returns for each site a list of dicts: { "title": "...", "url": "..." }

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HackFinder/1.0)"}
REQUEST_TIMEOUT = 15

def fetch_text(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[fetch_text] failed {url} -> {e}")
        return ""

def fetch_json(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[fetch_json] failed {url} -> {e}")
        return None

# normalize a url-like string: extract first http(s)://... token, otherwise return empty
_http_re = re.compile(r"https?://[^\s'\"<>]+", flags=re.IGNORECASE)

def normalize_url(raw, base=None):
    """
    Clean and normalize URL strings.
    - If `raw` contains multiple links, pick the first sensible one.
    - If `raw` is relative and base is provided, join it.
    - If nothing valid, return empty string.
    """
    if not raw:
        return ""
    raw = raw.strip()

    # If string contains an http(s) URL inside, extract it.
    m = _http_re.search(raw)
    if m:
        url = m.group(0)
        # strip trailing punctuation
        url = url.rstrip('.,;:)"\'')
        return url

    # If it looks like a relative path and base is provided
    if base and not raw.startswith("http") and raw.startswith("/"):
        try:
            return urljoin(base, raw)
        except:
            return ""

    # otherwise if it's already an absolute url-like (rare)
    if raw.startswith("http"):
        return raw

    return ""

def parse_rss(url, limit=40):
    """
    Generic RSS/Atom parser. Returns list of (title, link)
    Tries to extract link from <link>, and if that is missing, tries <guid> or content.
    """
    text = fetch_text(url)
    if not text:
        return []

    soup = BeautifulSoup(text, "xml")
    items = []

    # Try <item> (RSS)
    for node in soup.find_all("item")[:limit]:
        title_node = node.find("title")
        link_node = node.find("link")
        guid_node = node.find("guid")
        # sometimes <link> is a full tag with url inside text
        link = None
        if link_node:
            link = (link_node.get_text(strip=True) or link_node.get("href") or None)
        if not link and guid_node:
            link = (guid_node.get_text(strip=True) or guid_node.get("href") or None)
        title = title_node.get_text(strip=True) if title_node else None

        # fallback: try to find any http in the raw node text
        if not link:
            raw_text = str(node)
            link = normalize_url(raw_text)

        if title:
            link = normalize_url(link, base=url) or ""
            items.append((title, link or url))

    # If none, try Atom <entry>
    if not items:
        for node in soup.find_all("entry")[:limit]:
            title_node = node.find("title")
            link_node = node.find("link")
            title = title_node.get_text(strip=True) if title_node else None
            link = None
            if link_node and link_node.has_attr("href"):
                link = link_node["href"]
            else:
                # fallback: extract any http inside entry
                link = normalize_url(str(node))
            if title:
                link = normalize_url(link, base=url) or ""
                items.append((title, link or url))

    return items

def unique_items(items):
    """
    Input: list of (title, url) tuples
    Output: list of dicts with normalized unique title+url order preserved
    """
    seen = set()
    out = []
    for t, u in items:
        t_norm = (t or "").strip()
        u_norm = normalize_url(u or "")
        key = (t_norm.lower(), u_norm.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append({"title": t_norm, "url": u_norm})
    return out

# -----------------------------
# Government / official RSS
# -----------------------------

def scrape_mygov():
    url = "https://www.mygov.in/challenges/feed/"
    items = parse_rss(url)
    return unique_items(items)

def scrape_digital_india():
    url = "https://www.digitalindia.gov.in/rss.xml"
    items = parse_rss(url)
    return unique_items(items)

def scrape_isro():
    url = "https://www.isro.gov.in/press-release/feed"
    items = parse_rss(url)
    return unique_items(items)

def scrape_rbi():
    url = "https://www.rbi.org.in/scripts/BS_PressReleaseRSS.xml"
    items = parse_rss(url)
    return unique_items(items)

def scrape_meity():
    base = "https://www.meity.gov.in"
    url = f"{base}/press-releases"
    text = fetch_text(url)
    if not text:
        return []
    soup = BeautifulSoup(text, "lxml")
    found = []
    for a in soup.select("a"):
        t = a.get_text(" ", strip=True)
        href = a.get("href") or ""
        if not t:
            continue
        low = t.lower()
        if any(k in low for k in ("hackathon", "challenge", "innovation", "competition", "contest")):
            link = normalize_url(href, base=base) or urljoin(base, href)
            found.append((t, link))
    return unique_items(found)

def scrape_nic():
    url = "https://www.nic.in/news/"
    text = fetch_text(url)
    if not text:
        return []
    soup = BeautifulSoup(text, "lxml")
    found = []
    for tag in soup.select("h2, h3, a"):
        t = tag.get_text(" ", strip=True)
        if not t:
            continue
        low = t.lower()
        if any(k in low for k in ("hackathon", "challenge", "competition", "contest")):
            href = tag.get("href") or ""
            link = normalize_url(href, base=url) or "https://www.nic.in/news/"
            found.append((t, link))
    return unique_items(found)

# -----------------------------
# Corporate / Tech (RSS / JSON / static)
# -----------------------------

def scrape_nvidia():
    # Try JSON endpoint first (best-effort)
    json_url = "https://developer.nvidia.com/events.json"
    data = fetch_json(json_url)
    items = []
    if data and isinstance(data, dict):
        events = data.get("events") or data.get("data") or data.get("items") or []
        for ev in events[:40]:
            title = ev.get("title") or ev.get("name") or ev.get("headline") or None
            link = ev.get("url") or ev.get("link") or ev.get("href") or None
            if title:
                link = normalize_url(link, base="https://developer.nvidia.com")
                items.append((title, link))
    # fallback to simple page scrape
    if not items:
        page = fetch_text("https://developer.nvidia.com/community/events")
        soup = BeautifulSoup(page, "lxml")
        for h in soup.select("h3, h2, .event-title, .views-field-title a")[:40]:
            title = h.get_text(" ", strip=True)
            href = h.get("href") or ""
            link = normalize_url(href, base="https://developer.nvidia.com")
            if title:
                items.append((title, link))
    return unique_items(items)

def scrape_meta():
    url = "https://developers.facebook.com/blog/feed"
    items = parse_rss(url)
    return unique_items(items)

def scrape_google_dev():
    # Google Developers events RSS
    url = "https://developers.google.com/events/rss.xml"
    items = parse_rss(url)
    # normalize links that were previously malformed (some feeds have hrefs embedded)
    normalized = []
    for title, link in items:
        link = normalize_url(link, base="https://developers.google.com")
        normalized.append((title, link))
    return unique_items(normalized)

def scrape_microsoft():
    url = "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board_id=DeveloperCommunity"
    items = parse_rss(url)
    return unique_items(items)

def scrape_apple():
    url = "https://developer.apple.com/news/releases/rss/releases.rss"
    items = parse_rss(url)
    return unique_items(items)

def scrape_aws():
    url = "https://aws.amazon.com/events/feed/"
    items = parse_rss(url)
    return unique_items(items)

# -----------------------------
# Platforms and competitions
# -----------------------------

def scrape_kaggle():
    base = "https://www.kaggle.com"
    url = f"{base}/competitions"
    text = fetch_text(url)
    if not text:
        return []
    soup = BeautifulSoup(text, "lxml")
    found = []
    # look for anchors with /c/ prefix
    for a in soup.select("a[href*='/c/']")[:120]:
        t = a.get_text(" ", strip=True)
        href = a.get("href")
        if t and href:
            link = normalize_url(href, base=base) or urljoin(base, href)
            found.append((t, link))
    return unique_items(found)

def scrape_aicrowd():
    json_url = "https://www.aicrowd.com/challenges.json"
    data = fetch_json(json_url)
    items = []
    if data and isinstance(data, dict):
        challenges = data.get("challenges") or data.get("data") or []
        for ch in challenges[:60]:
            title = ch.get("title") or ch.get("name") or None
            link = ch.get("url") or ch.get("permalink") or None
            if title:
                link = normalize_url(link, base="https://www.aicrowd.com")
                items.append((title, link))
    if not items:
        page = fetch_text("https://www.aicrowd.com/challenges")
        soup = BeautifulSoup(page, "lxml")
        for a in soup.select("a[href*='/challenges/']")[:60]:
            t = a.get("title") or a.get_text(" ", strip=True)
            href = a.get("href")
            link = normalize_url(href, base="https://www.aicrowd.com")
            if t:
                items.append((t, link))
    return unique_items(items)

def scrape_devfolio():
    json_url = "https://devfolio.co/api/hackathons"
    data = fetch_json(json_url)
    items = []
    if data and isinstance(data, dict):
        list_h = data.get("data") or data.get("hackathons") or data.get("hackathon") or []
        for h in list_h[:60]:
            title = h.get("title") or h.get("name") or None
            link = h.get("url") or h.get("external_url") or None
            if title:
                link = normalize_url(link, base="https://devfolio.co")
                items.append((title, link))
    if not items:
        page = fetch_text("https://devfolio.co/hackathons")
        soup = BeautifulSoup(page, "lxml")
        for h in soup.select("h3, a"):
            t = h.get_text(" ", strip=True)
            href = h.get("href") or ""
            if t and "hackathon" in t.lower():
                link = normalize_url(href, base="https://devfolio.co")
                items.append((t, link))
    return unique_items(items)

# -----------------------------
# News (Google News RSS)
# -----------------------------

def scrape_google_news():
    url = "https://news.google.com/rss/search?q=hackathon"
    items = parse_rss(url)
    return unique_items(items)

# -----------------------------
# Master mapping
# -----------------------------

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
    results = {}
    for name, fn in SITES_INFO.items():
        try:
            data = fn() or []
        except Exception as e:
            print(f"[scrape_all] error in {name}: {e}")
            data = []
        # ensure list of dicts with title/url
        cleaned = []
        for it in data:
            if not isinstance(it, dict):
                # safety: if returned as tuple (title,url) convert
                if isinstance(it, tuple) and len(it) >= 2:
                    title = (it[0] or "").strip()
                    url = normalize_url(it[1] or "")
                else:
                    continue
                if title:
                    cleaned.append({"title": title, "url": url})
            else:
                title = (it.get("title") or "").strip()
                url = normalize_url(it.get("url") or "")
                if title:
                    cleaned.append({"title": title, "url": url})
        # final dedupe pass (title+url)
        final = []
        seen = set()
        for it in cleaned:
            key = (it["title"].lower(), (it["url"] or "").lower())
            if key in seen:
                continue
            seen.add(key)
            final.append(it)
        results[name] = final
        time.sleep(0.15)
    return results
