#!/usr/bin/env python3
"""
Build index.html from data/listings.json + data/enriched.json + data/marketing.json.

Produces a single self-contained HTML file with all data embedded inline,
so it opens with a double-click (no local server needed). Re-run this
any time the enrichment or marketing data changes:

    .venv/bin/python scripts/build_page.py
"""
from __future__ import annotations

import json
from datetime import date
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
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
        .replace("</", "<\\/")
    )


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

    html = (
        HTML_TEMPLATE
        .replace("__DATA_PLACEHOLDER__", _safe_embed(merged))
        .replace("__SUBTITLE_PLACEHOLDER__", subtitle)
    )
    OUTPUT_PATH.write_text(html, encoding="utf-8")

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} ({size_kb:.0f} KB)")
    print(f"  Listings:       {len(merged)}")
    print(f"  Enriched:       {len(merged) - missing_enrichment}")
    print(f"  With marketing: {len(merged) - missing_marketing}")
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
  header.hero {
    background: linear-gradient(135deg, #0f4c81 0%, #1b6aa8 100%);
    color: #fff;
    padding: 48px 24px 40px;
  }
  .wrap { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
  header.hero .wrap { padding: 0 24px; }
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

  /* Search + filter bar */
  .controls {
    background: #fff;
    border-bottom: 1px solid var(--line);
    padding: 16px 0;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .controls .row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
  }
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
  .count {
    margin-left: auto;
    color: var(--muted);
    font-size: 13px;
    white-space: nowrap;
  }

  /* Listing cards */
  main.wrap { padding-top: 28px; padding-bottom: 64px; }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 16px;
  }
  .card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 20px 20px 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
  }
  .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(15, 76, 129, 0.10);
    border-color: #cfd6e0;
  }
  .headline { font-size: 15px; font-weight: 700; line-height: 1.35; color: var(--ink); }
  .addr-row { color: var(--muted); font-size: 12px; line-height: 1.4; }
  .addr-row .addr { font-weight: 500; color: var(--ink); }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip {
    background: var(--chip);
    color: var(--ink);
    font-size: 11px;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 999px;
    letter-spacing: 0.02em;
    text-transform: uppercase;
  }
  .chip.state { background: var(--accent); color: #fff; }
  .chip.avail { background: var(--avail-bg); color: var(--avail); }
  .sf { font-size: 13px; color: var(--muted); }
  .sf strong { color: var(--ink); font-weight: 600; }
  .description { font-size: 13px; line-height: 1.55; color: var(--muted); }
  .angle {
    font-size: 12px;
    color: var(--ai);
    background: var(--ai-bg);
    border-left: 3px solid var(--ai);
    padding: 8px 12px;
    border-radius: 4px;
    font-style: italic;
    line-height: 1.45;
  }
  details.tenants { border-top: 1px solid var(--line); padding-top: 10px; margin-top: 4px; }
  details.tenants summary {
    cursor: pointer;
    font-size: 11px;
    font-weight: 700;
    color: var(--ai);
    list-style: none;
    padding: 4px 0;
    user-select: none;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  details.tenants summary::-webkit-details-marker { display: none; }
  details.tenants summary::before { content: "▸  "; display: inline-block; width: 16px; }
  details.tenants[open] summary::before { content: "▾  "; }
  details.tenants ul { list-style: none; padding: 6px 0 0; margin: 0; }
  details.tenants li { padding: 12px 0; border-top: 1px dashed var(--line); }
  details.tenants li:first-child { border-top: none; }
  .tenant-cat { font-size: 13px; font-weight: 700; color: var(--ink); }
  .tenant-brands { font-size: 11px; color: var(--ai); margin: 4px 0 6px; letter-spacing: 0.02em; font-weight: 500; }
  .tenant-why { font-size: 12px; color: var(--muted); line-height: 1.5; }

  /* Marketing content */
  details.marketing { border-top: 1px solid var(--line); padding-top: 10px; margin-top: 2px; }
  details.marketing > summary {
    cursor: pointer;
    font-size: 11px;
    font-weight: 700;
    color: var(--ai);
    list-style: none;
    padding: 4px 0;
    user-select: none;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  details.marketing > summary::-webkit-details-marker { display: none; }
  details.marketing > summary::before { content: "▸  "; display: inline-block; width: 16px; }
  details.marketing[open] > summary::before { content: "▾  "; }
  .channel-tabs { display: flex; flex-wrap: wrap; gap: 4px; margin: 10px 0 8px; }
  .channel-tab {
    font-size: 10px;
    font-weight: 700;
    padding: 5px 9px;
    border-radius: 999px;
    border: 1px solid var(--line);
    background: #fff;
    color: var(--muted);
    cursor: pointer;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    font-family: inherit;
  }
  .channel-tab:hover { border-color: var(--ai); color: var(--ai); }
  .channel-tab.active { background: var(--ai); color: #fff; border-color: var(--ai); }
  .channel-panel { display: none; }
  .channel-panel.active { display: block; }
  .local-context {
    font-size: 11px;
    color: var(--muted);
    font-style: italic;
    background: #faf9f5;
    padding: 8px 10px;
    border-radius: 4px;
    margin-bottom: 10px;
    line-height: 1.5;
  }
  .post-body {
    font-size: 12px;
    line-height: 1.55;
    color: var(--ink);
    background: #fafafa;
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 10px 12px;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: 260px;
    overflow-y: auto;
  }
  .ad-field { font-size: 12px; line-height: 1.5; padding: 6px 10px; border-left: 2px solid var(--line); margin: 6px 0; }
  .ad-field .label { font-size: 9px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-bottom: 2px; }
  .ad-field .value { color: var(--ink); }
  .ad-field .len { color: var(--muted); font-size: 10px; margin-left: 6px; }
  .hooks { margin: 0; padding: 0; list-style: none; }
  .hooks li { font-size: 12px; line-height: 1.5; padding: 6px 0 6px 10px; border-left: 2px solid var(--ai); margin-bottom: 6px; color: var(--ink); }

  /* Post action buttons */
  .post-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
  .copy-btn {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 5px 10px;
    border: 1px solid var(--ai);
    color: var(--ai);
    background: #fff;
    border-radius: 999px;
    cursor: pointer;
    font-family: inherit;
  }
  .copy-btn:hover { background: var(--ai); color: #fff; }
  .copy-btn.copied { background: var(--avail); color: #fff; border-color: var(--avail); }
  .card a.more {
    margin-top: auto;
    display: inline-block;
    color: var(--accent);
    font-size: 13px;
    font-weight: 600;
    text-decoration: none;
    padding-top: 6px;
  }
  .card a.more:hover { text-decoration: underline; }
  .empty { grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--muted); }

  /* Toast */
  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: var(--ink);
    color: #fff;
    font-size: 13px;
    font-weight: 500;
    padding: 12px 18px;
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    opacity: 0;
    transform: translateY(8px);
    transition: opacity 0.2s, transform 0.2s;
    pointer-events: none;
    z-index: 100;
    max-width: 320px;
  }
  .toast.show { opacity: 1; transform: translateY(0); }
  .toast.error { background: #8a1f1f; }

  footer {
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    padding: 24px 16px 48px;
    max-width: 720px;
    margin: 0 auto;
  }
  footer a { color: var(--muted); }
</style>
</head>
<body>

<header class="hero">
  <div class="wrap">
    <h1>Goodman Properties</h1>
    <p>__SUBTITLE_PLACEHOLDER__</p>
    <div class="ai-badge">AI enrichment + local marketing content · Claude Sonnet 4.6</div>
  </div>
</header>

<div class="controls">
  <div class="wrap row">
    <input id="q" type="search" placeholder="Search address, city, zip, or tenant category (e.g. &quot;fitness&quot;, &quot;urgent care&quot;)…" autocomplete="off">
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
  <div class="grid" id="grid"></div>
</main>

<footer>
  Listings sourced from <a href="https://goodmanproperties.org/our-properties/" target="_blank" rel="noopener">goodmanproperties.org</a>.
  AI enrichment (headlines, descriptions, tenant recommendations, marketing copy) generated by Claude Sonnet 4.6 — verify before use.
</footer>

<script>
const BASE = "https://goodmanproperties.org";
const LISTINGS = __DATA_PLACEHOLDER__;

const STATE_NAMES = {
  PA: "Pennsylvania", NJ: "New Jersey", IN: "Indiana", MD: "Maryland",
  VA: "Virginia", WV: "West Virginia", FL: "Florida", DE: "Delaware"
};

const grid = document.getElementById("grid");
const q = document.getElementById("q");
const stateSel = document.getElementById("state");
const typeSel = document.getElementById("type");
const availSel = document.getElementById("avail");
const countEl = document.getElementById("count");

function populate(sel, values, labelFn) {
  const sorted = [...values].sort();
  for (const v of sorted) {
    const o = document.createElement("option");
    o.value = v;
    o.textContent = labelFn ? labelFn(v) : v;
    sel.appendChild(o);
  }
}

populate(stateSel, new Set(LISTINGS.map(l => l.s)), s => STATE_NAMES[s] || s);
populate(typeSel, new Set(LISTINGS.map(l => l.t)));

function esc(str) {
  return String(str == null ? "" : str).replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"
  }[c]));
}

function searchBlob(l) {
  const parts = [l.a, l.c, l.s, l.z, l.t];
  const e = l.e;
  if (e) {
    parts.push(e.headline || "", e.description || "", e.leasing_angle || "");
    if (Array.isArray(e.ideal_tenants)) {
      for (const t of e.ideal_tenants) {
        parts.push(t.category || "");
        if (Array.isArray(t.example_brands)) parts.push(...t.example_brands);
        parts.push(t.why || "");
      }
    }
  }
  const m = l.m;
  if (m) {
    parts.push(m.local_context || "", m.facebook_local_post || "", m.nextdoor_post || "");
    parts.push(m.instagram_caption || "", m.linkedin_post || "");
    if (Array.isArray(m.community_hooks)) parts.push(...m.community_hooks);
  }
  return parts.join(" ").toLowerCase();
}

// ─── Copy to clipboard ────────────────────────────────────────────────────────

window.copyText = function(btn) {
  const text = btn.closest(".channel-panel").querySelector(".post-body").textContent;
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = "Copied";
    btn.classList.add("copied");
    setTimeout(() => { btn.textContent = orig; btn.classList.remove("copied"); }, 1500);
  });
};

// ─── Channel tab switching ────────────────────────────────────────────────────

window.showChannel = function(btn, panelId) {
  const container = btn.closest("details.marketing");
  container.querySelectorAll(".channel-tab").forEach(t => t.classList.remove("active"));
  container.querySelectorAll(".channel-panel").forEach(p => p.classList.remove("active"));
  btn.classList.add("active");
  container.querySelector("#" + panelId).classList.add("active");
};

let cardCounter = 0;
function cardId() { return "card-" + (cardCounter++); }

// ─── Marketing content rendering ──────────────────────────────────────────────

function renderMarketing(m, uid) {
  if (!m) return "";
  const safe = s => esc(s || "");

  const tabs = [], panels = [];

  function addTab(key, label, bodyHtml) {
    const pid = uid + "-" + key;
    const isFirst = tabs.length === 0;
    tabs.push(`<button class="channel-tab${isFirst ? " active" : ""}" onclick="showChannel(this, '${pid}')">${label}</button>`);
    panels.push(`
      <div class="channel-panel${isFirst ? " active" : ""}" id="${pid}">
        ${bodyHtml}
        <div class="post-actions">
          <button class="copy-btn" onclick="copyText(this)">Copy</button>
        </div>
      </div>`);
  }

  function postPanel(text) {
    return `<div class="post-body">${safe(text)}</div>`;
  }

  if (m.facebook_local_post) addTab("fb",  "Facebook",  postPanel(m.facebook_local_post));
  if (m.nextdoor_post)       addTab("nd",  "Nextdoor",  postPanel(m.nextdoor_post));
  if (m.instagram_caption)   addTab("ig",  "Instagram", postPanel(m.instagram_caption));
  if (m.linkedin_post)       addTab("li",  "LinkedIn",  postPanel(m.linkedin_post));

  if (m.google_search_ad && typeof m.google_search_ad === "object") {
    const a = m.google_search_ad;
    const field = (lbl, val, lim) => `
      <div class="ad-field">
        <span class="label">${lbl}<span class="len">${(val||"").length}/${lim}</span></span>
        <span class="value">${safe(val)}</span>
      </div>`;
    const body = field("Headline 1",    a.headline_1,    30)
               + field("Headline 2",    a.headline_2,    30)
               + field("Headline 3",    a.headline_3,    30)
               + field("Description 1", a.description_1, 90)
               + field("Description 2", a.description_2, 90);
    // wrap in a post-body-like div so copyText finds it
    addTab("gad", "Google Ad", `<div class="post-body">${body}</div>`);
  }

  if (m.facebook_ad && typeof m.facebook_ad === "object") {
    const a = m.facebook_ad;
    const field = (lbl, val, lim) => `
      <div class="ad-field">
        <span class="label">${lbl}<span class="len">${(val||"").length}/${lim}</span></span>
        <span class="value">${safe(val)}</span>
      </div>`;
    const body = field("Primary Text", a.primary_text, 125)
               + field("Headline",     a.headline,     27)
               + field("Description",  a.description,  27);
    addTab("fad", "FB Ad", `<div class="post-body">${body}</div>`);
  }

  if (Array.isArray(m.community_hooks) && m.community_hooks.length) {
    const body = `<ul class="hooks">${m.community_hooks.map(h => `<li>${safe(h)}</li>`).join("")}</ul>`;
    addTab("hk", "Hooks", `<div class="post-body">${body}</div>`);
  }

  if (!tabs.length) return "";

  const context = m.local_context
    ? `<div class="local-context">${safe(m.local_context)}</div>`
    : "";

  return `
    <details class="marketing">
      <summary>Local Marketing Content (${tabs.length})</summary>
      ${context}
      <div class="channel-tabs">${tabs.join("")}</div>
      ${panels.join("")}
    </details>`;
}

// ─── Listing card rendering ───────────────────────────────────────────────────

function render() {
  const query = q.value.trim().toLowerCase();
  const st = stateSel.value;
  const tp = typeSel.value;
  const av = availSel.value;

  const filtered = LISTINGS.filter(l => {
    if (st && l.s !== st) return false;
    if (tp && l.t !== tp) return false;
    if (av === "yes" && !l.sf) return false;
    if (query && !searchBlob(l).includes(query)) return false;
    return true;
  });

  countEl.textContent = `${filtered.length} of ${LISTINGS.length} listings`;

  if (filtered.length === 0) {
    grid.innerHTML = '<div class="empty">No listings match your filters.</div>';
    return;
  }

  cardCounter = 0;
  grid.innerHTML = filtered.map(l => {
    const e = l.e;
    const uid = cardId();
    const headline = (e && e.headline) ? e.headline : l.a;
    const availChip = l.sf ? '<span class="chip avail">Available</span>' : '';
    const description = (e && e.description) ? `<div class="description">${esc(e.description)}</div>` : '';
    const angle = (e && e.leasing_angle) ? `<div class="angle">${esc(e.leasing_angle)}</div>` : '';
    const tenants = (e && Array.isArray(e.ideal_tenants) && e.ideal_tenants.length)
      ? `<details class="tenants">
          <summary>Ideal Tenants (${e.ideal_tenants.length})</summary>
          <ul>
            ${e.ideal_tenants.map(t => `
              <li>
                <div class="tenant-cat">${esc(t.category)}</div>
                <div class="tenant-brands">${esc((t.example_brands || []).join(" · "))}</div>
                <div class="tenant-why">${esc(t.why)}</div>
              </li>`).join("")}
          </ul>
        </details>`
      : '';
    const marketing = renderMarketing(l.m, uid);
    return `
      <article class="card">
        <div class="headline">${esc(headline)}</div>
        <div class="addr-row"><span class="addr">${esc(l.a)}</span> · ${esc(l.c)}, ${esc(l.s)} ${esc(l.z)}</div>
        <div class="chips">
          <span class="chip state">${esc(l.s)}</span>
          <span class="chip">${esc(l.t)}</span>
          ${availChip}
        </div>
        ${l.sf ? `<div class="sf">Available: <strong>${esc(l.sf)} SF</strong></div>` : ''}
        ${description}${angle}${tenants}${marketing}
        <a class="more" href="${BASE}${esc(l.u)}" target="_blank" rel="noopener">View source details →</a>
      </article>`;
  }).join("");
}

q.addEventListener("input", render);
stateSel.addEventListener("change", render);
typeSel.addEventListener("change", render);
availSel.addEventListener("change", render);

render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
