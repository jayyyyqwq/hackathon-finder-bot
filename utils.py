# utils.py
# ---------------------------------------------------------
# Utility functions for Hackathon Finder Bot
# Minimal filtering, no deadline checks
# ---------------------------------------------------------

import json
from pathlib import Path

# ---------------------------------------------------------
# JSON HELPERS
# ---------------------------------------------------------

def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except:
        return {}

# ---------------------------------------------------------
# LIGHT FILTERING (NO DEADLINE LOGIC)
# ---------------------------------------------------------

GOOD_WORDS = [
    "hack",
    "challenge",
    "competition",
    "contest",
    "innovation",
    "fellowship",
    "student challenge",
]

BAD_WORDS = [
    "webinar",
    "bootcamp",
    "workshop",
    "seminar",
    "summit",
    "training",
    "winner announcement",
    "announcement",
]

def pass_filter(title: str):
    t = title.lower()

    # remove obvious noise
    for bad in BAD_WORDS:
        if bad in t:
            return False

    # keep if any good word is in it
    for good in GOOD_WORDS:
        if good in t:
            return True

    return False


def filter_by_light_rules(results):
    """
    Input:
    {
        site: [{title, url}, ...]
    }

    Output:
    Only relevant items, no deadline requirements.
    """
    filtered = {}

    for site, items in results.items():
        clean = []
        for it in items:
            title = it.get("title", "")
            if not title:
                continue

            if pass_filter(title):
                clean.append(it)

        filtered[site] = clean

    return filtered


# ---------------------------------------------------------
# MESSAGE FORMATTING
# ---------------------------------------------------------

def format_item_html(item):
    title = item.get("title", "Untitled")
    url = item.get("url")

    if url:
        return f"• <a href=\"{url}\">{title}</a>"
    else:
        return f"• {title}"


def format_message(results):
    msg = "🔥 <b>Latest Hackathons and Challenges</b>\n\n"

    empty = True

    for site, items in results.items():
        if not items:
            continue

        empty = False
        msg += f"⭐ <b>{site.upper()}</b>\n"

        for it in items[:10]:
            msg += format_item_html(it) + "\n"

        msg += "\n"

    if empty:
        return "😴 No relevant hackathons found right now."

    return msg.strip()
