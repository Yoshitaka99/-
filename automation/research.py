"""元ネタ収集: Hacker News + RSS から当日のAIニュースを集める（無料APIのみ）。

ろじん原則「持論ではなく元情報」の供給源。出力は候補ネタのJSONリスト。
"""
import json
import re
import sys
from pathlib import Path

import feedparser
import requests
import yaml

ROOT = Path(__file__).parent
STATE = ROOT / "state"


def load_config():
    return yaml.safe_load((ROOT / "config.yaml").read_text())


def fetch_hackernews(keywords, limit=30):
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=15
        ).json()[:80]
    except Exception as e:
        print(f"[research] HN取得失敗: {e}", file=sys.stderr)
        return []
    pattern = re.compile("|".join(re.escape(k) for k in keywords), re.IGNORECASE)
    items = []
    for sid in ids:
        if len(items) >= limit:
            break
        try:
            it = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=10
            ).json()
        except Exception:
            continue
        title = (it or {}).get("title", "")
        if title and pattern.search(title):
            items.append(
                {
                    "title": title,
                    "url": it.get("url") or f"https://news.ycombinator.com/item?id={sid}",
                    "source": "hackernews",
                    "score": it.get("score", 0),
                }
            )
    return items


def fetch_rss(feeds):
    items = []
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed)
        except Exception as e:
            print(f"[research] RSS取得失敗 {feed}: {e}", file=sys.stderr)
            continue
        for e in parsed.entries[:5]:
            items.append(
                {
                    "title": e.get("title", ""),
                    "url": e.get("link", ""),
                    "source": parsed.feed.get("title", feed),
                    "summary": re.sub(r"<[^>]+>", "", e.get("summary", ""))[:300],
                }
            )
    return items


def load_used_urls():
    used = set()
    posted = STATE / "posted.jsonl"
    if posted.exists():
        for line in posted.read_text().splitlines():
            try:
                used.add(json.loads(line).get("source_url", ""))
            except json.JSONDecodeError:
                pass
    return used


def run():
    cfg = load_config()["research"]
    used = load_used_urls()
    items = fetch_hackernews(cfg["hackernews_keywords"]) + fetch_rss(cfg["rss_feeds"])
    fresh = [i for i in items if i["url"] and i["url"] not in used]
    # HNスコア順→RSSはそのまま後ろに（注目資本の大きい順）
    fresh.sort(key=lambda i: i.get("score", 0), reverse=True)
    result = fresh[: load_config()["research"]["max_items"]]
    STATE.mkdir(exist_ok=True)
    (STATE / "research-latest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)
    )
    print(f"[research] {len(result)}件の元ネタを収集")
    return result


if __name__ == "__main__":
    run()
