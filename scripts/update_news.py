
import datetime as dt
import html
import json
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]

FEEDS = [
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("France 24", "https://www.france24.com/fr/rss"),
]

def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(value.split())

def fetch_feed(source, url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "DailyWidgets/1.0"}
    )

    with urllib.request.urlopen(request, timeout=18) as response:
        root = ET.fromstring(response.read())

    results = []

    for item in root.findall("./channel/item")[:12]:
        title = clean_text(item.findtext("title"))
        link = (item.findtext("link") or "").strip()
        date = (item.findtext("pubDate") or "").strip()

        description = clean_text(
            item.findtext("description")
        )

        if not title or not link:
            continue

        try:
            published = parsedate_to_datetime(date)
            published = published.astimezone(
                dt.timezone.utc
            ).isoformat()
        except (ValueError, TypeError, IndexError):
            published = None

        if description == title:
            description = ""

        results.append({
            "title": title,
            "source": source,
            "url": link,
            "published_at": published,
            "summary": description[:350]
        })

    return results

def main():
    now = dt.datetime.now(dt.timezone.utc)
    headlines = []
    errors = []

    for source, url in FEEDS:
        try:
            headlines.extend(fetch_feed(source, url))
        except Exception as exc:
            errors.append(
                f"{source}: {type(exc).__name__}"
            )

    if not headlines:
        raise RuntimeError(
            "No RSS headlines retrieved: " +
            ", ".join(errors)
        )

    headlines.sort(
        key=lambda item: item["published_at"] or "",
        reverse=True
    )

    unique = []
    seen = set()

    for item in headlines:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    previous = {}

    target = ROOT / "data" / "news.json"

    if target.exists():
        try:
            previous = json.loads(
                target.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            previous = {}

    previous = {}

    target = ROOT / "data" / "news.json"

    if target.exists():
        try:
            previous = json.loads(
                target.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            previous = {}

    output = {
        "title": "The Morning Brief",
        "status": "rss_ready",
        "updated_at": now.isoformat(),
        "headlines": unique[:15],
        "quiz": previous.get("quiz", []),

"quiz_updated_at": previous.get("quiz_updated_at"),

"debrief": previous.get("debrief", ""),
        "concept": {
            "title": "",
            "explanation": ""
        },
        "feed_errors": errors
    }

    target = ROOT / "data" / "news.json"
    target.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    target.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print(
        f"Saved {len(output['headlines'])} headlines"
    )

if __name__ == "__main__":
    main()
