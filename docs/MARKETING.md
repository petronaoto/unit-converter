# Advertisement & Promotion Strategy — O&G Engineering Converter

**Document version:** 1.7 (accompanies app v3.8.3)
**Maintainer:** Naoto Yamabe (petro.naoto@gmail.com)
**Companion documents:** [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) · [SPECIFICATION.md](SPECIFICATION.md)

A pragmatic promotion plan for a solo-maintained, free, zero-tracking engineering tool. Budget assumption: **~2 hours/week**, no paid advertising.

---

## 1. Positioning

> **The free, standards-traceable engineering calculator for gas & LNG professionals — no signup, no tracking, JIS/ISO/API-referenced, control-room ready.**

| vs. | Our differentiation |
|---|---|
| Generic unit-converter websites | Real engineering depth: JIS K 2301 rounding cascade, API 520 PRV sizing, Colebrook-White ΔP, flow-regime maps — not just multiplication factors. Standards editions cited in-app. |
| Legacy Excel sheets | Always current, shareable by URL, works on any device, no macro-security warnings, embedded theory manual, digit-for-digit match to the reference worksheet (documented test vectors). |
| Commercial process simulators | Zero cost, zero install, instant answers for the 90 % of daily questions that don't need a full simulation. Positioned as a *companion*, not a competitor. |
| Ad-funded calculator portals | No ads, no cookies, no data collection — usable inside corporate networks with strict policies. |

**Trust signals to emphasize everywhere:** standards citations with edition years, the published reference test vectors, the embedded Theory tab, the open GitHub repository, and the explicit "reference only" disclaimer (which reads as professional honesty, not weakness).

## 2. Target Segments

1. **Japanese LNG terminal / city-gas utility engineers** — the JIS K 2301:2011 compositional chain with exact Excel-matching rounding is a unique hook; almost no free web tool offers it. **Update (v2.7):** the entire app — working calculators AND the How To Use / Theory manuals — is now fully available in Japanese (and 8 further languages: 中文, 한국어, ไทย, Bahasa Indonesia, Русский, Español, Français, Deutsch). The content-marketing angle in §3 below (turning Theory-tab sections into Qiita/Zenn articles) can now source fully Japanese-language theory text directly from the app, and the multilingual coverage opens the same play for Chinese-, Korean-, and Southeast-Asian-market engineering communities.
2. **Global O&G / LNG process & facilities engineers** — daily ΔP screening, PSV sanity checks, erosional-velocity checks (RP 14E), flow-regime orientation.
3. **EPC junior engineers & graduates** — the How To Use + Theory tabs make the tool a learning aid; juniors who adopt a tool keep it for a career.
4. **Chemical/petroleum engineering students & instructors** — free, browser-based, theory-documented; instructors can link it in coursework.

## 3. SEO & Content

### On-site (small code changes, roadmap items — respect the preservation rules)

- Descriptive `<title>` and meta description mentioning the highest-value keywords.
- Open Graph / Twitter card tags so shared links preview properly (title, description, a screenshot image).
- One `<h1>` naming the tool and its purpose; semantic headings already exist per tab.
- A `sitemap.txt`/`robots.txt` is unnecessary for a single-page app, but registering the URL in search consoles is (see §5).

### Keyword targets (long-tail, low competition, high intent)

- "JIS K 2301 calculator", "Wobbe index calculator", "gas heating value from composition"
- "API 520 PSV sizing online", "relief valve orifice calculator API 526"
- "pipe pressure drop calculator Colebrook", "two-phase pressure drop HEM calculator"
- "LNG density calculator Klosek McKinley", "ISO 6578 LNG density"
- "erosional velocity API RP 14E calculator", "two-phase flow regime map online"

### Content marketing (mirrors the Theory tab — near-zero extra research)

- Each Theory-tab section can become a standalone article: "How JIS K 2301 rounding actually works (and why your Excel differs by 0.01)", "PSV sizing in 5 modes — a worked API 520 tour", "Reading a Hewitt & Roberts flow-regime map". Publish on a blog/Qiita/Zenn/LinkedIn and link to the live tool with the matching card pre-filled via a Share link — **Share links are a built-in marketing feature**: every example in an article can be one click from a live, pre-populated calculation.

## 4. Channels (ranked by expected return on time)

| Channel | Action | Cadence |
|---|---|---|
| **Qiita / Zenn (Japanese)** | JIS K 2301 / LNG density articles — the most differentiated content; Japanese engineering community is underserved for this niche. Since v2.6 the linked calculator itself renders in Japanese, so articles can now show a genuinely native-language tool, not just a native-language write-up of an English UI. | 1 article / month |
| **LinkedIn** | Short worked-example posts (screenshot + Share link + one insight); tag oil & gas / LNG hashtags | 2 posts / month |
| **Reddit** (r/ChemicalEngineering, r/oilandgasworkers, r/engineering) | Share as a free tool in tool-recommendation threads; always follow each sub's self-promotion rules; answer questions using the tool | Opportunistic |
| **Hacker News (Show HN)** | One well-timed "Show HN: A standards-traceable O&G engineering calculator (no signup, no tracking)" — the single-file no-build architecture is itself HN-interesting | Once, when v2.5+ is polished |
| **SPE Connect / PetroWiki / eng-tips forums** | Signature-style mentions and helpful answers | Opportunistic |
| **University outreach** | Email process-engineering instructors offering the tool for coursework | 1–2 / quarter |
| **GitHub** | Good README (done), topics/tags on the repo, pin the repo on the profile | Once + maintenance |

## 5. Analytics — within the zero-data-harvesting policy

**Status: resolved in v3.2 — option 2 adopted.** The options as originally ranked:

1. **Search Console only (recommended start).** Google Search Console + Bing Webmaster Tools measure impressions, queries, and clicks with **zero on-site code** — fully compatible with the current Privacy Policy as written. Do this immediately.
2. **Vercel Web Analytics (optional, later).** ✅ **Adopted in v3.2.** Cookieless, aggregate-only. Still adds a measurement script, so the in-app Privacy tab **must be updated first** to disclose it; requires the maintainer's explicit decision.
3. **Self-hosted Plausible / GoatCounter (optional).** Cookieless, open-source, EU-hostable. Same disclosure requirement as #2, plus hosting effort.

**Rule: no on-site analytics of any kind ships before the Privacy Policy tab is updated in the same release.** Honoured — v3.2 rewrote Privacy §2, §5, §7 and §9 in English plus all nine translations in the same commit as the script.

### 5.1 What v3.2 measures

The app is a **single URL**, so raw page views say nothing about which of the ~20 calculators earn their keep. Custom events close that gap. Five event names, chosen to stay well inside the Pro plan's allowance:

| Event | Data | Fired |
|---|---|---|
| `Tool Used` | `tool` — fixed slug (`steam-if97`, `pipe-dp`, `gt-fuel`, `gas-composition`, …) | **Once per tool per visit.** The live converters run on every keystroke (31 inline `oninput="calcGHV()"` bindings alone), so this is de-duplicated — it measures reach, not typing. |
| `Calculation` | `tool` — `pipe-dp` \| `prv-sizing` \| `flow-regime` | **Every run.** These are click-driven and each costs a serverless invocation, so the count is directly comparable to the function invocation count in the Vercel dashboard. A gap between the two is the ad-blocker rate. |
| `Tab View` | `tab` | Per tab switch (user-initiated only). |
| `Language` | `lang` | Per language switch — the payoff metric for the v2.7 i18n work. |
| `Action` | `action` — `export-pdf` \| `share-link` \| `report-sent` | Per click. |

**The boundary, restated:** slugs only. No input value, no result, and the Report tab is excluded outright. Boot is silent — `applyState()` → `recomputeAll()` runs the live calculators on every page load and none of them count, or a `localStorage` restore would read as user activity.

**Questions this is meant to answer:** which calculators justify further work (GT Fuel, the newest and largest, is instrumented from day one); whether the ten-language investment is used; whether Share and Export are discovered at all; and what fraction of ΔP/PRV traffic the ad-blocker rate is hiding.

## 6. Success Metrics

| Metric | Source | 6-month target (suggestion) |
|---|---|---|
| Search impressions / clicks | Search Console | Establish baseline → +50 % |
| Referral visits per channel | Vercel Web Analytics — Referrers (live since v3.2) | Establish baseline; LinkedIn should be visible on posting days |
| Calculator reach (share of visits touching each tool) | Vercel Web Analytics — `Tool Used` event | Identify the bottom quartile; decide keep / improve / retire |
| Deliberate server-backed runs | Vercel Web Analytics — `Calculation` event | Compare against serverless invocation count |
| Non-English usage share | Vercel Web Analytics — `Language` event | Validate or retire the ten-language investment |
| GitHub stars / forks | GitHub | 50 stars |
| Report-tab feedback emails | Inbox | Quality signal, not volume |
| Article engagement (Qiita LGTM, LinkedIn reactions) | Per platform | Trend up |
| Anecdotal adoption ("our shift uses it") | Feedback | The real goal |

## 7. Cadence & Review

- **Weekly (~2 h):** one content or community action from §4; note what was done in a simple log.
- **Quarterly:** review Search Console trends, decide whether the analytics stance (§5) should change, refresh keyword targets, and update this document.
- **Per release:** announce on LinkedIn + relevant communities with a worked example that shows the new feature via a Share link.
