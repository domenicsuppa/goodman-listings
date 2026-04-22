#!/usr/bin/env python3
"""
Export data/schedule.json as bulk-upload CSVs for social scheduling tools.

Writes four files under exports/:
  - hootsuite.csv           — Hootsuite Bulk Composer format
  - meta_business_suite.csv — Meta Business Suite bulk scheduling format
  - buffer.csv              — Buffer bulk upload format
  - content_calendar.csv    — generic content calendar (Excel / Google Sheets)

Column layouts are tool-specific. When uploading, always double-check the
target platform's current template since they change occasionally.

Usage:
    python scripts/export_schedule.py
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEDULE_PATH = ROOT / "data" / "schedule.json"
EXPORTS_DIR = ROOT / "exports"

BASE_URL = "https://goodmanproperties.org"

# Maps our internal channel key to the platform label each tool expects.
HOOTSUITE_PLATFORM = {
    "facebook_local_post": "Facebook",
    "nextdoor_post": "Facebook",  # Nextdoor isn't natively supported; we tag it as FB with a note in the post
    "linkedin_post": "LinkedIn",
    "instagram_caption": "Instagram",
}

BUFFER_PROFILE = {
    "facebook_local_post": "Facebook Page",
    "nextdoor_post": "Facebook Page",
    "linkedin_post": "LinkedIn Company Page",
    "instagram_caption": "Instagram Business",
}

META_PLATFORM = {
    "facebook_local_post": "Facebook",
    "instagram_caption": "Instagram",
}


def iso_to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def listing_link(summary: dict) -> str:
    return f"{BASE_URL}{summary.get('u', '')}"


def load_schedule() -> list[dict]:
    if not SCHEDULE_PATH.exists():
        print(
            f"ERROR: {SCHEDULE_PATH.relative_to(ROOT)} not found. "
            f"Run scripts/build_schedule.py first.",
            file=sys.stderr,
        )
        sys.exit(1)
    return json.loads(SCHEDULE_PATH.read_text())


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)


def export_hootsuite(items: list[dict]) -> int:
    """Hootsuite Bulk Composer accepts CSV with columns:
    Date (YYYY-MM-DD), Time (HH:MM), Message, Link, Image URL"""
    rows = []
    for item in items:
        dt = iso_to_dt(item["scheduled_for"])
        rows.append(
            {
                "Date": dt.strftime("%Y-%m-%d"),
                "Time": dt.strftime("%H:%M"),
                "Platform": HOOTSUITE_PLATFORM.get(item["channel"], "Facebook"),
                "Message": item["content"],
                "Link": listing_link(item["listing_summary"]),
                "Image URL": "",
            }
        )
    path = EXPORTS_DIR / "hootsuite.csv"
    write_csv(path, rows, ["Date", "Time", "Platform", "Message", "Link", "Image URL"])
    return len(rows)


def export_buffer(items: list[dict]) -> int:
    """Buffer bulk upload format: Date, Time, Profile, Text, Link."""
    rows = []
    for item in items:
        dt = iso_to_dt(item["scheduled_for"])
        rows.append(
            {
                "Date": dt.strftime("%Y-%m-%d"),
                "Time": dt.strftime("%H:%M"),
                "Profile": BUFFER_PROFILE.get(item["channel"], "Facebook Page"),
                "Text": item["content"],
                "Link": listing_link(item["listing_summary"]),
            }
        )
    path = EXPORTS_DIR / "buffer.csv"
    write_csv(path, rows, ["Date", "Time", "Profile", "Text", "Link"])
    return len(rows)


def export_meta(items: list[dict]) -> int:
    """Meta Business Suite bulk scheduling. Only Facebook and Instagram items.
    Columns: Scheduled Date, Scheduled Time, Platform, Post Content, Link, Media URL."""
    filtered = [i for i in items if i["channel"] in META_PLATFORM]
    rows = []
    for item in filtered:
        dt = iso_to_dt(item["scheduled_for"])
        rows.append(
            {
                "Scheduled Date": dt.strftime("%Y-%m-%d"),
                "Scheduled Time": dt.strftime("%H:%M"),
                "Platform": META_PLATFORM[item["channel"]],
                "Post Content": item["content"],
                "Link": listing_link(item["listing_summary"]),
                "Media URL": "",
            }
        )
    path = EXPORTS_DIR / "meta_business_suite.csv"
    write_csv(
        path,
        rows,
        ["Scheduled Date", "Scheduled Time", "Platform", "Post Content", "Link", "Media URL"],
    )
    return len(rows)


def export_calendar(items: list[dict]) -> int:
    """Human-readable content calendar, viewable in Excel or Google Sheets.
    Includes listing address, city, channel, scheduled time, content preview,
    and the source URL. Useful for review/sign-off before scheduling."""
    rows = []
    for item in items:
        summary = item["listing_summary"]
        dt = iso_to_dt(item["scheduled_for"])
        content = item["content"]
        preview = content[:120] + ("..." if len(content) > 120 else "")
        rows.append(
            {
                "Scheduled Date": dt.strftime("%Y-%m-%d"),
                "Scheduled Time": dt.strftime("%H:%M"),
                "Weekday": dt.strftime("%A"),
                "Channel": item["channel_label"],
                "Property": summary["a"],
                "City": summary["c"],
                "State": summary["s"],
                "Property Type": summary["t"],
                "Available SF": summary.get("sf", ""),
                "Headline": summary.get("headline", ""),
                "Content Preview": preview,
                "Full Content": content,
                "Source URL": listing_link(summary),
                "Status": item["status"],
            }
        )
    path = EXPORTS_DIR / "content_calendar.csv"
    write_csv(
        path,
        rows,
        [
            "Scheduled Date",
            "Scheduled Time",
            "Weekday",
            "Channel",
            "Property",
            "City",
            "State",
            "Property Type",
            "Available SF",
            "Headline",
            "Content Preview",
            "Full Content",
            "Source URL",
            "Status",
        ],
    )
    return len(rows)


def main() -> int:
    items = load_schedule()
    if not items:
        print("Schedule is empty. Run scripts/build_schedule.py first.", file=sys.stderr)
        return 1

    print(f"Loaded {len(items)} scheduled items")
    print("-" * 60)

    n_hoot = export_hootsuite(items)
    print(f"  hootsuite.csv           {n_hoot:4d} rows")

    n_buf = export_buffer(items)
    print(f"  buffer.csv              {n_buf:4d} rows")

    n_meta = export_meta(items)
    print(f"  meta_business_suite.csv {n_meta:4d} rows  (Facebook + Instagram only)")

    n_cal = export_calendar(items)
    print(f"  content_calendar.csv    {n_cal:4d} rows  (all channels, full preview)")

    print("-" * 60)
    print(f"Done. 4 exports written to {EXPORTS_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
