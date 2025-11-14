# utils.py
# ---------------------------------------------------------
# Utility functions for Hackathon Finder Bot
# Handles:
# - JSON load/save
# - Deadline filtering (active/upcoming only)
# - Formatting pretty Telegram messages (HTML)
# ---------------------------------------------------------

import json
from datetime import datetime, date
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
# DEADLINE FILTERING
# ---------------------------------------------------------

def parse_deadline_str(s):
    """
    Convert a string YYYY-MM-DD into date object.
    If invalid, return None.
    """
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except:
        return None

def filter_by_deadline(results):
    """
    Input:
    {
        site1: [ {title, url, deadline}, ... ],
        site2: [ ... ]
    }

    Output:
    Only items where:
        - deadline is None (unknown → keep),
        - or deadline >= TODAY
    """
    today = date.today()

    filtered = {}

    for site, items in results.items():
        good_items = []
        for it in items:
            d = it.get("deadline")

            if not d:
                # No deadline found → keep anyway
                good_items.append(it)
                continue

            deadline = parse_deadline_str(d)
            if deadline and deadline >= today:
                good_items.append(it)

        filtered[site] = good_items

    return filtered


# ---------------------------------------------------------
# MESSAGE FORMATTING (TELEGRAM)
# ---------------------------------------------------------

def format_item_html(item):
    """
    Convert single item dict -> HTML line
    Example:
        • <a href='URL'>TITLE</a> (deadline: YYYY-MM-DD)
    """
    title = item.get("title", "Untitled")
    url = item.get("url", "")
    deadline = item.get("deadline", None)

    line = f"• <a href=\"{url}\">{title}</a>"
    if deadline:
        line += f" <b>(Deadline: {deadline})</b>"
    return line


def format_message(results):
    """
    Convert the entire results dictionary into an HTML Telegram message.

    Input:
    {
        "devpost": [ {...}, {...} ],
        "hackerearth": [ {...} ],
        ...
    }
    """

    msg = "🔥 <b>Latest Hackathons & Challenges</b>\n\n"

    empty = True

    for site, items in results.items():
        if not items:
            continue

        empty = False
        msg += f"⭐ <b>{site.upper()}</b>\n"

        for it in items[:10]:  # show top 10 per site
            msg += format_item_html(it) + "\n"

        msg += "\n"

    if empty:
        return "😴 No active or upcoming hackathons found right now."

    return msg.strip()
