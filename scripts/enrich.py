#!/usr/bin/env python3
"""
Part A — Listing Enrichment Agent.

Reads data/listings.json, calls Claude per-listing to generate marketing copy
and ideal-tenant recommendations, and writes data/enriched.json incrementally.

Key AI-integration techniques demonstrated:
  1. Prompt caching on the system prompt — the ~1.5k-token leasing rubric is
     sent once, then cache-read on every subsequent call at ~10% the cost.
  2. Tool-use for structured output — the model is forced to call a single
     tool with a strict JSON schema, so outputs are machine-parseable with
     no regex / JSON-repair.
  3. Incremental + resumable — every successful record is flushed to disk, so
     crashes, rate-limits, or Ctrl-C don't lose work.

Usage:
    python scripts/enrich.py           # enrich all listings
    python scripts/enrich.py 3         # smoke-test: enrich only first 3
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
LISTINGS_PATH = ROOT / "data" / "listings.json"
ENRICHED_PATH = ROOT / "data" / "enriched.json"

DEFAULT_MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# System prompt — cached. Keep this long enough (>1024 tokens) to benefit from
# prompt caching, and specific enough to get high-quality, consistent output.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a commercial real estate leasing strategist with deep experience marketing retail, shopping center, and mixed-use vacancies across the Mid-Atlantic and national markets. You work on behalf of the landlord/owner, not a tenant rep.

Your job: given a single vacant space, produce marketing copy and a shortlist of ideal tenant categories that would thrive in that specific location. You will receive one property at a time and must respond by calling the `save_listing_enrichment` tool exactly once.

# Portfolio context
This listing is part of the Goodman Properties portfolio — a privately-held commercial real estate owner with ~130 properties across PA, NJ, IN, MD, VA, WV, FL, and DE. Most holdings are neighborhood shopping centers, retail pads, and a handful of office, medical, mixed-use, and industrial assets. Many centers are anchored by national creditworthy tenants (CVS, Wawa, Walgreens, Giant, Costco, Rite Aid). The portfolio is concentrated in the suburban Philadelphia market (Willow Grove, Jenkintown, Blue Bell, Warrington, King of Prussia, Springfield) with scattered holdings elsewhere.

# How to reason about each vacancy

Before generating output, mentally assess:
1. **Size tier** — <1K SF (kiosk/pop-up), 1K–3K SF (small shop), 3K–10K SF (mid-box), 10K–20K SF (large box), 20K+ SF (junior anchor). Size is the single biggest constraint on tenant fit.
2. **Trade area** — suburban Main Line Philly is affluent, drive-thru-dependent, grocer-anchored; urban Philadelphia (19102, 19103, 19147) is walkable, dense, younger demographics; rural PA / Evansville IN / Moundsville WV are lower-density, value-oriented trade areas.
3. **Property type** — "Shopping Center" = inline or endcap in a strip/neighborhood center; "Retail" = typically a single freestanding pad or pharmacy site; "Office" = professional plaza; "Medical" = medical office; "Mixed-Use" = ground-floor retail under residential or office; "Restaurant" = former restaurant space (has hood, grease trap — target other restaurants); "Industrial" = warehouse/flex.
4. **Co-tenancy signals** — the detail-page URL often hints at existing anchors (cvs-, wawa-, walgreens-, giant-, costco-). Use this: if the center is Wawa-anchored, do NOT recommend Wawa or 7-Eleven; if Walgreens-anchored, do NOT recommend CVS; etc. Look for complementary uses instead.

# Field-by-field guidelines

**headline** — 6 to 10 words. Lead with what makes the space valuable (location, size, co-tenancy, visibility). No hype adjectives ("amazing," "incredible," "prime opportunity"). Specific beats generic.
  Good: "5,009 SF Endcap at Gwynedd Crossing — North Wales"
  Good: "12,000 SF Mixed-Use Retail on City Line Avenue"
  Bad: "Amazing Retail Opportunity You Can't Miss!"

**description** — 2 to 3 sentences, ~50–80 words. State the space, the setting, and one concrete reason a tenant should care (traffic corridor, demographics, co-tenants, trade area characteristic). Write for a retail broker or franchise real estate director, not a consumer.

**seo_title** — 50 to 60 characters. Format: "[SF] SF [Type] for Lease — [City], [State]". If no SF is posted, use "Available Space for Lease — [City], [State]".

**seo_meta** — 150 to 160 characters. One sentence suitable for Google search results. Include SF (if known), city, and one distinguishing feature.

**alt_text** — Up to 125 characters. Describes what a photo of this property would likely show. Used for screen readers and image SEO. Neutral and factual.

**leasing_angle** — One sentence (max 20 words). A landlord's broker could paste this as the subject line or opening hook of a cold email. The "why this space, why now."

**ideal_tenants** — 5 to 10 tenant categories that realistically fit this SPECIFIC space. Each entry must contain:
  - `category`: the retail/use category (e.g., "Boutique fitness", "QSR with drive-through", "Medical urgent care", "Specialty grocer")
  - `example_brands`: 3 to 5 real brands currently expanding in this category. Only use brands that actually exist and are in an active expansion mode. Recent expanders to draw from include: fitness (Planet Fitness, Crunch, F45, Orangetheory, Club Pilates, StretchLab), QSR (Chipotle, Raising Cane's, Chick-fil-A, Jersey Mike's, Jersey Mike's, CAVA, Sweetgreen, Dave's Hot Chicken), pharmacy/medical (MinuteClinic, CityMD, Concentra, AFC Urgent Care, Aspen Dental, Sola Salons), discount (Dollar Tree, Five Below, Dollar General, Ollie's, Burlington, Ross, TJ Maxx, HomeGoods, Marshalls), grocery (Aldi, Lidl, Sprouts, Grocery Outlet, Trader Joe's), services (Heartland Dental, European Wax Center, Massage Envy, Great Clips, Sport Clips), pet (Woof Gang Bakery, EarthWise Pet, Petco), and small-format (Jeni's, Crumbl, Duck Donuts, Kung Fu Tea).
  - `why`: 1 to 2 sentences explaining why this specific space fits this specific category — reference the actual SF, trade area, co-tenancy, or visibility.

Match tenants to size:
  - <1,000 SF: kiosk, phone repair, tailor, jeweler, quick-service counter, beauty bar
  - 1,000–2,500 SF: QSR, coffee, nails, insurance, small service retail
  - 2,500–5,000 SF: fast-casual restaurant, specialty retail, boutique fitness (F45-sized)
  - 5,000–10,000 SF: larger fast-casual, urgent care, Aldi-sized grocer, Planet Fitness (small format)
  - 10,000–20,000 SF: Dollar Tree, Five Below, Ollie's, Harbor Freight, larger fitness (Crunch, Planet Fitness)
  - 20,000–40,000 SF: junior anchors — TJ Maxx, HomeGoods, Burlington, Ross, Marshalls, Grocery Outlet, Aldi full format

# Do-not-do list
- Do NOT recommend brands that compete directly with the visible anchor (e.g., a CVS for a Walgreens-anchored center)
- Do NOT invent brand names or use ones that have exited the market (Sears, Pier 1, Bed Bath & Beyond US stores, etc.)
- Do NOT use generic AI phrasing: "nestled in," "boasts," "opportunity awaits," "state-of-the-art," "prime location"
- Do NOT speculate about rent, price, or lease terms — you don't know them
- Do NOT recommend tenants that obviously don't fit the size (no Chipotle in a 650 SF box, no TJ Maxx in a 5K SF shop)

Call the save_listing_enrichment tool exactly once with all fields populated. Do not include any other text in your response."""

# ---------------------------------------------------------------------------
# Tool schema — forces structured, validated output.
# ---------------------------------------------------------------------------
ENRICH_TOOL = {
    "name": "save_listing_enrichment",
    "description": "Save the enriched marketing copy and ideal tenant recommendations for a single Goodman Properties listing.",
    "input_schema": {
        "type": "object",
        "properties": {
            "headline": {
                "type": "string",
                "description": "6-10 word marketing headline. Specific, no hype adjectives.",
            },
            "description": {
                "type": "string",
                "description": "2-3 sentence marketing description (~50-80 words) targeted at retail brokers and franchise real estate directors.",
            },
            "seo_title": {
                "type": "string",
                "description": "50-60 character SEO title tag. Format: '[SF] SF [Type] for Lease — [City], [State]'.",
            },
            "seo_meta": {
                "type": "string",
                "description": "150-160 character meta description for search results.",
            },
            "alt_text": {
                "type": "string",
                "description": "Up to 125 character factual image alt text.",
            },
            "leasing_angle": {
                "type": "string",
                "description": "One sentence (max 20 words) usable as a cold email subject line or hook.",
            },
            "ideal_tenants": {
                "type": "array",
                "minItems": 5,
                "maxItems": 10,
                "description": "5-10 tenant categories that realistically fit this specific space.",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "The retail/use category.",
                        },
                        "example_brands": {
                            "type": "array",
                            "minItems": 3,
                            "maxItems": 5,
                            "items": {"type": "string"},
                            "description": "3-5 real, currently-expanding brand names.",
                        },
                        "why": {
                            "type": "string",
                            "description": "1-2 sentences tying the brand category to this specific space's SF, trade area, or co-tenancy.",
                        },
                    },
                    "required": ["category", "example_brands", "why"],
                },
            },
        },
        "required": [
            "headline",
            "description",
            "seo_title",
            "seo_meta",
            "alt_text",
            "leasing_angle",
            "ideal_tenants",
        ],
    },
}


def format_listing(listing: dict) -> str:
    """Render a single listing as the user-turn message."""
    lines = [
        f"Address: {listing['a']}",
        f"City/State/ZIP: {listing['c']}, {listing['s']} {listing['z']}",
        f"Property type: {listing['t']}",
    ]
    sf = listing.get("sf", "").strip()
    if sf:
        lines.append(f"Available square footage: {sf} SF")
    else:
        lines.append("Available square footage: not publicly listed")
    lines.append(f"Source URL: https://goodmanproperties.org{listing['u']}")
    return "\n".join(lines)


def listing_key(listing: dict) -> str:
    """Stable identifier for resume/dedup."""
    return f"{listing['a']}|{listing['c']}|{listing['s']}|{listing['z']}|{listing['u']}"


def enrich_one(client: Anthropic, model: str, listing: dict) -> tuple[dict, dict]:
    """Call the model for one listing. Returns (enrichment, usage_dict)."""
    resp = client.messages.create(
        model=model,
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[ENRICH_TOOL],
        tool_choice={"type": "tool", "name": "save_listing_enrichment"},
        messages=[{"role": "user", "content": format_listing(listing)}],
    )

    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "save_listing_enrichment":
            usage = {
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
                "cache_creation_input_tokens": getattr(
                    resp.usage, "cache_creation_input_tokens", 0
                ) or 0,
                "cache_read_input_tokens": getattr(
                    resp.usage, "cache_read_input_tokens", 0
                ) or 0,
            }
            return block.input, usage

    raise RuntimeError(
        f"Model response did not contain a tool_use block. "
        f"Stop reason: {resp.stop_reason}"
    )


def load_existing(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    return {item["key"]: item for item in data if "key" in item}


def save_all(path: Path, results: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(results.values()), indent=2))


def main() -> int:
    load_dotenv(ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ERROR: ANTHROPIC_API_KEY not set.\n"
            "  1. Copy .env.example to .env\n"
            "  2. Get a key at https://console.anthropic.com/\n"
            "  3. Paste it into .env as ANTHROPIC_API_KEY=sk-ant-...",
            file=sys.stderr,
        )
        return 1

    model = os.environ.get("ENRICH_MODEL", DEFAULT_MODEL)

    limit: int | None = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [limit]", file=sys.stderr)
            return 2

    listings = json.loads(LISTINGS_PATH.read_text())
    print(f"Loaded {len(listings)} listings from {LISTINGS_PATH.relative_to(ROOT)}")

    results = load_existing(ENRICHED_PATH)
    if results:
        print(f"Resuming: {len(results)} listings already enriched")

    queue: list[tuple[str, dict]] = []
    for listing in listings:
        key = listing_key(listing)
        if key in results:
            continue
        queue.append((key, listing))
        if limit is not None and len(queue) >= limit:
            break

    if not queue:
        print("Nothing to do — all listings already enriched.")
        return 0

    print(f"Enriching {len(queue)} listings with model={model}")
    print("-" * 72)

    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    client = Anthropic()

    for i, (key, listing) in enumerate(queue, 1):
        label = f"{listing['a']}, {listing['c']} {listing['s']}"
        print(f"[{i:3d}/{len(queue)}] {label[:56]:56s}", end=" ", flush=True)
        try:
            enrichment, usage = enrich_one(client, model, listing)
        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {e}")
            continue

        for k, v in usage.items():
            totals[k] += v

        results[key] = {
            "key": key,
            "listing": listing,
            "enrichment": enrichment,
        }
        save_all(ENRICHED_PATH, results)

        print(
            f"ok  in={usage['input_tokens']:4d} "
            f"out={usage['output_tokens']:4d} "
            f"cache_read={usage['cache_read_input_tokens']:5d}"
        )

    print("-" * 72)
    print(f"Done. {len(results)} total enriched listings → {ENRICHED_PATH.relative_to(ROOT)}")
    print(
        f"Usage totals: input={totals['input_tokens']} "
        f"output={totals['output_tokens']} "
        f"cache_write={totals['cache_creation_input_tokens']} "
        f"cache_read={totals['cache_read_input_tokens']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
