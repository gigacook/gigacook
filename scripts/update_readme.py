#!/usr/bin/env python3
"""Refreshes the live bits of the profile README.

- Truth of the Day: one quote from zeroCortisol, same pick as gigacook.github.io/truth
- Hall of Goon: top goonyjump players. Live from the server if GOONER_URL is set,
  otherwise the archived Season 1 leaderboard.

Stdlib only. Run: python3 scripts/update_readme.py
"""
import datetime
import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
QUOTES_URL = "https://raw.githubusercontent.com/gigacook/zeroCortisol/main/data/quotes.json"
HALL_URL = "https://raw.githubusercontent.com/gigacook/goonyjump/main/gooner_seen.season1.json"
MEDALS = ["🥇", "🥈", "🥉", "4", "5"]


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "gigacook-profile"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def md_safe(text, limit=40):
    """Player names are user input: keep them from breaking (or injecting into) the table."""
    text = re.sub(r"[<>|`\[\]\\*_#!]", "", str(text)).strip()
    return text[:limit] or "anonymous gooner"


def truth_of_the_day(today):
    quotes = get_json(QUOTES_URL)
    # Must match pickTruth() in gigacook.github.io: day number × 97, mod corpus size.
    day = (today - datetime.date(1970, 1, 1)).days
    q = quotes[(day * 97) % len(quotes)]
    return (
        f"> *\"{q['quote']}\"*\n>\n"
        f"> — **{q['author']}**, *{q['work']}*\n\n"
        f"<sub>One of {len(quotes)} verbatim passages from "
        f"[zeroCortisol](https://github.com/gigacook/zeroCortisol). "
        f"New one every morning. Updated {today.isoformat()}.</sub>"
    )


def hall_of_goon():
    live_url = os.environ.get("GOONER_URL", "").rstrip("/")
    players, label = None, "Season 1, archived"
    if live_url:
        try:
            players = get_json(f"{live_url}/info").get("seen") or None
            label = "live from the tower"
        except Exception:
            players = None
    if players is None:
        players = list(get_json(HALL_URL).values())
    players = sorted(players, key=lambda p: -int(p.get("lvl", 1)))[:5]
    rows = ["| | Gooner | Level | Body | Hat |", "|---|---|---|---|---|"]
    for medal, p in zip(MEDALS, players):
        rows.append(f"| {medal} | **{md_safe(p.get('name'))}** | LV {int(p.get('lvl', 1))} "
                    f"| {md_safe(p.get('char', 'goober'), 12)} | {md_safe(p.get('hat', 'cap'), 12)} |")
    return "\n".join(rows) + f"\n\n<sub>Hall of Goon ({label}). Think you can do better? "\
        "[Play in your browser](https://gigacook.github.io/play/).</sub>"


def replace_block(text, name, body):
    pattern = re.compile(rf"(<!-- {name}:START -->\n).*?(<!-- {name}:END -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"marker {name} missing from README")
    return pattern.sub(lambda m: m.group(1) + body + "\n" + m.group(2), text)


def main():
    today = datetime.datetime.now(datetime.timezone.utc).date()
    with open(README, encoding="utf-8") as f:
        text = f.read()
    text = replace_block(text, "TRUTH", truth_of_the_day(today))
    text = replace_block(text, "HALL", hall_of_goon())
    with open(README, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
