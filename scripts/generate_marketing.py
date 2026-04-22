#!/usr/bin/env python3
"""
Part of the Goodman Listings pipeline: localized digital marketing content.

For every listing, generate ready-to-post copy for multiple channels, each
specifically written for the property's immediate neighborhood — so a
broker or marketing person can paste it directly into Facebook, Nextdoor,
LinkedIn, Instagram, or Google Ads Manager without additional editing.

Channels per listing:
  - facebook_local_post   — casual community-page friendly
  - nextdoor_post         — neighborly, hyper-local
  - instagram_caption     — caption + hashtags
  - linkedin_post         — professional, broker audience
  - google_search_ad      — 3 headlines + 2 descriptions, to character limits
  - facebook_ad           — primary_text + headline + description
  - community_hooks       — 3 short localized hooks for flyer/sign/email
  - local_context         — the specific neighborhood framing

Techniques demonstrated:
  * Prompt caching on a detailed system prompt (>2k tokens)
  * Forced tool_use for validated, schema-constrained output
  * Incremental resume on crash/Ctrl-C
  * Uses enriched.json for richer input context (headline, description, angle)

Usage:
    python scripts/generate_marketing.py          # generate for all listings
    python scripts/generate_marketing.py 3        # smoke-test: first 3 only
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
ENRICHED_PATH = ROOT / "data" / "enriched.json"
OUTPUT_PATH = ROOT / "data" / "marketing.json"

DEFAULT_MODEL = "claude-sonnet-4-6"


SYSTEM_PROMPT = """You are a local marketing copywriter hired by a commercial real estate landlord to market vacant retail, shopping center, and mixed-use spaces directly to the communities they sit in. Your job is NOT to write broker-facing copy — that already exists. Your job is to write consumer- and community-facing copy that gets seen, shared, and clicked by:

  - Local residents who might tell a friend or forward it to a business owner they know
  - Local small-business owners scrolling Facebook community pages, Nextdoor, or Instagram
  - Franchise real estate directors or regional managers running LinkedIn searches for opportunities
  - Paid-ad responders searching Google for "retail space for lease near [neighborhood]"

Every piece of copy you write must feel LOCAL. Reference the actual neighborhood, the corridor (Easton Road, Route 611, Old York Road, Baltimore Pike, City Line Avenue, Roosevelt Boulevard, etc.), known adjacent landmarks, or the community character. If you don't know a specific local detail, describe the setting honestly rather than inventing one — but lean hard on the city/neighborhood name in every channel.

# Portfolio context
These are properties owned by Goodman Properties, a private commercial real estate owner with ~130 properties concentrated in the suburban Philadelphia market (Montgomery County, Bucks County, Chester County, Philadelphia, Delaware County), with scattered holdings in NJ, IN, MD, VA, WV, FL, and DE. Most are neighborhood shopping centers and retail pads. Many centers are grocery- or pharmacy-anchored.

# Per-channel rules

**facebook_local_post** (150-250 words, casual, conversational)
Written to be pasted into a local community Facebook group or the landlord's page. Lead with the neighborhood name. Mention the specific street. Talk about what kind of business would thrive there. End with a clear call to inquiry (email/phone/website). Use line breaks. Can use light emoji only if it would feel natural in a suburban community group — otherwise skip. Do NOT use hashtags; Facebook posts don't benefit from them the way Instagram does.

**nextdoor_post** (100-180 words, very neighborly)
Nextdoor posts read like a message from a neighbor, not an advertiser. Lead with a question or community-minded framing ("Know a local business that needs a storefront?..." or "For anyone wondering about that empty space on..."). Reference the exact street and cross-street if reasonable. No hashtags. No emoji. Short paragraphs. Invite replies.

**instagram_caption** (120-200 words + 8-12 hashtags)
Instagram is visual-first, so the caption's job is to add context to an implied photo. Open with a hook line. Reference the neighborhood explicitly. Include a brief "who this space is for" paragraph. End with a call-to-action and 8-12 hashtags mixing: neighborhood (#WillowGrove, #JenkintownPA, #BlueBellPA), category (#RetailForLease, #RetailSpace, #SmallBusiness, #PhillySuburbs), and broader (#CommercialRealEstate, #CRE). Hashtags go on their own lines at the end.

**linkedin_post** (150-250 words, professional)
Business audience. Written from the landlord/owner perspective. Lead with a specific, concrete claim (size, location, opportunity). Speak to brokers, franchise directors, and expansion-focused operators. Use short paragraphs. Close with a clear next step. No emoji. 1-3 relevant hashtags at the end (e.g., #CommercialRealEstate, #RetailLeasing, #[CityName]).

**google_search_ad** (strict character limits — ENFORCE THESE)
  - headline_1: up to 30 characters
  - headline_2: up to 30 characters
  - headline_3: up to 30 characters
  - description_1: up to 90 characters
  - description_2: up to 90 characters
Each headline is a complete phrase a searcher would click on. Include the city/neighborhood or SF number in at least one headline. Descriptions should expand on the value.

**facebook_ad** (strict character limits)
  - primary_text: up to 125 characters, the body text above the image
  - headline: up to 27 characters, the big headline under the image
  - description: up to 27 characters, the small description line
Write for a suburban/local audience browsing Facebook. Conversational.

**community_hooks** — an array of 3 SHORT localized hooks (max 15 words each). These are one-liners suitable for:
  - A sign in the vacant storefront window
  - The opening line of a cold email to a local franchisee
  - An SMS broadcast to a broker list
  Each hook must reference something specific about the neighborhood or property. Variety matters: one formal, one conversational, one community-minded.

**local_context** (2-3 sentences)
A factual framing of the immediate trade area / neighborhood character. What kind of community is this? Suburban, urban, working-class, affluent, family-oriented, commuter? What's the immediate corridor like? This is the context source all other channels draw from.

# What to reference for "local"
Every property comes with:
  - Full street address
  - City, state, zip
  - Property type
  - An AI-generated headline and description from an earlier pass (use these as additional context — they already identify landmarks, anchors, and trade area)
  - The leasing angle (one-sentence hook)

Use all of this. When the earlier description mentions "grocery-anchored" or names a co-tenant (Giant, Wawa, CVS), carry it through. When the city is Willow Grove, reference Willow Grove explicitly and by name in every channel. When the corridor is "Old York Road" or "Easton Road" or "Route 611," mention it by name. Specificity beats generic every time.

# What to avoid
- Generic CRE vocabulary: "prime location," "high-visibility," "state-of-the-art," "nestled," "unparalleled"
- Making up specific landmarks you don't know exist ("next to the famous Willow Grove diner") — if unsure, describe the corridor/community instead
- Hyping the space beyond its actual characteristics
- Treating Philadelphia, Willow Grove, and Evansville like the same trade area — they're not
- Repeating the exact same copy across channels; each channel has a different voice
- Exceeding character limits on Google/Facebook ad fields — these are strict API constraints, not suggestions

# How to think about the task
Read the input property. Identify: (1) what city/neighborhood this is, (2) what kind of trade area it represents, (3) who realistically opens a business here, (4) what the nearest corridor or landmark is that a local would recognize. Then write each channel in its own voice, using the shared local context. Enforce the character limits. Call the save_marketing_content tool exactly once with your output."""


MARKETING_TOOL = {
    "name": "save_marketing_content",
    "description": "Save locally-tailored digital marketing copy for a single property across multiple channels.",
    "input_schema": {
        "type": "object",
        "properties": {
            "local_context": {
                "type": "string",
                "description": "2-3 sentence factual framing of the neighborhood and trade area character.",
            },
            "facebook_local_post": {
                "type": "string",
                "description": "150-250 word casual post for a local community Facebook group or the landlord's page. No hashtags.",
            },
            "nextdoor_post": {
                "type": "string",
                "description": "100-180 word neighborly post written to look like a message from a neighbor. No hashtags, no emoji.",
            },
            "instagram_caption": {
                "type": "string",
                "description": "120-200 word Instagram caption ending with 8-12 hashtags on their own lines.",
            },
            "linkedin_post": {
                "type": "string",
                "description": "150-250 word professional post for brokers and franchise directors, with 1-3 hashtags at the end.",
            },
            "google_search_ad": {
                "type": "object",
                "description": "Google Ads responsive search ad fields, within strict character limits.",
                "properties": {
                    "headline_1": {"type": "string", "description": "Up to 30 characters."},
                    "headline_2": {"type": "string", "description": "Up to 30 characters."},
                    "headline_3": {"type": "string", "description": "Up to 30 characters."},
                    "description_1": {"type": "string", "description": "Up to 90 characters."},
                    "description_2": {"type": "string", "description": "Up to 90 characters."},
                },
                "required": ["headline_1", "headline_2", "headline_3", "description_1", "description_2"],
            },
            "facebook_ad": {
                "type": "object",
                "description": "Facebook/Meta paid ad fields, within strict character limits.",
                "properties": {
                    "primary_text": {"type": "string", "description": "Up to 125 characters."},
                    "headline": {"type": "string", "description": "Up to 27 characters."},
                    "description": {"type": "string", "description": "Up to 27 characters."},
                },
                "required": ["primary_text", "headline", "description"],
            },
            "community_hooks": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": {"type": "string"},
                "description": "Three short one-liners (max 15 words each) suitable for window signs, cold email opens, or SMS blasts.",
            },
        },
        "required": [
            "local_context",
            "facebook_local_post",
            "nextdoor_post",
            "instagram_caption",
            "linkedin_post",
            "google_search_ad",
            "facebook_ad",
            "community_hooks",
        ],
    },
}


def format_listing(rec: dict) -> str:
    l = rec["listing"]
    e = rec.get("enrichment") or {}
    lines = [
        f"Address: {l['a']}",
        f"City/State/ZIP: {l['c']}, {l['s']} {l['z']}",
        f"Property type: {l['t']}",
    ]
    sf = (l.get("sf") or "").strip()
    lines.append(f"Available square footage: {sf + ' SF' if sf else 'not publicly listed'}")

    if e.get("headline"):
        lines.append(f"Prior AI headline: {e['headline']}")
    if e.get("description"):
        lines.append(f"Prior AI description: {e['description']}")
    if e.get("leasing_angle"):
        lines.append(f"Prior leasing angle: {e['leasing_angle']}")

    lines.append(f"Source detail page: https://goodmanproperties.org{l['u']}")
    return "\n".join(lines)


def record_key(rec: dict) -> str:
    l = rec["listing"]
    return f"{l['a']}|{l['c']}|{l['s']}|{l['z']}|{l['u']}"


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


# Strict character limits for ad platforms. Violating these breaks bulk
# imports into Google Ads Editor or Meta Ads Manager, so we validate every
# record and retry-fix any violations before saving.
AD_LIMITS = {
    "google_search_ad": {
        "headline_1": 30,
        "headline_2": 30,
        "headline_3": 30,
        "description_1": 90,
        "description_2": 90,
    },
    "facebook_ad": {
        "primary_text": 125,
        "headline": 27,
        "description": 27,
    },
}


def validate_limits(marketing: dict) -> list[str]:
    """Return a list of human-readable violation strings, empty if clean.

    Also treats schema-shape violations (e.g. the model returning a string
    where a dict of ad fields was expected) as violations worth retrying."""
    violations = []
    for section, fields in AD_LIMITS.items():
        sec = marketing.get(section)
        if not isinstance(sec, dict):
            violations.append(
                f"{section} must be an object with fields {list(fields.keys())}, "
                f"not a {type(sec).__name__}"
            )
            continue
        for field, limit in fields.items():
            val = sec.get(field, "") or ""
            if not isinstance(val, str):
                violations.append(f"{section}.{field} must be a string")
                continue
            if len(val) > limit:
                violations.append(
                    f"{section}.{field} is {len(val)} characters; must be <= {limit}"
                )
    return violations


def hard_truncate(marketing: dict) -> None:
    """Final safety net: truncate any remaining over-limit strings in place.
    No-op for fields that aren't the expected shape."""
    for section, fields in AD_LIMITS.items():
        sec = marketing.get(section)
        if not isinstance(sec, dict):
            continue
        for field, limit in fields.items():
            val = sec.get(field, "") or ""
            if not isinstance(val, str) or len(val) <= limit:
                continue
            trimmed = val[:limit]
            space = trimmed.rfind(" ")
            if space >= int(limit * 0.7):
                sec[field] = trimmed[:space].rstrip()
            else:
                sec[field] = trimmed.rstrip()


def _call_model(client: Anthropic, model: str, messages: list) -> tuple[dict, dict, object]:
    resp = client.messages.create(
        model=model,
        max_tokens=3000,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[MARKETING_TOOL],
        tool_choice={"type": "tool", "name": "save_marketing_content"},
        messages=messages,
    )

    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "save_marketing_content":
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
            return block.input, usage, block

    raise RuntimeError(
        f"Model response did not contain a tool_use block. "
        f"Stop reason: {resp.stop_reason}"
    )


def generate_one(client: Anthropic, model: str, rec: dict) -> tuple[dict, dict, int]:
    """Generate marketing for one listing, validating ad char limits and
    retrying once with the violations surfaced if needed. Returns
    (marketing, merged_usage, retry_count)."""
    messages = [{"role": "user", "content": format_listing(rec)}]
    marketing, usage, first_block = _call_model(client, model, messages)

    violations = validate_limits(marketing)
    if not violations:
        return marketing, usage, 0

    # Retry once with the violations fed back as a tool_result turn. This
    # keeps the model's original reasoning in context and asks it to fix
    # only what's broken.
    messages.append({"role": "assistant", "content": [first_block]})
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": first_block.id,
                    "content": (
                        "The following fields exceed their ad-platform character limits:\n"
                        + "\n".join(f"  - {v}" for v in violations)
                        + "\n\nCall save_marketing_content again with ALL fields, "
                        "keeping everything the same EXCEPT rewriting the violating "
                        "fields so they fit within their limits. Do not simply truncate; "
                        "rewrite the copy to be genuinely shorter while preserving meaning."
                    ),
                }
            ],
        }
    )

    marketing2, usage2, _ = _call_model(client, model, messages)
    merged_usage = {k: usage[k] + usage2[k] for k in usage}
    # Apply hard truncation as final safety net in case the retry still missed
    hard_truncate(marketing2)
    return marketing2, merged_usage, 1


def main() -> int:
    load_dotenv(ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ERROR: ANTHROPIC_API_KEY not set. Check .env.",
            file=sys.stderr,
        )
        return 1

    if not ENRICHED_PATH.exists():
        print(
            f"ERROR: {ENRICHED_PATH.relative_to(ROOT)} not found. "
            f"Run scripts/enrich.py first.",
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

    records = json.loads(ENRICHED_PATH.read_text())
    print(f"Loaded {len(records)} enriched listings from {ENRICHED_PATH.relative_to(ROOT)}")

    results = load_existing(OUTPUT_PATH)
    if results:
        print(f"Resuming: {len(results)} listings already have marketing content")

    queue: list[dict] = []
    for rec in records:
        key = record_key(rec)
        if key in results:
            continue
        queue.append(rec)
        if limit is not None and len(queue) >= limit:
            break

    if not queue:
        print("Nothing to do — all listings already have marketing content.")
        return 0

    print(f"Generating marketing content for {len(queue)} listings with model={model}")
    print("-" * 72)

    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    retry_count = 0
    client = Anthropic()

    for i, rec in enumerate(queue, 1):
        l = rec["listing"]
        label = f"{l['a']}, {l['c']} {l['s']}"
        print(f"[{i:3d}/{len(queue)}] {label[:56]:56s}", end=" ", flush=True)

        try:
            marketing, usage, retries = generate_one(client, model, rec)
        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {e}")
            continue

        for k, v in usage.items():
            totals[k] += v
        retry_count += retries

        key = record_key(rec)
        results[key] = {
            "key": key,
            "listing": l,
            "marketing": marketing,
        }
        save_all(OUTPUT_PATH, results)

        retry_tag = f" [retry]" if retries else ""
        print(
            f"ok  in={usage['input_tokens']:4d} "
            f"out={usage['output_tokens']:4d} "
            f"cache_read={usage['cache_read_input_tokens']:5d}{retry_tag}"
        )

    print("-" * 72)
    print(f"Done. {len(results)} total marketing records -> {OUTPUT_PATH.relative_to(ROOT)}")
    print(
        f"Usage totals: input={totals['input_tokens']} "
        f"output={totals['output_tokens']} "
        f"cache_write={totals['cache_creation_input_tokens']} "
        f"cache_read={totals['cache_read_input_tokens']}"
    )
    print(f"Retries triggered by character-limit violations: {retry_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
