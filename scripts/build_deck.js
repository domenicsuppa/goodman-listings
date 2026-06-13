// Goodman Properties — AI Vacancy Management pitch deck
// Run: node scripts/build_deck.js

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" × 5.625"
pres.title = "AI-Powered Vacancy Management — Goodman Properties";

// ── Palette ──────────────────────────────────────────────────────────────────
const C = {
  navy:    "0F4C81",
  navyMid: "1B6AA8",
  navyLt:  "E8F0FA",
  white:   "FFFFFF",
  offWhite:"F6F5F1",
  ink:     "1B2330",
  muted:   "5B6677",
  line:    "E5E2D8",
  green:   "1F6F33",
  greenBg: "E8F5E9",
  amber:   "C45D00",
  amberBg: "FEF3E2",
  purple:  "5A3FD6",
  purpleBg:"F3F0FF",
  red:     "8A1F1F",
};

// ── Helpers ──────────────────────────────────────────────────────────────────
const makeShadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 2, angle: 135, opacity: 0.10 });

function darkSlide(slide) {
  slide.background = { color: C.navy };
}

function lightSlide(slide) {
  slide.background = { color: C.offWhite };
}

// Left accent bar on content cards
function accentBar(slide, x, y, h, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.06, h,
    fill: { color: color || C.navy },
    line: { color: color || C.navy },
  });
}

// Numbered circle
function numCircle(slide, num, x, y, color, textColor) {
  slide.addShape(pres.shapes.OVAL, {
    x, y, w: 0.42, h: 0.42,
    fill: { color: color || C.navy },
    line: { color: color || C.navy },
  });
  slide.addText(String(num), {
    x, y, w: 0.42, h: 0.42,
    fontSize: 14, bold: true, color: textColor || C.white,
    align: "center", valign: "middle", margin: 0,
  });
}

// White card box
function card(slide, x, y, w, h, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: color || C.white },
    line: { color: C.line, pt: 1 },
    shadow: makeShadow(),
  });
}

// Section label (small caps label above title)
function sectionLabel(slide, text, dark) {
  slide.addText(text, {
    x: 0.5, y: 0.22, w: 9, h: 0.3,
    fontSize: 9, bold: true, color: dark ? "FFFFFF" : C.muted,
    charSpacing: 4,
  });
}

// Slide title
function slideTitle(slide, text, dark) {
  slide.addText(text, {
    x: 0.5, y: 0.5, w: 9, h: 0.75,
    fontSize: 32, bold: true, fontFace: "Georgia",
    color: dark ? C.white : C.ink,
    margin: 0,
  });
}


// ════════════════════════════════════════════════════════════════════════════
// SLIDE 1 — TITLE
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  darkSlide(s);

  // Top accent stripe
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: "CADCFC" }, line: { color: "CADCFC" } });

  // Main title
  s.addText("AI-Powered Vacancy Management", {
    x: 0.8, y: 1.6, w: 8.4, h: 1.1,
    fontSize: 40, bold: true, fontFace: "Georgia",
    color: C.white, align: "left", margin: 0,
  });

  // Subtitle
  s.addText("From Reactive to Proactive", {
    x: 0.8, y: 2.75, w: 8, h: 0.5,
    fontSize: 20, bold: false, fontFace: "Calibri",
    color: "CADCFC", align: "left", margin: 0,
  });
  s.addText("A Roadmap for Goodman Properties", {
    x: 0.8, y: 3.2, w: 8, h: 0.45,
    fontSize: 16, color: "9AB8D8", align: "left", margin: 0,
  });

  // Bottom bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.2, w: 10, h: 0.425, fill: { color: "0A3560" }, line: { color: "0A3560" } });
  s.addText("CONFIDENTIAL  ·  PROOF OF CONCEPT  ·  2026", {
    x: 0.5, y: 5.2, w: 9, h: 0.425,
    fontSize: 9, color: "6A8FAF", charSpacing: 3, align: "center", valign: "middle", margin: 0,
  });
}


// ════════════════════════════════════════════════════════════════════════════
// SLIDE 2 — THE PROBLEM
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  lightSlide(s);
  sectionLabel(s, "THE CHALLENGE");

  s.addText("Vacancies Are a Race Against Time", {
    x: 0.5, y: 0.5, w: 8.5, h: 0.75,
    fontSize: 30, bold: true, fontFace: "Georgia", color: C.ink, margin: 0,
  });

  // Left column — problem bullets
  const bullets = [
    { icon: "⏱", text: "Every vacant day = direct revenue loss. Average commercial vacancy: 6–12 months." },
    { icon: "🔄", text: "Marketing is reactive — it starts after the tenant has already left." },
    { icon: "✍️", text: "Content creation is manual, inconsistent, and slow across properties." },
    { icon: "🔔", text: "No early-warning system for upcoming lease expirations." },
    { icon: "📡", text: "Today's marketing reaches 1–2 channels. Tenants search across 6+." },
  ];

  card(s, 0.4, 1.45, 5.7, 3.7);
  accentBar(s, 0.4, 1.45, 3.7, C.red);

  bullets.forEach((b, i) => {
    s.addText(b.icon + "  " + b.text, {
      x: 0.65, y: 1.6 + i * 0.68, w: 5.2, h: 0.58,
      fontSize: 12, color: C.ink, valign: "middle", margin: 0,
    });
  });

  // Right column — stat callouts
  const stats = [
    { num: "6–12", label: "months", sub: "avg. vacancy duration" },
    { num: "0", label: "days notice", sub: "in today's reactive model" },
    { num: "1–2", label: "channels", sub: "typical marketing reach" },
  ];

  stats.forEach((st, i) => {
    const cy = 1.45 + i * 1.22;
    card(s, 6.4, cy, 3.2, 1.05);
    s.addText(st.num, {
      x: 6.6, y: cy + 0.05, w: 2.8, h: 0.55,
      fontSize: 36, bold: true, fontFace: "Georgia", color: C.red, margin: 0,
    });
    s.addText(st.label, {
      x: 6.6, y: cy + 0.55, w: 2.8, h: 0.25,
      fontSize: 13, bold: true, color: C.ink, margin: 0,
    });
    s.addText(st.sub, {
      x: 6.6, y: cy + 0.77, w: 2.8, h: 0.22,
      fontSize: 10, color: C.muted, margin: 0,
    });
  });
}


// ════════════════════════════════════════════════════════════════════════════
// SLIDE 3 — THE VISION
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  darkSlide(s);
  sectionLabel(s, "THE VISION", true);

  s.addText("What If Vacancies Marketed Themselves?", {
    x: 0.5, y: 0.5, w: 9, h: 0.75,
    fontSize: 30, bold: true, fontFace: "Georgia", color: C.white, margin: 0,
  });
  s.addText("90 days before a lease ends, the system takes over — automatically.", {
    x: 0.5, y: 1.22, w: 9, h: 0.35,
    fontSize: 14, color: "9AB8D8", margin: 0,
  });

  const steps = [
    { num: "①", title: "Lease Alert", body: "System detects lease nearing expiry. Workflow triggered automatically. Zero manual effort.", color: "CADCFC" },
    { num: "②", title: "AI Content Ready", body: "Listing copy, social posts, ad creative — generated instantly. Replacement tenant outreach begins immediately, building a candidate pipeline before the existing tenant even knows you're looking.", color: "C3B5F5" },
    { num: "③", title: "Approve & Go Live", body: "Owner reviews everything in one screen. One click publishes simultaneously across all platforms.", color: "A7D9B5" },
  ];

  steps.forEach((st, i) => {
    const cx = 0.4 + i * 3.2;
    s.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: 1.75, w: 2.95, h: 3.4,
      fill: { color: "112D4E" },
      line: { color: "1E4D7A", pt: 1 },
    });
    // Top color bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: 1.75, w: 2.95, h: 0.06,
      fill: { color: st.color }, line: { color: st.color },
    });
    s.addText(st.num, {
      x: cx + 0.15, y: 1.9, w: 2.6, h: 0.5,
      fontSize: 28, bold: true, color: st.color, margin: 0,
    });
    s.addText(st.title, {
      x: cx + 0.15, y: 2.4, w: 2.6, h: 0.45,
      fontSize: 16, bold: true, fontFace: "Georgia", color: C.white, margin: 0,
    });
    s.addText(st.body, {
      x: cx + 0.15, y: 2.9, w: 2.65, h: 1.8,
      fontSize: 12, color: "9AB8D8", lineSpacingMultiple: 1.3, margin: 0,
    });
    // Arrow between steps
    if (i < 2) {
      s.addText("→", {
        x: cx + 2.95, y: 2.9, w: 0.25, h: 0.4,
        fontSize: 18, color: "4A6F8A", align: "center", margin: 0,
      });
    }
  });
}


// ════════════════════════════════════════════════════════════════════════════
// SLIDE 4 — WHAT WE BUILT
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  lightSlide(s);
  sectionLabel(s, "PROOF OF CONCEPT — ALREADY BUILT");

  s.addText("The Foundation Is Already Complete", {
    x: 0.5, y: 0.5, w: 8.5, h: 0.75,
    fontSize: 30, bold: true, fontFace: "Georgia", color: C.ink, margin: 0,
  });

  // Main card
  card(s, 0.4, 1.4, 5.8, 3.8);
  accentBar(s, 0.4, 1.4, 3.8, C.green);

  const items = [
    "All 129 Goodman properties enriched with AI headlines, descriptions & leasing angles",
    "Ready-to-post content for Facebook, Instagram, LinkedIn, Nextdoor & Google Ads",
    "AI-generated ideal tenant recommendations for every property",
    "Live vacancy pipeline dashboard with real-time countdown timers",
    "One-click approval workflow — review content, approve, done",
  ];

  items.forEach((item, i) => {
    // Green check circle
    s.addShape(pres.shapes.OVAL, {
      x: 0.6, y: 1.57 + i * 0.7, w: 0.28, h: 0.28,
      fill: { color: C.green }, line: { color: C.green },
    });
    s.addText("✓", {
      x: 0.6, y: 1.57 + i * 0.7, w: 0.28, h: 0.28,
      fontSize: 11, bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(item, {
      x: 1.05, y: 1.55 + i * 0.7, w: 4.95, h: 0.5,
      fontSize: 12, color: C.ink, valign: "middle", margin: 0,
    });
  });

  // Right — demo callout
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.4, y: 1.4, w: 3.2, h: 3.8,
    fill: { color: C.navy },
    line: { color: C.navy },
    shadow: makeShadow(),
  });
  s.addText("LIVE DEMO", {
    x: 6.55, y: 1.65, w: 2.9, h: 0.4,
    fontSize: 10, bold: true, color: "9AB8D8", charSpacing: 3, align: "center", margin: 0,
  });
  s.addText("129", {
    x: 6.55, y: 2.1, w: 2.9, h: 0.85,
    fontSize: 60, bold: true, fontFace: "Georgia", color: C.white, align: "center", margin: 0,
  });
  s.addText("properties\nenriched", {
    x: 6.55, y: 2.9, w: 2.9, h: 0.55,
    fontSize: 13, color: "CADCFC", align: "center", margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.55, y: 3.6, w: 2.9, h: 0.02, fill: { color: "2A5F90" }, line: { color: "2A5F90" },
  });
  s.addText("domenicsuppa.github.io\n/goodman-listings", {
    x: 6.55, y: 3.75, w: 2.9, h: 0.9,
    fontSize: 11, color: "9AB8D8", align: "center", margin: 0,
  });
}


// ════════════════════════════════════════════════════════════════════════════
// SLIDE 5 — INTEGRATIONS
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  lightSlide(s);
  sectionLabel(s, "PHASE 2 — INTEGRATIONS");

  s.addText("Connect Once. Publish Everywhere.", {
    x: 0.5, y: 0.5, w: 9, h: 0.75,
    fontSize: 30, bold: true, fontFace: "Georgia", color: C.ink, margin: 0,
  });

  // Social column
  const cols5 = [
    {
      title: "Social Platforms",
      color: C.purple,
      items: [
        { name: "Facebook & Instagram", sub: "Meta Graph API — posts, stories & ads" },
        { name: "LinkedIn", sub: "Company Page — professional reach" },
        { name: "Nextdoor Business", sub: "Hyper-local neighborhood targeting" },
        { name: "Google Business Profile", sub: "Local search visibility" },
      ],
    },
    {
      title: "Commercial CRE Platforms",
      color: C.navyMid,
      items: [
        { name: "CoStar & LoopNet", sub: "Largest CRE audience — brokers & tenants" },
        { name: "Crexi", sub: "Fastest-growing CRE marketplace" },
        { name: "CommercialCafe / Yardi Matrix", sub: "National tenant & investor reach" },
        { name: "Buildout & 42Floors", sub: "Broker MLS + direct tenant search" },
      ],
    },
    {
      title: "Real Estate Marketplaces",
      color: C.green,
      items: [
        { name: "Zillow", sub: "Largest U.S. real estate audience" },
        { name: "Redfin", sub: "High-intent buyers & tenants" },
        { name: "Realtor.com", sub: "NAR-affiliated national reach" },
        { name: "Trulia", sub: "Zillow Group — neighborhood focus" },
      ],
    },
  ];

  cols5.forEach((col, i) => {
    const cx = 0.35 + i * 3.12;
    card(s, cx, 1.4, 2.98, 3.8);
    accentBar(s, cx, 1.4, 3.8, col.color);
    s.addText(col.title, {
      x: cx + 0.2, y: 1.5, w: 2.65, h: 0.38,
      fontSize: 11, bold: true, color: col.color, margin: 0,
    });
    col.items.forEach((item, j) => {
      s.addShape(pres.shapes.OVAL, {
        x: cx + 0.2, y: 2.02 + j * 0.78, w: 0.2, h: 0.2,
        fill: { color: col.color }, line: { color: col.color },
      });
      s.addText(item.name, {
        x: cx + 0.55, y: 1.98 + j * 0.78, w: 2.35, h: 0.28,
        fontSize: 11, bold: true, color: C.ink, margin: 0,
      });
      s.addText(item.sub, {
        x: cx + 0.55, y: 2.24 + j * 0.78, w: 2.35, h: 0.24,
        fontSize: 9, color: C.muted, margin: 0,
      });
    });
  });

  // Bottom callout
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 5.1, w: 9.3, h: 0.38,
    fill: { color: C.navyLt }, line: { color: "C5D8F0", pt: 1 },
  });
  s.addText("One approval publishes to all channels simultaneously — estimated reach: 15× current", {
    x: 0.5, y: 5.1, w: 9.1, h: 0.38,
    fontSize: 11, bold: true, color: C.navy, align: "center", valign: "middle", margin: 0,
  });
}


// ════════════════════════════════════════════════════════════════════════════
// SLIDE 6 — SERVICE PROVIDERS
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  lightSlide(s);
  sectionLabel(s, "PHASE 3 — OPERATIONS");

  s.addText("Automate the Full Workflow, Not Just the Marketing", {
    x: 0.5, y: 0.5, w: 9, h: 0.75,
    fontSize: 28, bold: true, fontFace: "Georgia", color: C.ink, margin: 0,
  });

  const quadrants = [
    {
      title: "Lease Management",
      color: C.navy,
      items: [
        "Integrate Yardi / MRI / AppFolio",
        "Auto-trigger at 90 / 60 / 30 days",
        "Pull tenant, SF & lease terms automatically",
      ],
    },
    {
      title: "Photography & Signage",
      color: C.purple,
      items: [
        "Auto-dispatch photographers on trigger",
        "Auto-order 'For Lease' signage",
        "Drone photography for anchor properties",
      ],
    },
    {
      title: "Legal & Leasing",
      color: C.amber,
      items: [
        "Auto-populate listing agreements & LOIs",
        "NDA generation for qualified prospects",
        "Digital signature via DocuSign",
      ],
    },
    {
      title: "Tenant Qualification",
      color: C.green,
      items: [
        "AI scores inbound inquiries vs. ideal profile",
        "Integrated screening workflow",
        "Brokers notified automatically",
      ],
    },
  ];

  const positions = [
    { x: 0.4,  y: 1.45 },
    { x: 5.15, y: 1.45 },
    { x: 0.4,  y: 3.45 },
    { x: 5.15, y: 3.45 },
  ];

  quadrants.forEach((q, i) => {
    const { x, y } = positions[i];
    card(s, x, y, 4.55, 1.85);
    accentBar(s, x, y, 1.85, q.color);
    s.addText(q.title, {
      x: x + 0.22, y: y + 0.1, w: 4.1, h: 0.32,
      fontSize: 13, bold: true, color: q.color, margin: 0,
    });
    q.items.forEach((item, j) => {
      s.addText("– " + item, {
        x: x + 0.22, y: y + 0.48 + j * 0.38, w: 4.1, h: 0.34,
        fontSize: 11, color: C.ink, margin: 0,
      });
    });
  });
}


// ════════════════════════════════════════════════════════════════════════════
// SLIDE 7 — CREATIVE VACANCY REDUCTION
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  lightSlide(s);
  sectionLabel(s, "CREATIVE STRATEGY");

  s.addText("Don't Wait for Vacancies — Prevent Them", {
    x: 0.5, y: 0.5, w: 9, h: 0.75,
    fontSize: 30, bold: true, fontFace: "Georgia", color: C.ink, margin: 0,
  });

  const strategies = [
    { num: "01", title: "Pipeline as Negotiating Leverage", body: "Start building replacement candidate pipeline at 90 days. When the existing tenant knows qualified replacements are already lined up, ownership enters renewal talks from a position of strength.", color: C.navy },
    { num: "02", title: "Pop-Up & Short-Term Leases", body: "Fill transition gaps with 30–90 day pop-up retailers. Generate revenue and foot traffic during search.", color: C.purple },
    { num: "03", title: "Tenant Mix Optimization", body: "AI identifies highest-value tenant categories per property using co-tenancy, demographics & trade area data.", color: C.navyMid },
    { num: "04", title: "Referral Incentive Program", body: "Offer existing tenants rent credits for referring new tenants. Leverages the relationships you already have.", color: C.amber },
    { num: "05", title: "Shadow Anchor Strategy", body: "Target national credit tenants that drive traffic to smaller inline spaces — reduces vacancy risk across the center.", color: C.green },
    { num: "06", title: "Community Activation Events", body: "Partner with local events and food trucks during vacancies. Keeps properties visible, active & attractive.", color: "#6A3D9A" },
  ];

  const cols = [
    { x: 0.4,  y: 1.45 },
    { x: 3.55, y: 1.45 },
    { x: 6.7,  y: 1.45 },
    { x: 0.4,  y: 3.45 },
    { x: 3.55, y: 3.45 },
    { x: 6.7,  y: 3.45 },
  ];

  strategies.forEach((st, i) => {
    const { x, y } = cols[i];
    card(s, x, y, 2.95, 1.9);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.95, h: 0.06,
      fill: { color: st.color.replace("#","") }, line: { color: st.color.replace("#","") },
    });
    s.addText(st.num, {
      x: x + 0.15, y: y + 0.12, w: 0.5, h: 0.35,
      fontSize: 14, bold: true, color: st.color.replace("#",""), margin: 0,
    });
    s.addText(st.title, {
      x: x + 0.15, y: y + 0.48, w: 2.65, h: 0.45,
      fontSize: 11, bold: true, color: C.ink, margin: 0,
    });
    s.addText(st.body, {
      x: x + 0.15, y: y + 0.93, w: 2.65, h: 0.88,
      fontSize: 10, color: C.muted, lineSpacingMultiple: 1.25, margin: 0,
    });
  });
}


// ════════════════════════════════════════════════════════════════════════════
// SLIDE 8 — TIMELINE
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  lightSlide(s);
  sectionLabel(s, "IMPLEMENTATION ROADMAP");

  s.addText("Phased Rollout — Value at Every Step", {
    x: 0.5, y: 0.5, w: 9, h: 0.75,
    fontSize: 30, bold: true, fontFace: "Georgia", color: C.ink, margin: 0,
  });

  // Connector line
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.85, y: 2.48, w: 8.3, h: 0.04,
    fill: { color: C.line }, line: { color: C.line },
  });

  const phases = [
    {
      label: "Phase 1",
      time: "Complete",
      title: "Foundation",
      items: ["AI enrichment of full portfolio", "Pipeline dashboard", "Approval workflow"],
      color: C.green,
      done: true,
    },
    {
      label: "Phase 2",
      time: "Weeks 1–4",
      title: "Social & Listings",
      items: ["Social platform APIs", "CRE listing integrations", "Automated publishing"],
      color: C.navy,
      done: false,
    },
    {
      label: "Phase 3",
      time: "Weeks 4–8",
      title: "Full Operations",
      items: ["Lease system integration", "Photography & signage", "Legal workflow & DocuSign"],
      color: C.purple,
      done: false,
    },
    {
      label: "Phase 4",
      time: "Ongoing",
      title: "Optimize & Scale",
      items: ["Analytics dashboard", "A/B content testing", "Vacancy trend reporting"],
      color: C.amber,
      done: false,
    },
  ];

  phases.forEach((ph, i) => {
    const cx = 0.55 + i * 2.25;

    // Circle on timeline
    s.addShape(pres.shapes.OVAL, {
      x: cx + 0.65, y: 2.3, w: 0.4, h: 0.4,
      fill: { color: ph.color },
      line: { color: ph.color },
    });
    if (ph.done) {
      s.addText("✓", {
        x: cx + 0.65, y: 2.3, w: 0.4, h: 0.4,
        fontSize: 13, bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
      });
    }

    // Phase label + time above line
    s.addText(ph.label, {
      x: cx, y: 1.65, w: 1.7, h: 0.28,
      fontSize: 11, bold: true, color: ph.color, align: "center", margin: 0,
    });
    s.addText(ph.time, {
      x: cx, y: 1.9, w: 1.7, h: 0.28,
      fontSize: 10, color: C.muted, align: "center", margin: 0,
    });

    // Card below line
    s.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: 2.9, w: 2.0, h: 2.4,
      fill: { color: ph.done ? C.greenBg : C.white },
      line: { color: ph.done ? C.green : C.line, pt: 1 },
      shadow: makeShadow(),
    });
    accentBar(s, cx, 2.9, 2.4, ph.color);
    s.addText(ph.title, {
      x: cx + 0.2, y: 3.0, w: 1.7, h: 0.35,
      fontSize: 12, bold: true, color: ph.done ? C.green : C.ink, margin: 0,
    });
    ph.items.forEach((item, j) => {
      s.addText("· " + item, {
        x: cx + 0.2, y: 3.42 + j * 0.55, w: 1.72, h: 0.45,
        fontSize: 10, color: C.ink, margin: 0,
      });
    });
  });
}


// ════════════════════════════════════════════════════════════════════════════
// SLIDE 9 — BUSINESS CASE
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  darkSlide(s);
  sectionLabel(s, "THE BUSINESS CASE", true);

  s.addText("The Numbers Are Simple", {
    x: 0.5, y: 0.5, w: 9, h: 0.75,
    fontSize: 32, bold: true, fontFace: "Georgia", color: C.white, margin: 0,
  });

  const stats = [
    { num: "6–12", unit: "months", label: "Average commercial vacancy duration today", color: "CADCFC" },
    { num: "90", unit: "days earlier", label: "How much sooner marketing starts with this system", color: "C3B5F5" },
    { num: "$0", unit: "extra cost", label: "AI content creation cost per property vs. hours of manual work", color: "A7D9B5" },
  ];

  stats.forEach((st, i) => {
    const cx = 0.4 + i * 3.2;
    s.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: 1.5, w: 2.9, h: 2.8,
      fill: { color: "112D4E" },
      line: { color: "1E4D7A", pt: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: 1.5, w: 2.9, h: 0.06,
      fill: { color: st.color }, line: { color: st.color },
    });
    s.addText(st.num, {
      x: cx + 0.15, y: 1.65, w: 2.6, h: 0.95,
      fontSize: 52, bold: true, fontFace: "Georgia", color: st.color, align: "center", margin: 0,
    });
    s.addText(st.unit, {
      x: cx + 0.15, y: 2.6, w: 2.6, h: 0.3,
      fontSize: 13, bold: true, color: C.white, align: "center", margin: 0,
    });
    s.addText(st.label, {
      x: cx + 0.15, y: 3.0, w: 2.6, h: 0.85,
      fontSize: 10, color: "9AB8D8", align: "center", lineSpacingMultiple: 1.3, margin: 0,
    });
  });

  s.addText("Reducing vacancy duration by 30 days across 129 properties = hundreds of thousands recovered annually. And when qualified replacements are already in the pipeline at 90 days out, ownership enters every renewal negotiation from a position of strength — not desperation.", {
    x: 0.5, y: 4.5, w: 9, h: 0.85,
    fontSize: 12, color: "9AB8D8", align: "center", italic: true, lineSpacingMultiple: 1.4, margin: 0,
  });
}


// ════════════════════════════════════════════════════════════════════════════
// SLIDE 10 — NEXT STEPS
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  lightSlide(s);
  sectionLabel(s, "NEXT STEPS");

  s.addText("Where Do We Go From Here?", {
    x: 0.5, y: 0.5, w: 9, h: 0.75,
    fontSize: 30, bold: true, fontFace: "Georgia", color: C.ink, margin: 0,
  });

  const steps = [
    { num: 1, title: "Connect social accounts", body: "Facebook Page, Instagram Business, LinkedIn Company Page", time: "1–2 days" },
    { num: 2, title: "Identify pilot properties", body: "Select 5 upcoming vacancies for the first full automated run", time: "Week 1" },
    { num: 3, title: "Integrate lease management system", body: "Pull real expiry dates from Yardi / MRI to replace mock data", time: "Week 2" },
    { num: 4, title: "First automated publish", body: "Real content, real channels, real results — measure and learn", time: "Weeks 3–4" },
    { num: 5, title: "Review & scale", body: "Analyze performance, refine AI output, roll out to full 129-property portfolio", time: "Month 2–3" },
  ];

  steps.forEach((st, i) => {
    const cy = 1.45 + i * 0.78;
    numCircle(s, st.num, 0.4, cy + 0.08, C.navy);
    s.addText(st.title, {
      x: 1.0, y: cy + 0.04, w: 6.2, h: 0.3,
      fontSize: 13, bold: true, color: C.ink, margin: 0,
    });
    s.addText(st.body, {
      x: 1.0, y: cy + 0.34, w: 6.2, h: 0.28,
      fontSize: 11, color: C.muted, margin: 0,
    });
    // Time badge
    s.addShape(pres.shapes.RECTANGLE, {
      x: 7.4, y: cy + 0.1, w: 1.9, h: 0.35,
      fill: { color: C.navyLt }, line: { color: "C5D8F0", pt: 1 },
    });
    s.addText(st.time, {
      x: 7.4, y: cy + 0.1, w: 1.9, h: 0.35,
      fontSize: 10, bold: true, color: C.navy, align: "center", valign: "middle", margin: 0,
    });
    // Divider
    if (i < 4) {
      s.addShape(pres.shapes.LINE, {
        x: 0.4, y: cy + 0.72, w: 9.2, h: 0,
        line: { color: C.line, pt: 0.5 },
      });
    }
  });

  // Closing line
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.2, w: 10, h: 0.425,
    fill: { color: C.navy }, line: { color: C.navy },
  });
  s.addText("The system is built. The content is ready. The next step is yours.", {
    x: 0.5, y: 5.2, w: 9, h: 0.425,
    fontSize: 13, bold: true, color: C.white, align: "center", valign: "middle", italic: true, margin: 0,
  });
}


// ── Write file ────────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "Goodman-AI-Vacancy-Management.pptx" })
  .then(() => console.log("✓ Wrote Goodman-AI-Vacancy-Management.pptx"))
  .catch(err => { console.error(err); process.exit(1); });
