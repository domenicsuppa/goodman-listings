#!/usr/bin/env python3
"""
Generate one-page PDF leasing flyers for every Goodman Properties listing.

Reads data/enriched.json and writes flyers/{slug}.pdf per listing. Each flyer
contains the AI-generated headline, property facts, description, leasing
angle callout, top-5 ideal tenant categories, and a QR code linking to the
source detail page on goodmanproperties.org.

No API calls — this is a pure local build step that consumes the output of
scripts/enrich.py.

Usage:
    python scripts/build_flyers.py          # generate all flyers
    python scripts/build_flyers.py 5        # smoke-test: first 5 only
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import qrcode
from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
ENRICHED_PATH = ROOT / "data" / "enriched.json"
FLYERS_DIR = ROOT / "flyers"

# US Letter, mm
PAGE_W = 215.9
PAGE_H = 279.4
MARGIN = 15
INNER_W = PAGE_W - 2 * MARGIN

# Brand palette (matches index.html)
INK = (27, 35, 48)
MUTED = (91, 102, 119)
ACCENT = (15, 76, 129)
ACCENT_LIGHT = (200, 220, 240)
AI_PURPLE = (90, 63, 214)
AI_BG = (243, 240, 255)
LINE = (229, 226, 216)
STAT_BG = (246, 245, 241)

BASE_URL = "https://goodmanproperties.org"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def slug(listing: dict) -> str:
    # Use the unique URL segment (e.g. "cvs-of-norristown") so two listings
    # at the same street address get distinct filenames.
    segment = listing["u"].strip("/").split("/")[-1] or "listing"
    return re.sub(r"[^a-zA-Z0-9-]+", "-", segment).lower().strip("-")[:80]


def clean(text: str | None) -> str:
    """Normalize smart-quotes, em/en dashes, bullets etc. to Latin-1 safe chars
    so the built-in Helvetica core font can render the string."""
    if not text:
        return ""
    return (
        text.replace("\u2014", " - ")  # em-dash
        .replace("\u2013", "-")         # en-dash
        .replace("\u2018", "'")         # left single
        .replace("\u2019", "'")         # right single
        .replace("\u201c", '"')         # left double
        .replace("\u201d", '"')         # right double
        .replace("\u2022", "-")         # bullet
        .replace("\u00b7", "-")         # middle dot
        .replace("\u00a0", " ")         # nbsp
        .replace("\u2026", "...")       # ellipsis
    )


def make_qr_png(url: str) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Flyer layout
# ---------------------------------------------------------------------------
def build_flyer(listing: dict, enrichment: dict) -> FPDF:
    pdf = FPDF(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # --- Header band ---
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 0, PAGE_W, 30, "F")

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(MARGIN, 10)
    pdf.cell(0, 6, "GOODMAN PROPERTIES")

    pdf.set_text_color(*ACCENT_LIGHT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(MARGIN, 17)
    pdf.cell(0, 5, "FOR LEASE")

    # QR code — top right of header
    qr_url = f"{BASE_URL}{listing['u']}"
    qr_bytes = make_qr_png(qr_url)
    qr_size = 24
    pdf.image(io.BytesIO(qr_bytes), x=PAGE_W - MARGIN - qr_size, y=3, w=qr_size, h=qr_size)

    # --- Headline block ---
    y = 40
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(MARGIN, y)
    pdf.multi_cell(INNER_W, 8, clean(enrichment.get("headline") or listing["a"]))
    y = pdf.get_y() + 2

    # Address
    pdf.set_text_color(*MUTED)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_xy(MARGIN, y)
    addr = f"{listing['a']}   |   {listing['c']}, {listing['s']} {listing['z']}"
    pdf.cell(0, 6, clean(addr))
    y += 10

    # --- Three stat boxes ---
    gap = 5
    stat_w = (INNER_W - 2 * gap) / 3
    stat_h = 18
    stats = [
        ("AVAILABLE", (listing["sf"] + " SF") if listing["sf"] else "Contact"),
        ("PROPERTY TYPE", listing["t"]),
        ("LOCATION", f"{listing['c']}, {listing['s']}"),
    ]
    for i, (label, value) in enumerate(stats):
        x = MARGIN + i * (stat_w + gap)
        pdf.set_fill_color(*STAT_BG)
        pdf.set_draw_color(*LINE)
        pdf.rect(x, y, stat_w, stat_h, "DF")
        pdf.set_text_color(*MUTED)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_xy(x + 3, y + 3)
        pdf.cell(stat_w - 6, 4, label)
        pdf.set_text_color(*INK)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_xy(x + 3, y + 9)
        pdf.cell(stat_w - 6, 6, clean(value)[:30])
    y += stat_h + 6

    # --- Description ---
    pdf.set_text_color(*ACCENT)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(MARGIN, y)
    pdf.cell(0, 4, "THE OPPORTUNITY")
    y += 6
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(MARGIN, y)
    pdf.multi_cell(INNER_W, 5, clean(enrichment.get("description", "")))
    y = pdf.get_y() + 4

    # --- Leasing angle callout ---
    angle = enrichment.get("leasing_angle", "")
    if angle:
        angle_text = clean(angle)
        # Measure how tall the callout needs to be
        pdf.set_font("Helvetica", "BI", 10)
        lines = pdf.multi_cell(INNER_W - 10, 5, angle_text, dry_run=True, output="LINES")
        line_count = max(1, len(lines))
        box_h = 6 + line_count * 5
        # Background
        pdf.set_fill_color(*AI_BG)
        pdf.rect(MARGIN, y, INNER_W, box_h, "F")
        # Left accent bar
        pdf.set_fill_color(*AI_PURPLE)
        pdf.rect(MARGIN, y, 1.5, box_h, "F")
        # Text
        pdf.set_text_color(*AI_PURPLE)
        pdf.set_xy(MARGIN + 6, y + 3)
        pdf.multi_cell(INNER_W - 10, 5, angle_text)
        y += box_h + 4

    # --- Ideal tenants (top 5) ---
    pdf.set_text_color(*ACCENT)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(MARGIN, y)
    pdf.cell(0, 4, "IDEAL TENANT CATEGORIES")
    y += 6

    tenants = enrichment.get("ideal_tenants", [])[:5]
    for i, t in enumerate(tenants, 1):
        if y > PAGE_H - 35:
            break  # avoid overflowing footer

        # Category line
        pdf.set_text_color(*INK)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_xy(MARGIN, y)
        pdf.cell(0, 5, f"{i}.  {clean(t.get('category', ''))}")
        y += 5

        # Brand list
        brands = "   |   ".join(t.get("example_brands", []) or [])
        pdf.set_text_color(*AI_PURPLE)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_xy(MARGIN + 6, y)
        pdf.multi_cell(INNER_W - 6, 4, clean(brands))
        y = pdf.get_y() + 0.5

        # Reasoning
        pdf.set_text_color(*MUTED)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_xy(MARGIN + 6, y)
        pdf.multi_cell(INNER_W - 6, 4.5, clean(t.get("why", "")))
        y = pdf.get_y() + 2.5

    # --- Footer ---
    footer_y = PAGE_H - 24
    pdf.set_draw_color(*LINE)
    pdf.line(MARGIN, footer_y, PAGE_W - MARGIN, footer_y)

    pdf.set_text_color(*ACCENT)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(MARGIN, footer_y + 3)
    pdf.cell(0, 4, "For leasing inquiries, scan the QR code or visit goodmanproperties.org")

    pdf.set_text_color(*MUTED)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_xy(MARGIN, footer_y + 9)
    pdf.cell(0, 4, "AI-enriched marketing copy generated by Claude Sonnet 4.6. Verify before external use.")

    return pdf


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> int:
    if not ENRICHED_PATH.exists():
        print(
            f"ERROR: {ENRICHED_PATH.relative_to(ROOT)} not found. "
            f"Run scripts/enrich.py first.",
            file=sys.stderr,
        )
        return 1

    records = json.loads(ENRICHED_PATH.read_text())

    limit: int | None = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [limit]", file=sys.stderr)
            return 2

    queue = records[:limit] if limit else records
    FLYERS_DIR.mkdir(exist_ok=True)

    print(f"Generating {len(queue)} flyers into {FLYERS_DIR.relative_to(ROOT)}/")
    print("-" * 72)

    for i, rec in enumerate(queue, 1):
        listing = rec["listing"]
        enrichment = rec.get("enrichment") or {}
        filename = f"{slug(listing)}.pdf"
        path = FLYERS_DIR / filename

        try:
            pdf = build_flyer(listing, enrichment)
            pdf.output(str(path))
            status = "ok"
        except Exception as e:
            status = f"FAILED: {type(e).__name__}: {e}"

        label = f"{listing['a']}, {listing['c']} {listing['s']}"
        print(f"[{i:3d}/{len(queue)}] {label[:52]:52s}  {filename[:36]:36s}  {status}")

    print("-" * 72)
    print(f"Done. {len(queue)} flyers written to {FLYERS_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
