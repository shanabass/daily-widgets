import datetime as dt
import json
import pathlib
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
FEEDS = [
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("France 24", "https://www.france24.com/fr/rss"),
]

def fetch_feed(source, url):
    request = urllib.request.Request(url, headers={"User-Agent": "DailyWidgets/1.0"})
    with urllib.request.urlopen(request, timeout=18) as response:
        root = ET.fromstring(response.read())
    results = []
    for item in root.findall("./channel/item")[:12]:
        title = " ".join((item.findtext("title") or "").split())
        link = (item.findtext("link") or "").strip()
        date = (item.findtext("pubDate") or "").strip()
        if not title or not link:
            continue
        try:
            published = parsedate_to_datetime(date).astimezone(dt.timezone.utc).isoformat()
        except (ValueError, TypeError, IndexError):
            published = None
        results.append({"title": title, "source": source, "url": link, "published_at": published})
    return results

def main():
    now = dt.datetime.now(dt.timezone.utc)
    headlines = []
    errors = []
    for source, url in FEEDS:
        try:
            headlines.extend(fetch_feed(source, url))
        except Exception as exc:
            errors.append(f"{source}: {type(exc).__name__}")
    if not headlines:
        raise RuntimeError("No RSS headlines retrieved; preserving previous data. " + ", ".join(errors))
    headlines.sort(key=lambda item: item["published_at"] or "", reverse=True)
    seen = set()
    unique = []
    for item in headlines:
        key = item["url"]
        if key not in seen:
            seen.add(key)
            unique.append(item)
    output = {
        "title": "The Morning Brief",
        "status": "rss_ready",
        "updated_at": now.isoformat(),
        "headlines": unique[:15],
        "quiz": [],
        "debrief": "",
        "concept": {"title": "", "explanation": ""},
        "feed_errors": errors,
    }
    target = ROOT / "data" / "news.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(output['headlines'])} headlines; feed errors: {errors}")

if __name__ == "__main__":
    main()
