#!/usr/bin/env python3
"""
Build index.html from data/listings.json + data/enriched.json + data/marketing.json.

Produces a single self-contained HTML file with all data embedded inline.
Re-run any time data changes:

    .venv/bin/python scripts/build_page.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LISTINGS_PATH = ROOT / "data" / "listings.json"
ENRICHED_PATH = ROOT / "data" / "enriched.json"
MARKETING_PATH = ROOT / "data" / "marketing.json"
OUTPUT_PATH = ROOT / "index.html"


def listing_key(l: dict) -> str:
    return f"{l['a']}|{l['c']}|{l['s']}|{l['z']}|{l['u']}"


def _safe_embed(obj) -> str:
    return (
        json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
        .replace("</", "<\\/")
    )


# ---------------------------------------------------------------------------
# Mock pipeline data — simulates leases approaching expiry for the POC demo.
# Days are relative to build date so the countdown is always current.
# ---------------------------------------------------------------------------
MOCK_LEASES = [
    ("Planet Fitness",        88),
    ("Dollar Tree",           73),
    ("Subway",                58),
    ("Great Clips",           44),
    ("Verizon Wireless",      31),
    ("H&R Block",             19),
    ("State Farm Insurance",  11),
    ("UPS Store",              5),
]

MOCK_SF_FALLBACK = [4200, 1800, 950, 3100, 2400, 1200, 6500, 2800]


def build_pipeline(merged: list) -> list:
    """Pick 8 enriched listings spread across states and attach mock lease data."""
    today = date.today()

    by_state: dict = defaultdict(list)
    for l in merged:
        if l.get("e") and l.get("m"):
            by_state[l["s"]].append(l)

    candidates: list = []
    for s in ["PA", "NJ", "MD", "IN", "VA", "FL", "DE", "WV"]:
        if by_state[s]:
            candidates.append(by_state[s][0])
        if len(candidates) == 8:
            break

    # Fill remaining from PA if we didn't reach 8
    for l in by_state["PA"][1:]:
        if l not in candidates:
            candidates.append(l)
        if len(candidates) == 8:
            break

    listing_index = {listing_key(l): i for i, l in enumerate(merged)}

    pipeline = []
    for i, l in enumerate(candidates[:8]):
        tenant, days = MOCK_LEASES[i]
        lease_end = today + timedelta(days=days)
        key = listing_key(l)
        pipeline.append({
            "key": key,
            "listing_idx": listing_index[key],
            "a": l["a"],
            "c": l["c"],
            "s": l["s"],
            "sf": l.get("sf") or str(MOCK_SF_FALLBACK[i]),
            "tenant": tenant,
            "lease_end": lease_end.isoformat(),
            "days": days,
        })
    return pipeline


def main() -> None:
    listings = json.loads(LISTINGS_PATH.read_text())
    enriched_records = json.loads(ENRICHED_PATH.read_text())
    enriched_by_key = {r["key"]: r["enrichment"] for r in enriched_records}

    marketing_by_key: dict = {}
    if MARKETING_PATH.exists():
        marketing_records = json.loads(MARKETING_PATH.read_text())
        marketing_by_key = {r["key"]: r["marketing"] for r in marketing_records}

    merged = []
    missing_enrichment = 0
    missing_marketing = 0
    for l in listings:
        key = listing_key(l)
        e = enriched_by_key.get(key)
        m = marketing_by_key.get(key)
        if e is None:
            missing_enrichment += 1
        if m is None:
            missing_marketing += 1
        merged.append({**l, "e": e, "m": m})

    state_count = len({l["s"] for l in listings})
    subtitle = f"{len(listings)} properties across {state_count} states · Updated {date.today().strftime('%B %d, %Y')}"
    pipeline = build_pipeline(merged)

    html = (
        HTML_TEMPLATE
        .replace("__DATA_PLACEHOLDER__", _safe_embed(merged))
        .replace("__PIPELINE_PLACEHOLDER__", _safe_embed(pipeline))
        .replace("__SUBTITLE_PLACEHOLDER__", subtitle)
    )
    OUTPUT_PATH.write_text(html, encoding="utf-8")

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} ({size_kb:.0f} KB)")
    print(f"  Listings:       {len(merged)}")
    print(f"  Enriched:       {len(merged) - missing_enrichment}")
    print(f"  With marketing: {len(merged) - missing_marketing}")
    print(f"  Pipeline items: {len(pipeline)}")
    if missing_enrichment:
        print(f"  Missing enrichment: {missing_enrichment}")
    if missing_marketing:
        print(f"  Missing marketing: {missing_marketing}")


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Goodman Properties — AI-Enriched Listings</title>
<style>
  :root {
    --bg: #f6f5f1;
    --card: #ffffff;
    --ink: #1b2330;
    --muted: #5b6677;
    --line: #e5e2d8;
    --accent: #0f4c81;
    --chip: #eef1f6;
    --ai: #5a3fd6;
    --ai-bg: #f3f0ff;
    --avail: #1f6f33;
    --avail-bg: #e8f5e9;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg);
    color: var(--ink);
  }

  /* ── Hero ── */
  header.hero {
    background: linear-gradient(135deg, #0f4c81 0%, #1b6aa8 100%);
    color: #fff;
    padding: 48px 24px 40px;
  }
  .wrap { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
  header.hero h1 { margin: 0 0 6px; font-size: 28px; letter-spacing: -0.01em; }
  header.hero p { margin: 0; opacity: 0.9; font-size: 14px; }
  header.hero a { color: #fff; }
  header.hero .ai-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    color: #fff;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 5px 12px;
    border-radius: 999px;
    margin-top: 14px;
  }
  .view-toggle {
    display: inline-flex;
    background: rgba(255,255,255,0.15);
    border-radius: 999px;
    padding: 3px;
    margin-top: 16px;
  }
  .view-toggle button {
    font: inherit;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 7px 16px;
    border: none;
    border-radius: 999px;
    color: rgba(255,255,255,0.85);
    background: transparent;
    cursor: pointer;
  }
  .view-toggle button.active { background: #fff; color: var(--accent); }

  /* ── Controls ── */
  .controls {
    background: #fff;
    border-bottom: 1px solid var(--line);
    padding: 16px 0;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .controls .row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
  .controls input, .controls select {
    font: inherit;
    padding: 9px 12px;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #fff;
    color: var(--ink);
    min-width: 0;
  }
  .controls input[type="search"] { flex: 1 1 280px; }
  .controls select { flex: 0 0 auto; }
  .count { margin-left: auto; color: var(--muted); font-size: 13px; white-space: nowrap; }

  /* ── Views ── */
  .view { display: none; }
  .view.active { display: block; }
  main.wrap { padding-top: 28px; padding-bottom: 80px; }

  /* ── Listing cards ── */
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
  .card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 20px 20px 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    transition: transform 0.12s, box-shadow 0.12s, border-color 0.12s;
  }
  .card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(15,76,129,.10); border-color: #cfd6e0; }
  .headline { font-size: 15px; font-weight: 700; line-height: 1.35; color: var(--ink); }
  .addr-row { color: var(--muted); font-size: 12px; line-height: 1.4; }
  .addr-row .addr { font-weight: 500; color: var(--ink); }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip { background: var(--chip); color: var(--ink); font-size: 11px; font-weight: 600; padding: 4px 8px; border-radius: 999px; letter-spacing: .02em; text-transform: uppercase; }
  .chip.state { background: var(--accent); color: #fff; }
  .chip.avail { background: var(--avail-bg); color: var(--avail); }
  .sf { font-size: 13px; color: var(--muted); }
  .sf strong { color: var(--ink); font-weight: 600; }
  .description { font-size: 13px; line-height: 1.55; color: var(--muted); }
  .angle { font-size: 12px; color: var(--ai); background: var(--ai-bg); border-left: 3px solid var(--ai); padding: 8px 12px; border-radius: 4px; font-style: italic; line-height: 1.45; }
  details.tenants { border-top: 1px solid var(--line); padding-top: 10px; margin-top: 4px; }
  details.tenants summary { cursor: pointer; font-size: 11px; font-weight: 700; color: var(--ai); list-style: none; padding: 4px 0; user-select: none; letter-spacing: .05em; text-transform: uppercase; }
  details.tenants summary::-webkit-details-marker { display: none; }
  details.tenants summary::before { content: "▸  "; display: inline-block; width: 16px; }
  details.tenants[open] summary::before { content: "▾  "; }
  details.tenants ul { list-style: none; padding: 6px 0 0; margin: 0; }
  details.tenants li { padding: 12px 0; border-top: 1px dashed var(--line); }
  details.tenants li:first-child { border-top: none; }
  .tenant-cat { font-size: 13px; font-weight: 700; color: var(--ink); }
  .tenant-brands { font-size: 11px; color: var(--ai); margin: 4px 0 6px; letter-spacing: .02em; font-weight: 500; }
  .tenant-why { font-size: 12px; color: var(--muted); line-height: 1.5; }
  details.marketing { border-top: 1px solid var(--line); padding-top: 10px; margin-top: 2px; }
  details.marketing > summary { cursor: pointer; font-size: 11px; font-weight: 700; color: var(--ai); list-style: none; padding: 4px 0; user-select: none; letter-spacing: .05em; text-transform: uppercase; }
  details.marketing > summary::-webkit-details-marker { display: none; }
  details.marketing > summary::before { content: "▸  "; display: inline-block; width: 16px; }
  details.marketing[open] > summary::before { content: "▾  "; }
  .channel-tabs { display: flex; flex-wrap: wrap; gap: 4px; margin: 10px 0 8px; }
  .channel-tab { font-size: 10px; font-weight: 700; padding: 5px 9px; border-radius: 999px; border: 1px solid var(--line); background: #fff; color: var(--muted); cursor: pointer; letter-spacing: .03em; text-transform: uppercase; font-family: inherit; }
  .channel-tab:hover { border-color: var(--ai); color: var(--ai); }
  .channel-tab.active { background: var(--ai); color: #fff; border-color: var(--ai); }
  .channel-panel { display: none; }
  .channel-panel.active { display: block; }
  .local-context { font-size: 11px; color: var(--muted); font-style: italic; background: #faf9f5; padding: 8px 10px; border-radius: 4px; margin-bottom: 10px; line-height: 1.5; }
  .post-body { font-size: 12px; line-height: 1.55; color: var(--ink); background: #fafafa; border: 1px solid var(--line); border-radius: 6px; padding: 10px 12px; white-space: pre-wrap; word-wrap: break-word; max-height: 260px; overflow-y: auto; }
  .ad-field { font-size: 12px; line-height: 1.5; padding: 6px 10px; border-left: 2px solid var(--line); margin: 6px 0; }
  .ad-field .label { font-size: 9px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; display: block; margin-bottom: 2px; }
  .ad-field .value { color: var(--ink); }
  .ad-field .len { color: var(--muted); font-size: 10px; margin-left: 6px; }
  .hooks { margin: 0; padding: 0; list-style: none; }
  .hooks li { font-size: 12px; line-height: 1.5; padding: 6px 0 6px 10px; border-left: 2px solid var(--ai); margin-bottom: 6px; color: var(--ink); }
  .post-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
  .copy-btn { display: inline-block; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; padding: 5px 10px; border: 1px solid var(--ai); color: var(--ai); background: #fff; border-radius: 999px; cursor: pointer; font-family: inherit; }
  .copy-btn:hover { background: var(--ai); color: #fff; }
  .copy-btn.copied { background: var(--avail); color: #fff; border-color: var(--avail); }
  .card a.more { margin-top: auto; display: inline-block; color: var(--accent); font-size: 13px; font-weight: 600; text-decoration: none; padding-top: 6px; }
  .card a.more:hover { text-decoration: underline; }
  .empty { grid-column: 1/-1; text-align: center; padding: 60px 20px; color: var(--muted); }

  /* ── Pipeline view ── */
  .workflow-steps {
    display: flex;
    align-items: center;
    gap: 0;
    background: #fff;
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 24px;
    overflow-x: auto;
  }
  .wf-step {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 180px;
  }
  .wf-num {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--accent);
    color: #fff;
    font-size: 15px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .wf-text strong { display: block; font-size: 13px; font-weight: 700; color: var(--ink); }
  .wf-text span { font-size: 11px; color: var(--muted); }
  .wf-arrow {
    font-size: 20px;
    color: var(--line);
    padding: 0 12px;
    flex-shrink: 0;
  }

  .pipe-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }
  .pipe-stat {
    background: #fff;
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 16px 18px;
  }
  .pipe-stat-num { font-size: 28px; font-weight: 800; color: var(--ink); line-height: 1; }
  .pipe-stat-label { font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin-top: 6px; }

  .pipe-card {
    background: #fff;
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
    display: grid;
    grid-template-columns: 100px 1fr auto;
    gap: 20px;
    align-items: center;
    transition: box-shadow 0.12s;
  }
  .pipe-card:hover { box-shadow: 0 4px 16px rgba(15,76,129,.08); }
  .pipe-card.approved { opacity: 0.75; }

  .pipe-days {
    border-radius: 10px;
    padding: 14px 10px;
    text-align: center;
  }
  .pipe-days-num { font-size: 32px; font-weight: 800; line-height: 1; }
  .pipe-days-label { font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; margin-top: 2px; }
  .pipe-urgency { font-size: 9px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; margin-top: 4px; opacity: .7; }

  .pipe-headline { font-size: 15px; font-weight: 700; color: var(--ink); margin-bottom: 3px; }
  .pipe-addr { font-size: 12px; color: var(--muted); margin-bottom: 6px; }
  .pipe-meta { font-size: 12px; color: var(--muted); }
  .pipe-meta strong { color: var(--ink); }

  .pipe-action { display: flex; flex-direction: column; align-items: flex-end; gap: 10px; }
  .pipe-status-badge {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .05em;
    text-transform: uppercase;
    padding: 5px 10px;
    border-radius: 999px;
    white-space: nowrap;
  }
  .pipe-status-badge.content-ready { background: #fdf4d3; color: #7a5c00; }
  .pipe-status-badge.approved { background: var(--avail-bg); color: var(--avail); }

  .pipe-approve-btn {
    font: inherit;
    font-size: 12px;
    font-weight: 700;
    padding: 10px 18px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    white-space: nowrap;
    letter-spacing: .02em;
  }
  .pipe-approve-btn:hover { background: #0d3f6a; }

  /* ── Approval modal ── */
  .modal-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(15,20,30,.55);
    z-index: 50;
    align-items: flex-start;
    justify-content: center;
    padding: 40px 16px;
    overflow-y: auto;
  }
  .modal-overlay.open { display: flex; }
  .modal-box {
    background: #fff;
    border-radius: 16px;
    width: 100%;
    max-width: 760px;
    box-shadow: 0 20px 60px rgba(0,0,0,.25);
    display: flex;
    flex-direction: column;
    max-height: calc(100vh - 80px);
    overflow: hidden;
  }
  .modal-header {
    padding: 24px 28px 20px;
    border-bottom: 1px solid var(--line);
    flex-shrink: 0;
  }
  .modal-header h2 { margin: 0 0 4px; font-size: 18px; color: var(--ink); }
  .modal-header .modal-sub { font-size: 13px; color: var(--muted); }
  .modal-close {
    position: absolute;
    top: 16px;
    right: 20px;
    font: inherit;
    font-size: 22px;
    line-height: 1;
    background: none;
    border: none;
    cursor: pointer;
    color: var(--muted);
    padding: 4px 8px;
  }
  .modal-close:hover { color: var(--ink); }

  .modal-steps {
    display: flex;
    align-items: center;
    padding: 16px 28px;
    background: #f9f8fc;
    border-bottom: 1px solid var(--line);
    gap: 0;
    flex-shrink: 0;
    overflow-x: auto;
  }
  .ms-step {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 130px;
  }
  .ms-num {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    font-size: 12px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .ms-num.done { background: var(--avail); color: #fff; }
  .ms-num.current { background: var(--accent); color: #fff; }
  .ms-num.pending { background: var(--line); color: var(--muted); }
  .ms-label { font-size: 11px; font-weight: 600; color: var(--muted); }
  .ms-label.current { color: var(--accent); }
  .ms-label.done { color: var(--avail); }
  .ms-arrow { font-size: 16px; color: var(--line); padding: 0 8px; flex-shrink: 0; }

  .modal-body {
    padding: 24px 28px;
    overflow-y: auto;
    flex: 1;
  }
  .modal-body h3 { font-size: 13px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin: 0 0 12px; }

  .modal-footer {
    padding: 20px 28px;
    border-top: 1px solid var(--line);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-shrink: 0;
    background: #fff;
  }
  .modal-footer-note { font-size: 12px; color: var(--muted); }
  .modal-approve-btn {
    font: inherit;
    font-size: 14px;
    font-weight: 700;
    padding: 13px 28px;
    background: var(--avail);
    color: #fff;
    border: none;
    border-radius: 10px;
    cursor: pointer;
    letter-spacing: .02em;
    white-space: nowrap;
  }
  .modal-approve-btn:hover { background: #175929; }
  .modal-approve-btn:disabled { opacity: .6; cursor: wait; }

  /* ── Toast ── */
  .toast {
    position: fixed;
    bottom: 28px;
    right: 28px;
    background: var(--ink);
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    padding: 13px 20px;
    border-radius: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,.2);
    opacity: 0;
    transform: translateY(10px);
    transition: opacity .22s, transform .22s;
    pointer-events: none;
    z-index: 200;
    max-width: 340px;
  }
  .toast.show { opacity: 1; transform: translateY(0); }
  .toast.success { background: var(--avail); }

  footer { text-align: center; color: var(--muted); font-size: 12px; padding: 24px 16px 48px; max-width: 720px; margin: 0 auto; }
  footer a { color: var(--muted); }

  @media (max-width: 600px) {
    .pipe-card { grid-template-columns: 80px 1fr; }
    .pipe-action { grid-column: 1 / -1; flex-direction: row; align-items: center; }
    .modal-footer { flex-direction: column; }
    .modal-approve-btn { width: 100%; }
  }
</style>
</head>
<body>

<header class="hero">
  <div class="wrap">
    <h1>Goodman Properties</h1>
    <p>__SUBTITLE_PLACEHOLDER__</p>
    <div class="ai-badge">AI enrichment + local marketing content · Claude Sonnet 4.6</div>
    <div>
      <div class="view-toggle">
        <button id="btn-listings" class="active" onclick="showView('listings')">All Listings</button>
        <button id="btn-pipeline" onclick="showView('pipeline')">Vacancy Pipeline</button>
      </div>
    </div>
  </div>
</header>

<div class="controls" id="listing-controls">
  <div class="wrap row">
    <input id="q" type="search" placeholder="Search address, city, zip, or tenant category…" autocomplete="off">
    <select id="state"><option value="">All states</option></select>
    <select id="type"><option value="">All types</option></select>
    <select id="avail">
      <option value="">Availability: any</option>
      <option value="yes">Space available</option>
    </select>
    <span class="count" id="count"></span>
  </div>
</div>

<main class="wrap">

  <!-- All Listings view -->
  <div id="view-listings" class="view active">
    <div class="grid" id="grid"></div>
  </div>

  <!-- Vacancy Pipeline view -->
  <div id="view-pipeline" class="view">

    <!-- 3-step workflow explanation -->
    <div class="workflow-steps">
      <div class="wf-step">
        <div class="wf-num">1</div>
        <div class="wf-text">
          <strong>90-Day Lease Alert</strong>
          <span>System detects lease nearing end &amp; triggers workflow</span>
        </div>
      </div>
      <div class="wf-arrow">→</div>
      <div class="wf-step">
        <div class="wf-num">2</div>
        <div class="wf-text">
          <strong>AI Content Generated</strong>
          <span>Listing copy, social posts &amp; ads created automatically</span>
        </div>
      </div>
      <div class="wf-arrow">→</div>
      <div class="wf-step">
        <div class="wf-num">3</div>
        <div class="wf-text">
          <strong>Approve &amp; Schedule</strong>
          <span>One click publishes across all channels on your schedule</span>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="pipe-stats" id="pipe-stats"></div>

    <!-- Pipeline cards -->
    <div id="pipe-list"></div>

  </div>

</main>

<footer>
  Listings sourced from <a href="https://goodmanproperties.org/our-properties/" target="_blank" rel="noopener">goodmanproperties.org</a>.
  AI enrichment generated by Claude Sonnet 4.6 — verify before use.
</footer>

<!-- Approval modal -->
<div class="modal-overlay" id="approve-modal">
  <div class="modal-box" style="position:relative">
    <button class="modal-close" onclick="closeModal()">✕</button>
    <div class="modal-header">
      <h2 id="modal-title"></h2>
      <div class="modal-sub" id="modal-sub"></div>
    </div>
    <div class="modal-steps">
      <div class="ms-step">
        <div class="ms-num done">✓</div>
        <div class="ms-label done">Lease Alert Triggered</div>
      </div>
      <div class="ms-arrow">→</div>
      <div class="ms-step">
        <div class="ms-num done">✓</div>
        <div class="ms-label done">Content Generated</div>
      </div>
      <div class="ms-arrow">→</div>
      <div class="ms-step">
        <div class="ms-num current">3</div>
        <div class="ms-label current">Your approval needed</div>
      </div>
    </div>
    <div class="modal-body">
      <h3>AI-Generated Marketing Content</h3>
      <div id="modal-content"></div>
    </div>
    <div class="modal-footer">
      <div class="modal-footer-note">Approving will schedule posts across Facebook, Instagram, and LinkedIn.</div>
      <button class="modal-approve-btn" id="modal-approve-btn">Approve &amp; Schedule All Posts</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const BASE = "https://goodmanproperties.org";
const LISTINGS  = __DATA_PLACEHOLDER__;
const PIPELINE  = __PIPELINE_PLACEHOLDER__;

const STATE_NAMES = {
  PA:"Pennsylvania", NJ:"New Jersey", IN:"Indiana", MD:"Maryland",
  VA:"Virginia", WV:"West Virginia", FL:"Florida", DE:"Delaware"
};

// ── Utilities ────────────────────────────────────────────────────────────────

function esc(str) {
  return String(str == null ? "" : str).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
}

function searchBlob(l) {
  const parts = [l.a, l.c, l.s, l.z, l.t];
  const e = l.e;
  if (e) {
    parts.push(e.headline||"", e.description||"", e.leasing_angle||"");
    if (Array.isArray(e.ideal_tenants)) {
      for (const t of e.ideal_tenants) {
        parts.push(t.category||"");
        if (Array.isArray(t.example_brands)) parts.push(...t.example_brands);
        parts.push(t.why||"");
      }
    }
  }
  const m = l.m;
  if (m) {
    parts.push(m.local_context||"", m.facebook_local_post||"", m.nextdoor_post||"");
    parts.push(m.instagram_caption||"", m.linkedin_post||"");
    if (Array.isArray(m.community_hooks)) parts.push(...m.community_hooks);
  }
  return parts.join(" ").toLowerCase();
}

// ── Toast ────────────────────────────────────────────────────────────────────

const toastEl = document.getElementById("toast");
let toastTimer;
function showToast(msg, type="") {
  toastEl.textContent = msg;
  toastEl.className = "toast show" + (type ? " " + type : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 4000);
}

// ── View switching ────────────────────────────────────────────────────────────

window.showView = function(which) {
  document.getElementById("view-listings").classList.toggle("active", which === "listings");
  document.getElementById("view-pipeline").classList.toggle("active", which === "pipeline");
  document.getElementById("listing-controls").style.display = which === "listings" ? "" : "none";
  document.getElementById("btn-listings").classList.toggle("active", which === "listings");
  document.getElementById("btn-pipeline").classList.toggle("active", which === "pipeline");
  if (which === "pipeline") renderPipeline();
};

// ── Copy to clipboard ────────────────────────────────────────────────────────

window.copyText = function(btn) {
  const text = btn.closest(".channel-panel").querySelector(".post-body").textContent;
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = "Copied";
    btn.classList.add("copied");
    setTimeout(() => { btn.textContent = orig; btn.classList.remove("copied"); }, 1500);
  });
};

// ── Channel tabs ─────────────────────────────────────────────────────────────

window.showChannel = function(btn, panelId) {
  const container = btn.closest("details.marketing, .modal-marketing");
  container.querySelectorAll(".channel-tab").forEach(t => t.classList.remove("active"));
  container.querySelectorAll(".channel-panel").forEach(p => p.classList.remove("active"));
  btn.classList.add("active");
  container.querySelector("#" + panelId).classList.add("active");
};

let cardCounter = 0;
function cardId() { return "c" + (cardCounter++); }

// ── Marketing content renderer ────────────────────────────────────────────────

function renderMarketing(m, uid, wrapClass) {
  if (!m) return "";
  const safe = s => esc(s||"");
  const wrap = wrapClass || "marketing";
  const tabs = [], panels = [];

  function addTab(key, label, bodyHtml) {
    const pid = uid + "-" + key;
    const first = tabs.length === 0;
    tabs.push(`<button class="channel-tab${first?" active":""}" onclick="showChannel(this,'${pid}')">${label}</button>`);
    panels.push(`<div class="channel-panel${first?" active":""}" id="${pid}">${bodyHtml}<div class="post-actions"><button class="copy-btn" onclick="copyText(this)">Copy</button></div></div>`);
  }

  const post = text => `<div class="post-body">${safe(text)}</div>`;

  if (m.facebook_local_post) addTab("fb",  "Facebook",  post(m.facebook_local_post));
  if (m.nextdoor_post)       addTab("nd",  "Nextdoor",  post(m.nextdoor_post));
  if (m.instagram_caption)   addTab("ig",  "Instagram", post(m.instagram_caption));
  if (m.linkedin_post)       addTab("li",  "LinkedIn",  post(m.linkedin_post));

  if (m.google_search_ad && typeof m.google_search_ad === "object") {
    const a = m.google_search_ad;
    const f = (lbl,val,lim) => `<div class="ad-field"><span class="label">${lbl}<span class="len">${(val||"").length}/${lim}</span></span><span class="value">${safe(val)}</span></div>`;
    addTab("gad","Google Ad",`<div class="post-body">${f("Headline 1",a.headline_1,30)}${f("Headline 2",a.headline_2,30)}${f("Headline 3",a.headline_3,30)}${f("Description 1",a.description_1,90)}${f("Description 2",a.description_2,90)}</div>`);
  }
  if (m.facebook_ad && typeof m.facebook_ad === "object") {
    const a = m.facebook_ad;
    const f = (lbl,val,lim) => `<div class="ad-field"><span class="label">${lbl}<span class="len">${(val||"").length}/${lim}</span></span><span class="value">${safe(val)}</span></div>`;
    addTab("fad","FB Ad",`<div class="post-body">${f("Primary Text",a.primary_text,125)}${f("Headline",a.headline,27)}${f("Description",a.description,27)}</div>`);
  }
  if (Array.isArray(m.community_hooks) && m.community_hooks.length) {
    addTab("hk","Hooks",`<div class="post-body"><ul class="hooks">${m.community_hooks.map(h=>`<li>${safe(h)}</li>`).join("")}</ul></div>`);
  }

  if (!tabs.length) return "";
  const ctx = m.local_context ? `<div class="local-context">${safe(m.local_context)}</div>` : "";

  if (wrap === "modal") {
    return `<div class="modal-marketing">${ctx}<div class="channel-tabs">${tabs.join("")}</div>${panels.join("")}</div>`;
  }
  return `<details class="${wrap}"><summary>Local Marketing Content (${tabs.length})</summary>${ctx}<div class="channel-tabs">${tabs.join("")}</div>${panels.join("")}</details>`;
}

// ── Listings view ─────────────────────────────────────────────────────────────

const grid = document.getElementById("grid");
const q = document.getElementById("q");
const stateSel = document.getElementById("state");
const typeSel = document.getElementById("type");
const availSel = document.getElementById("avail");
const countEl = document.getElementById("count");

function populate(sel, values, labelFn) {
  [...values].sort().forEach(v => {
    const o = document.createElement("option");
    o.value = v; o.textContent = labelFn ? labelFn(v) : v;
    sel.appendChild(o);
  });
}
populate(stateSel, new Set(LISTINGS.map(l=>l.s)), s => STATE_NAMES[s]||s);
populate(typeSel,  new Set(LISTINGS.map(l=>l.t)));

function render() {
  const query = q.value.trim().toLowerCase();
  const st = stateSel.value, tp = typeSel.value, av = availSel.value;
  const filtered = LISTINGS.filter(l => {
    if (st && l.s!==st) return false;
    if (tp && l.t!==tp) return false;
    if (av==="yes" && !l.sf) return false;
    if (query && !searchBlob(l).includes(query)) return false;
    return true;
  });
  countEl.textContent = `${filtered.length} of ${LISTINGS.length} listings`;
  if (!filtered.length) { grid.innerHTML = '<div class="empty">No listings match your filters.</div>'; return; }

  cardCounter = 0;
  grid.innerHTML = filtered.map(l => {
    const e = l.e, uid = cardId();
    const headline = e?.headline || l.a;
    const availChip = l.sf ? '<span class="chip avail">Available</span>' : '';
    const description = e?.description ? `<div class="description">${esc(e.description)}</div>` : '';
    const angle = e?.leasing_angle ? `<div class="angle">${esc(e.leasing_angle)}</div>` : '';
    const tenants = (e && Array.isArray(e.ideal_tenants) && e.ideal_tenants.length)
      ? `<details class="tenants"><summary>Ideal Tenants (${e.ideal_tenants.length})</summary><ul>${e.ideal_tenants.map(t=>`<li><div class="tenant-cat">${esc(t.category)}</div><div class="tenant-brands">${esc((t.example_brands||[]).join(" · "))}</div><div class="tenant-why">${esc(t.why)}</div></li>`).join("")}</ul></details>`
      : '';
    return `<article class="card">
      <div class="headline">${esc(headline)}</div>
      <div class="addr-row"><span class="addr">${esc(l.a)}</span> · ${esc(l.c)}, ${esc(l.s)} ${esc(l.z)}</div>
      <div class="chips"><span class="chip state">${esc(l.s)}</span><span class="chip">${esc(l.t)}</span>${availChip}</div>
      ${l.sf ? `<div class="sf">Available: <strong>${esc(l.sf)} SF</strong></div>` : ''}
      ${description}${angle}${tenants}${renderMarketing(l.m, uid)}
      <a class="more" href="${BASE}${esc(l.u)}" target="_blank" rel="noopener">View source details →</a>
    </article>`;
  }).join("");
}
q.addEventListener("input", render);
stateSel.addEventListener("change", render);
typeSel.addEventListener("change", render);
availSel.addEventListener("change", render);

// ── Pipeline state ────────────────────────────────────────────────────────────

const pipeState = {
  get approved() { return JSON.parse(localStorage.getItem("pipe_approved")||"[]"); },
  approve(key) {
    const a = this.approved;
    if (!a.includes(key)) { a.push(key); localStorage.setItem("pipe_approved", JSON.stringify(a)); }
  },
  isApproved(key) { return this.approved.includes(key); },
  reset() { localStorage.removeItem("pipe_approved"); }
};

function daysStyle(days) {
  if (days <=  7) return {bg:"#fde7e7", color:"#8a1f1f", label:"CRITICAL"};
  if (days <= 14) return {bg:"#fde7e7", color:"#8a1f1f", label:"URGENT"};
  if (days <= 30) return {bg:"#fef3e2", color:"#c45d00", label:"URGENT"};
  if (days <= 60) return {bg:"#fdfae3", color:"#7a5c00", label:"UPCOMING"};
  return {bg:"#e8f5f0", color:"#1f6f33", label:"PIPELINE"};
}

// ── Pipeline view ─────────────────────────────────────────────────────────────

function renderPipeline() {
  const statsEl = document.getElementById("pipe-stats");
  const listEl  = document.getElementById("pipe-list");
  const approved = pipeState.approved;

  const total        = PIPELINE.length;
  const approvedCount = PIPELINE.filter(p => pipeState.isApproved(p.key)).length;
  const pendingCount  = total - approvedCount;
  const criticalCount = PIPELINE.filter(p => p.days <= 30 && !pipeState.isApproved(p.key)).length;

  statsEl.innerHTML = `
    <div class="pipe-stat">
      <div class="pipe-stat-num">${total}</div>
      <div class="pipe-stat-label">Leases Expiring<br>Within 90 Days</div>
    </div>
    <div class="pipe-stat">
      <div class="pipe-stat-num" style="color:#c45d00">${pendingCount}</div>
      <div class="pipe-stat-label">Awaiting<br>Owner Approval</div>
    </div>
    <div class="pipe-stat">
      <div class="pipe-stat-num" style="color:var(--avail)">${approvedCount}</div>
      <div class="pipe-stat-label">Approved &amp;<br>Scheduled</div>
    </div>
    <div class="pipe-stat">
      <div class="pipe-stat-num" style="color:#8a1f1f">${criticalCount}</div>
      <div class="pipe-stat-label">Critical<br>(≤ 30 Days)</div>
    </div>`;

  const sorted = [...PIPELINE].sort((a,b) => a.days - b.days);

  listEl.innerHTML = sorted.map(p => {
    const listing   = LISTINGS[p.listing_idx];
    const isApproved = pipeState.isApproved(p.key);
    const leaseDate  = new Date(p.lease_end).toLocaleDateString([], {month:"long", day:"numeric", year:"numeric"});
    const sf         = p.sf ? p.sf + " SF" : "";
    const headline   = listing.e?.headline || listing.a;

    if (isApproved) {
      return `<div class="pipe-card approved">
        <div class="pipe-days" style="background:var(--avail-bg);color:var(--avail)">
          <div class="pipe-days-num" style="font-size:22px">✓</div>
          <div class="pipe-days-label">DONE</div>
        </div>
        <div class="pipe-info">
          <div class="pipe-headline">${esc(headline)}</div>
          <div class="pipe-addr">${esc(p.a)} · ${esc(p.c)}, ${esc(p.s)}</div>
          <div class="pipe-meta">Current tenant: <strong>${esc(p.tenant)}</strong> · Lease ends ${leaseDate}${sf ? " · " + esc(sf) : ""}</div>
        </div>
        <div class="pipe-action">
          <div class="pipe-status-badge approved">✓ Posts Scheduled</div>
        </div>
      </div>`;
    }

    const ds = daysStyle(p.days);
    return `<div class="pipe-card">
      <div class="pipe-days" style="background:${ds.bg};color:${ds.color}">
        <div class="pipe-days-num">${p.days}</div>
        <div class="pipe-days-label">DAYS</div>
        <div class="pipe-urgency">${ds.label}</div>
      </div>
      <div class="pipe-info">
        <div class="pipe-headline">${esc(headline)}</div>
        <div class="pipe-addr">${esc(p.a)} · ${esc(p.c)}, ${esc(p.s)}</div>
        <div class="pipe-meta">Current tenant: <strong>${esc(p.tenant)}</strong> · Lease ends ${leaseDate}${sf ? " · " + esc(sf) : ""}</div>
      </div>
      <div class="pipe-action">
        <div class="pipe-status-badge content-ready">Content Ready</div>
        <button class="pipe-approve-btn" onclick="openModal('${esc(p.key)}')">Review &amp; Approve →</button>
      </div>
    </div>`;
  }).join("");
}

// ── Approval modal ────────────────────────────────────────────────────────────

let _modalKey = null;

window.openModal = function(key) {
  const p = PIPELINE.find(x => x.key === key);
  if (!p) return;
  const listing  = LISTINGS[p.listing_idx];
  const leaseDate = new Date(p.lease_end).toLocaleDateString([], {month:"long", day:"numeric", year:"numeric"});
  _modalKey = key;

  document.getElementById("modal-title").textContent = listing.e?.headline || listing.a;
  document.getElementById("modal-sub").textContent =
    `${p.a} · ${p.c}, ${p.s}  ·  Current tenant: ${p.tenant}  ·  Lease ends ${leaseDate} (${p.days} days)`;

  cardCounter = 1000;
  document.getElementById("modal-content").innerHTML = renderMarketing(listing.m, cardId(), "modal");

  const btn = document.getElementById("modal-approve-btn");
  btn.textContent = "Approve & Schedule All Posts";
  btn.disabled = false;

  document.getElementById("approve-modal").classList.add("open");
  document.body.style.overflow = "hidden";
};

window.closeModal = function() {
  document.getElementById("approve-modal").classList.remove("open");
  document.body.style.overflow = "";
  _modalKey = null;
};

document.getElementById("approve-modal").addEventListener("click", function(e) {
  if (e.target === this) closeModal();
});

document.getElementById("modal-approve-btn").addEventListener("click", function() {
  if (!_modalKey) return;
  this.textContent = "Scheduling posts…";
  this.disabled = true;

  setTimeout(() => {
    pipeState.approve(_modalKey);
    closeModal();
    renderPipeline();
    showToast("✓ All posts approved and scheduled across Facebook, Instagram & LinkedIn", "success");
  }, 1400);
});

// ── Init ──────────────────────────────────────────────────────────────────────

render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
