#!/usr/bin/env python3
"""
Post any due items from data/schedule.json to a configured webhook URL.

Finds items where:
  - status == "pending"
  - scheduled_for <= now (or <= --until)

For each, POSTs a JSON payload to $WEBHOOK_URL (set in .env or the
environment). The payload format is auto-detected from the URL:

  hooks.slack.com/*          → Slack Incoming Webhook (text + blocks)
  discord.com/api/webhooks/* → Discord Webhook (content)
  anything else              → generic JSON with a standard shape

On success, marks the item status="posted" with posted_at timestamp.
On failure, marks status="failed" with the error string. The schedule
file is rewritten after each item so partial runs don't lose work.

Usage:
    python scripts/post_due.py                    # post everything due right now
    python scripts/post_due.py --dry-run          # show what would be posted
    python scripts/post_due.py --until 2026-04-20 # post everything due by a date
    python scripts/post_due.py --limit 5          # cap how many we post this run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib import error as urlerr
from urllib import request as urlreq
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
SCHEDULE_PATH = ROOT / "data" / "schedule.json"
TZ = ZoneInfo("America/New_York")

BASE_URL = "https://goodmanproperties.org"


def detect_platform(url: str) -> str:
    u = (url or "").lower()
    if "hooks.slack.com" in u:
        return "slack"
    if "discord.com/api/webhooks" in u or "discordapp.com/api/webhooks" in u:
        return "discord"
    return "generic"


def build_payload(item: dict, platform: str) -> dict:
    summary = item["listing_summary"]
    headline = summary.get("headline") or summary["a"]
    source_url = f"{BASE_URL}{summary.get('u', '')}"
    sf = summary.get("sf") or "Contact"
    location = f"{summary['c']}, {summary['s']} {summary['z']}"

    if platform == "slack":
        return {
            "text": f"[{item['channel_label']}] {headline}",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": headline[:150]},
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Channel:* {item['channel_label']}  |  "
                                f"*Address:* {summary['a']}, {location}  |  "
                                f"*Available:* {sf} SF  |  "
                                f"<{source_url}|Source>"
                            ),
                        }
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        # Slack blocks have a 3000 char limit per section
                        "text": item["content"][:2900],
                    },
                },
                {"type": "divider"},
            ],
        }

    if platform == "discord":
        # Discord caps content at 2000 chars
        body = (
            f"**[{item['channel_label']}] {headline}**\n"
            f"{summary['a']}, {location}  |  Available: {sf} SF  |  <{source_url}>\n\n"
            f"{item['content']}"
        )
        return {"content": body[:1990]}

    # Generic: any webhook endpoint (Zapier, Make, custom server)
    return {
        "event": "goodman.listing.post",
        "channel": item["channel"],
        "channel_label": item["channel_label"],
        "scheduled_for": item["scheduled_for"],
        "listing": summary,
        "content": item["content"],
        "source_url": source_url,
    }


def post_json(url: str, payload: dict, timeout: int = 15) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urlreq.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlreq.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urlerr.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except urlerr.URLError as e:
        return 0, f"URLError: {e.reason}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="print without posting")
    parser.add_argument("--until", type=str, default=None, help="post items due by this ISO date/datetime")
    parser.add_argument("--limit", type=int, default=None, help="max items to post this run")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    webhook_url = os.environ.get("WEBHOOK_URL", "").strip()

    if not webhook_url and not args.dry_run:
        print(
            "ERROR: WEBHOOK_URL not set. Add it to .env, e.g.:\n"
            "  WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ\n"
            "  WEBHOOK_URL=https://discord.com/api/webhooks/XXX/YYY\n"
            "Or run with --dry-run to preview without posting.",
            file=sys.stderr,
        )
        return 1

    if not SCHEDULE_PATH.exists():
        print(f"ERROR: {SCHEDULE_PATH.relative_to(ROOT)} not found. Run build_schedule.py first.", file=sys.stderr)
        return 1

    items = json.loads(SCHEDULE_PATH.read_text())

    # Cutoff: everything due at or before this moment
    if args.until:
        try:
            if len(args.until) == 10:  # YYYY-MM-DD
                cutoff = datetime.fromisoformat(args.until).replace(hour=23, minute=59, second=59, tzinfo=TZ)
            else:
                cutoff = datetime.fromisoformat(args.until)
                if cutoff.tzinfo is None:
                    cutoff = cutoff.replace(tzinfo=TZ)
        except ValueError:
            print(f"ERROR: --until must be ISO format, got {args.until!r}", file=sys.stderr)
            return 2
    else:
        cutoff = datetime.now(TZ)

    platform = detect_platform(webhook_url) if webhook_url else "generic"

    due: list[tuple[int, dict]] = []
    for idx, item in enumerate(items):
        if item.get("status") != "pending":
            continue
        scheduled = datetime.fromisoformat(item["scheduled_for"])
        if scheduled <= cutoff:
            due.append((idx, item))

    if args.limit is not None:
        due = due[: args.limit]

    if not due:
        print(f"No due items. Cutoff: {cutoff.isoformat()}")
        return 0

    print(f"Due items to post: {len(due)}")
    print(f"Cutoff:            {cutoff.isoformat()}")
    print(f"Platform detected: {platform}")
    if args.dry_run:
        print("Mode:              DRY RUN (nothing will be posted)")
    else:
        # Print a redacted version of the webhook URL
        redacted = webhook_url.split("/")
        if len(redacted) > 4:
            redacted[-1] = "***"
            redacted[-2] = "***"
        print(f"Webhook:           {'/'.join(redacted)}")
    print("-" * 72)

    posted = failed = 0
    for idx, item in due:
        summary = item["listing_summary"]
        label = f"{summary['a'][:30]}, {summary['c']} {summary['s']}"
        channel = item["channel_label"]
        print(f"  [{channel:10s}] {label[:48]:48s}", end=" ", flush=True)

        if args.dry_run:
            preview = item["content"][:60].replace("\n", " ")
            print(f"DRY  {preview}...")
            continue

        payload = build_payload(item, platform)
        status, body = post_json(webhook_url, payload)
        if 200 <= status < 300:
            item["status"] = "posted"
            item["posted_at"] = datetime.now(TZ).isoformat()
            item["error"] = None
            posted += 1
            print(f"OK   ({status})")
        else:
            item["status"] = "failed"
            item["error"] = f"HTTP {status}: {body[:200]}"
            failed += 1
            print(f"FAIL ({status}) {body[:80]}")

        # Flush after each post so we don't lose progress
        SCHEDULE_PATH.write_text(json.dumps(items, indent=2))

    print("-" * 72)
    if args.dry_run:
        print(f"Dry run complete. {len(due)} items would be posted.")
    else:
        print(f"Done. Posted: {posted}  Failed: {failed}")
    return 0 if failed == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
