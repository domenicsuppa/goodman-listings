#!/usr/bin/env python3
"""
Generate a content calendar from data/marketing.json.

For each listing, queue one post per channel, staggered across a weekday
schedule. Default config: 1 listing per weekday, 4 channels (Facebook,
Nextdoor, LinkedIn, Instagram) posted at 9am, 11am, 1pm, 3pm local time
on that listing's assigned day.

Output: data/schedule.json — a list of queue items with:
  - id                (stable per-item key: "{listing_key}::{channel}")
  - listing_key       (join key back to listings/enrichment/marketing)
  - listing_summary   ({a, c, s, z, t, sf, u, headline})
  - channel           ("facebook_local_post", etc.)
  - channel_label     (human-readable: "Facebook", "Nextdoor", etc.)
  - content           (ready-to-post text for this channel)
  - scheduled_for     (ISO 8601, local tz)
  - status            ("pending", "posted", "failed", "skipped")
  - posted_at         (ISO 8601 or null)
  - error             (string or null)

Re-running this script is a no-op for items that already exist in
schedule.json (matched by id). Pass --rebuild to wipe and regenerate.

Usage:
    python scripts/build_schedule.py
    python scripts/build_schedule.py --rebuild
    python scripts/build_schedule.py --start 2026-04-13
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
MARKETING_PATH = ROOT / "data" / "marketing.json"
ENRICHED_PATH = ROOT / "data" / "enriched.json"
SCHEDULE_PATH = ROOT / "data" / "schedule.json"

TZ = ZoneInfo("America/New_York")

# (channel_key, human_label, hour_of_day)
CHANNELS: list[tuple[str, str, int]] = [
    ("facebook_local_post", "Facebook", 9),
    ("nextdoor_post", "Nextdoor", 11),
    ("linkedin_post", "LinkedIn", 13),
    ("instagram_caption", "Instagram", 15),
]


def next_weekday(d: date) -> date:
    """Advance d to the next weekday (Mon-Fri), returning d itself if already one."""
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d += timedelta(days=1)
    return d


def advance_weekday(d: date) -> date:
    """Return the next weekday strictly after d."""
    d += timedelta(days=1)
    return next_weekday(d)


def item_id(listing_key: str, channel: str) -> str:
    return f"{listing_key}::{channel}"


def make_listing_summary(l: dict, enrichment: dict | None) -> dict:
    return {
        "a": l["a"],
        "c": l["c"],
        "s": l["s"],
        "z": l["z"],
        "t": l["t"],
        "sf": l.get("sf", ""),
        "u": l["u"],
        "headline": (enrichment or {}).get("headline") or l["a"],
    }


def channel_content(marketing: dict, channel: str) -> str | None:
    val = marketing.get(channel)
    return val if isinstance(val, str) and val.strip() else None


def build_schedule(
    marketing_records: list[dict],
    enriched_by_key: dict[str, dict],
    start_date: date,
    existing_ids: set[str],
) -> list[dict]:
    """Generate new schedule items, one per (listing, channel) pair, skipping
    anything already scheduled. Sorts listings by state then city then
    address for predictable ordering."""
    marketing_records = sorted(
        marketing_records,
        key=lambda r: (r["listing"]["s"], r["listing"]["c"], r["listing"]["a"]),
    )

    cursor = next_weekday(start_date)
    new_items: list[dict] = []

    for rec in marketing_records:
        l = rec["listing"]
        marketing = rec.get("marketing") or {}
        listing_key = rec["key"]
        enrichment = enriched_by_key.get(listing_key)
        summary = make_listing_summary(l, enrichment)

        added_for_this_listing = 0
        for channel_key, channel_label, hour in CHANNELS:
            content = channel_content(marketing, channel_key)
            if content is None:
                continue

            iid = item_id(listing_key, channel_key)
            if iid in existing_ids:
                continue

            scheduled_dt = datetime.combine(cursor, time(hour=hour), tzinfo=TZ)
            new_items.append(
                {
                    "id": iid,
                    "listing_key": listing_key,
                    "listing_summary": summary,
                    "channel": channel_key,
                    "channel_label": channel_label,
                    "content": content,
                    "scheduled_for": scheduled_dt.isoformat(),
                    "status": "pending",
                    "posted_at": None,
                    "error": None,
                }
            )
            added_for_this_listing += 1

        if added_for_this_listing > 0:
            cursor = advance_weekday(cursor)

    return new_items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="wipe existing schedule before rebuilding")
    parser.add_argument("--start", type=str, default=None, help="start date YYYY-MM-DD (default: next weekday)")
    args = parser.parse_args()

    if not MARKETING_PATH.exists():
        print(f"ERROR: {MARKETING_PATH.relative_to(ROOT)} not found.", file=sys.stderr)
        return 1

    marketing_records = json.loads(MARKETING_PATH.read_text())

    enriched_by_key: dict[str, dict] = {}
    if ENRICHED_PATH.exists():
        enriched_records = json.loads(ENRICHED_PATH.read_text())
        enriched_by_key = {r["key"]: r["enrichment"] for r in enriched_records}

    # Load existing schedule (for resume behavior)
    existing_items: list[dict] = []
    if SCHEDULE_PATH.exists() and not args.rebuild:
        try:
            existing_items = json.loads(SCHEDULE_PATH.read_text())
        except json.JSONDecodeError:
            existing_items = []

    existing_ids = {item["id"] for item in existing_items}

    # Determine start date
    if args.start:
        try:
            start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        except ValueError:
            print(f"ERROR: --start must be YYYY-MM-DD, got {args.start!r}", file=sys.stderr)
            return 2
    else:
        today = datetime.now(TZ).date()
        start_date = next_weekday(today + timedelta(days=1))  # start tomorrow or later

    new_items = build_schedule(marketing_records, enriched_by_key, start_date, existing_ids)

    all_items = existing_items + new_items
    all_items.sort(key=lambda i: i["scheduled_for"])

    SCHEDULE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_PATH.write_text(json.dumps(all_items, indent=2))

    by_channel: dict[str, int] = {}
    for item in all_items:
        by_channel[item["channel_label"]] = by_channel.get(item["channel_label"], 0) + 1

    print(f"Wrote {SCHEDULE_PATH.relative_to(ROOT)}")
    print(f"  Existing items carried over: {len(existing_items)}")
    print(f"  New items added:             {len(new_items)}")
    print(f"  Total items:                 {len(all_items)}")
    if all_items:
        print(f"  First post scheduled:        {all_items[0]['scheduled_for']}")
        print(f"  Last post scheduled:         {all_items[-1]['scheduled_for']}")
    print(f"  By channel:                  {dict(sorted(by_channel.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
