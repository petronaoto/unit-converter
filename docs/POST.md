# LinkedIn Campaign Log — O&G Engineering Converter

**Document version:** 1.1 (accompanies app v3.1)
**Maintainer:** Naoto Yamabe (petro.naoto@gmail.com)
**Companion documents:** [MARKETING.md](MARKETING.md) · [SPECIFICATION.md](SPECIFICATION.md) · [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)

A 20-post daily LinkedIn campaign, plus the running record of what was published, when, and
how it performed. **This file is the single source of truth for the campaign** — plan here,
post from here, record the URL here.

**Goal (stated):** acquire more visitors who will support the project. Not lead generation —
reach, credibility, and genuine affection for the work.

---

## 1. Campaign settings

| Setting | Decision |
|---|---|
| **Language** | **English and Japanese in the SAME post** (changed 2026-08-11 at Day 1 — combined length ~2,600 chars, inside LinkedIn's 3,000 limit). Japanese is a rewrite, not a translation. §6 retains the separate-post rationale in case the pattern is revisited. |
| **Visuals** | **Real annotated screenshots** of the live app. No invented UI, no fabricated numbers. |
| **Voice** | Engineer-to-engineer, tool-forward. Naoto is present as the author; the engineering leads. First person, no "excited to announce". |
| **Links** | Live app URL + public GitHub repo (`https://github.com/petronaoto/unit-converter`). |
| **Cadence** | Weekdays only, 5 posts/week, 4 weeks. Weekend posting on LinkedIn costs reach. |
| **Link placement** | **`https://engineering-converter.com` goes in the post BODY of every post** (maintainer instruction, 2026-08-11) — a reader who never opens the comments still needs to know where the tool lives. LinkedIn rewrites it to an `lnkd.in` short link automatically; it still resolves. The *pre-filled share link* goes in the first comment. |

### Live URLs

| | |
|---|---|
| **App** | <https://engineering-converter.com> |
| **Repo** | <https://github.com/petronaoto/unit-converter> |

### Pre-launch checklist

| # | Item | Status |
|---|---|---|
| B1 | **Production URL** — was recorded nowhere in the repo. | ✅ Supplied by Naoto 2026-08-11; now in `index.html` as `og:url` + `canonical`. |
| B2 | **Open Graph / Twitter card tags** — absent, so shared links previewed as naked text. | ✅ Added 2026-08-11 (`index.html` `<head>`). Static English by design: unfurlers never run the i18n pass. Verified the language switch does not overwrite them. 242 tests still pass. |
| B3 | **Producing the PNG.** | ✅ **Solved.** `PrintWindow` against an isolated `--app` Chrome window captures the graphic without needing focus or touching other windows. See §7 *Producing the image*. `docs/linkedin/day01.png` is a real 1200 × 675 capture. |
| B6 | **Attaching the image to a LinkedIn post.** | ✅ **Works — paste the image from the OS clipboard.** See §7 *Attaching the image*. |
| B4 | **Link preview on production.** | ✅ Verified after #25 deployed: `canonical` and `og:url` both read `https://engineering-converter.com/`. |
| B5 | **Force LinkedIn to re-scrape** via Post Inspector. | ✅ Re-run against the correct domain after #25: Fetched URL and Canonical URL both `https://engineering-converter.com/`, title and description correct, image re-ingested to LinkedIn's CDN. |

> **Vercel's CDN served a stale copy for ~1 minute after the merge** (`x-vercel-cache: HIT`
> with a pre-merge `last-modified`). It has since refreshed and now returns the tags on cache
> hits too. Worth knowing for future deploys: if a preview looks wrong immediately after a push,
> re-check with a cache-busting query string before assuming the change failed.

---

## 2. Master tracker

Status: ☐ planned · ✎ drafted · 📷 visual ready · 🕗 scheduled · ✅ posted

| Day | Date | Title | Lens | Status | Post URL | Reactions / Comments |
|---|---|---|---|---|---|---|
| 1 | Tue 11 Aug 2026 | The 1.013 bar error that never looks like an error | pain | ✅ **posted** | https://www.linkedin.com/feed/update/urn:li:share:7492837311416741888/ | |
| 2 | Wed 12 Aug 2026 | Why your HHV and the plant's HHV disagree in the second decimal | standards | ✅ **posted** | https://www.linkedin.com/feed/update/urn:li:share:7493067132373499904/ | |
| 3 | Thu 13 Aug 2026 | The steam spreadsheet nobody owns | story | ✅ **posted** | https://www.linkedin.com/feed/update/urn:li:share:7493228666642923520/ | |
| 4 | Fri 14 Aug 2026 | 176.9 kPa of ΔP, and 2.3 kPa of it is friction | teach | ✅ **posted** | https://www.linkedin.com/feed/update/urn:li:share:7493672957697806337/ | |
| 5 | Mon 17 Aug 2026 | There are three versions of these coefficients on the internet | standards | 🕗 **scheduled 08:00 JST** | *(URL exists only once it publishes)* | |
| 6 | Tue 18 Aug 2026 | You cannot rearrange Colebrook-White | teach | 🕗 **scheduled 08:00 JST** | *(URL exists only once it publishes)* | |
| 7 | Wed 19 Aug 2026 | The constant that looked precise and was wrong | story | ☐ | | |
| 8 | Thu 20 Aug 2026 | Your fittings are worth 30 m of pipe, not 23 m | teach | ☐ | | |
| 9 | Fri 21 Aug 2026 | The pressure drop was fine. The flow regime wasn't. | pain | ☐ | | |
| 10 | Mon 24 Aug 2026 | Which roughness did you use? *(engagement)* | story | ☐ | | |
| 11 | Tue 25 Aug 2026 | Required area 5.7047 in². The letter is the easy part. | standards | ☐ | | |
| 12 | Wed 26 Aug 2026 | The bug that was unreachable until I fixed a default | story | ☐ | | |
| 13 | Thu 27 Aug 2026 | Napier, and the viscosity correction you cannot do in one pass | standards | ☐ | | |
| 14 | Fri 28 Aug 2026 | Ideal gas costs you 7.5 % on the speed of sound | teach | ☐ | | |
| 15 | Mon 31 Aug 2026 | The calculator that refuses to tell you whether it passes | pain | ☐ | | |
| 16 | Tue 1 Sep 2026 | A green CI badge is not evidence | story | ☐ | | |
| 17 | Wed 2 Sep 2026 | There is no such thing as a tonnes-to-MMBtu factor *(engagement)* | pain | ☐ | | |
| 18 | Thu 3 Sep 2026 | The whole toolbox on one page, and ten published vectors | story | ☐ | | |
| 19 | Fri 4 Sep 2026 | No login, no cookies, and the share link never reaches my server | pain | ☐ | | |
| 20 | Mon 7 Sep 2026 | Five things this calculator refuses to do | standards | ☐ | | |

> ⚠️ **The `### Day N` sheets in §7 were never renumbered after the reflow (C12).** The table
> above is authoritative for *what runs when*; the sheets below are authoritative for *content*.
> Read the sheet by **title**, not by its number. Mapping:
>
> | Tracker day | Title | Lives in sheet |
> |---|---|---|
> | 1, 2, 4, 6–15, 19 | *(unchanged)* | same number ✓ |
> | **3** | The steam spreadsheet nobody owns | `### Day 5` |
> | **5** | There are three versions of these coefficients on the internet | `### Day 16` |
> | **16** | A green CI badge is not evidence | `### Day 17` |
> | **17** | There is no such thing as a tonnes-to-MMBtu factor *(engagement)* | `### Day 3` |
> | **18** | The whole toolbox on one page, and ten published vectors | `### Day 20` |
> | **20** | Five things this calculator refuses to do | `### Day 18` |
>
> **Next up (Day 7, Wed 19 Aug): "The constant that looked precise and was wrong" — draft is in `### Day 7`.**
>
> *Days 5 and 6 are both queued in LinkedIn (Mon 17 and Tue 18, 08:00 JST). Neither has a URL yet.*

**Weekly themes**

- **Week 1 (Days 1–5) — Everyday numbers, and where they come from.** Cold-readable; every post is useful without the tool. Now also carries the trust argument (Day 5), because a skeptic decides about a free solo-built sizing tool in the first week, not the fourth.
- **Week 2 (Days 6–10) — Hydraulics you can check.** The app's densest territory.
- **Week 3 (Days 11–15) — Safety-critical numbers: relief, flare, suction.** Specificity buys the most credibility here.
- **Week 4 (Days 16–20) — Scope, trust and the close.** Why you would trust a free tool built by one engineer — ending on the strongest evergreen post in the set.

**Variety rule enforced:** no two consecutive posts share a lens (verified programmatically
after the 2026-08-11 reflow — zero violations). Engagement posts sit on **Days 10 and 17**.

> **Reflowed 2026-08-11** to carry Naoto's two approved changes without side effects. Moving the
> coefficient-provenance post into week 1 put it directly after the JIS rounding post — two
> standards-credibility "where numbers come from" pieces back to back, which reads as repetitive.
> Closing on "Five things this calculator refuses to do" likewise put two story posts adjacent in
> week 4. The whole sequence was re-laid rather than patched: provenance now lands **Day 5** (still
> week 1, still cold-readable), the steam post moves up to Day 3, and week 4 alternates cleanly to
> the new close. The roadmap poll is cut from the ending entirely — hold it for a standalone post
> a fortnight after the campaign, when there is something concrete to decide.

---

## 3. The compact share-link recipe — *use this, never the Share button*

The app's own **Share** button encodes every field. A stock v3.0 link measures
**4,627 characters** (measured in-browser on 2026-08-11, empty state; the app itself warns
above `SHARE_URL_WARN_LEN = 2000`). That does not fit a LinkedIn comment (1,250 chars) or
post body (3,000 chars), and Teams/Outlook link rewriting truncates it into a link that looks
fine and silently restores nothing.

**But `applyState()` → `applyInputs()` tolerates a partial `inputs` object** — it iterates only
the keys present. So a hand-authored link carrying 10–15 keys lands at **~250–400 characters**
and restores perfectly, including the landing tab.

**Verified working example** (ΔP reference case, 343 chars, confirmed on a real page load —
inputs restored *and* the Advanced tab opened):

```javascript
// Run in the browser console on the live app, then paste the result into the post comment.
const state = {
  v: 2,
  tab: 'advanced',
  inputs: {
    'dp-id': '4', 'dp-id-unit': '0.0254', 'dp-len': '100', 'dp-elev': '70.711',
    'dp-v-flow': '150', 'dp-v-den': '10', 'dp-v-visc': '0.012',
    'dp-l-flow': '7300', 'dp-l-den': '500', 'dp-l-visc': '0.12', 'dp-cfactor': '100'
  }
};
console.log(location.origin + location.pathname + '#s=' + btoa(unescape(encodeURIComponent(JSON.stringify(state)))));
```

**Rules**

1. Include only the keys the post actually needs. Omitted keys keep their defaults.
2. `tab` accepts `general` / `basic` / `advanced` / `safety`. Omit it to land on General.
3. `lang` carries the UI language — **use `ja` only on the Japanese post**, never on the English one.
4. **Test every link on a real page load before publishing.** A fragment change alone does not
   re-run the restore; the page must actually load.
5. Server-backed cards (ΔP, Flow Regime, PRV) still need a **Calculate** click after opening.
   Client-side cards (composition, steam, NPSHa, compressor, gas properties, Z-factor, pipe
   volume) render on open with zero clicks.

---

## 4. Verified reference values

Every number below was reproduced **live on 2026-08-11** against v3.0 (commit `27084a5`) — via
the app's own UI and the three serverless endpoints running locally. `pytest`: **242 passed**.

> Anything not in this table must be verified before it appears in a post.

### JIS K 2301:2011 compositional chain — *app default composition*
CH₄ 89 / C₂H₆ 7 / C₃H₈ 2.5 / iC₄ 0.7 / nC₄ 0.5 / N₂ 0.3 vol%

| Quantity | Value |
|---|---|
| Mole fractions (4 d.p.) | 0.8887 / 0.0704 / 0.0254 / 0.0073 / 0.0052 / 0.0030 |
| Z_exact / Z_rounded | 0.996759 / 0.9968 |
| HHV | **44.59 MJ/Nm³** |
| LHV | 40.25 MJ/Nm³ |
| SG | 0.634 |
| Wobbe Index | **56.00** |
| MW | 18.305 g/mol |
| ρ_std | 0.81930 kg/Nm³ |
| MCP | 36.9 |
| LNG liquid density | 462.68 kg/m³ |
| 100 t/h → | 122.06 kNm³/h |
| 100 kNm³/h → | 81.930 t/h |

### Pipe ΔP (Darcy-Weisbach + Colebrook-White, HEM two-phase)
ID 4 in · L 100 m · Δz 70.711 m · ε 0.045 mm · vapour 150 kg/h @ 10 kg/m³ / 0.012 cP ·
liquid 7,300 kg/h @ 500 kg/m³ / 0.12 cP · C = 100

| Quantity | Value |
|---|---|
| ΔP_total | **176.929 kPa** |
| ΔP_friction / ΔP_static | 2.338 kPa (1.3 %) / 174.590 kPa (98.7 %) |
| Velocity | 1.0142 m/s |
| Reynolds | 2.201 × 10⁵ (Turbulent) |
| Darcy f | 0.01835 |
| ρ_mix (HEM, no-slip) | 251.69 kg/m³ |
| V_e (API RP 14E, C=100) | **7.689 m/s** — *not 7.72; the √1.5 constant was corrected in v2.8* |
| v / V_e | 0.1319 → WITHIN LIMIT |
| Phase badge | Two-Phase (HEM) |

### Flow regime — *same inputs*
**Churn / Slug Flow**, θ = **+45.0°**, vertical (Hewitt & Roberts type) map,
j_G = 0.514 m/s, j_L = 0.500 m/s, v_mix = 1.0142 m/s, λ_l = 0.4932.

### API 520 PRV sizing (USC)

| Mode | Inputs | Result |
|---|---|---|
| §5.6 gas | W 53,500 lb/h · M 51 · k 1.3 · T 627 °R · Z 1.0 · P₁ 97.2 psia · P₂ 0 · K_d 0.975 | **5.7047 in² → orifice P** (6.38 in²); C 346.9764; P_cf 53.045 psia; critical ratio 0.5457; Critical Flow |
| §5.7 steam | W 153,500 lb/h · P₁ 1,774.7 psia · K_d 0.975 | 1.7030 in² → orifice K; K_N 1.0115 |
| §5.8 liquid (certified) | Q 1,800 gal/min · G_l 0.9 · P₁ 275 psig · K_d 0.65 | 4.1690 in² → orifice N |
| §5.9 liquid (non-certified) | same | 4.1001 in² → orifice N |
| §5.10 two-phase | W 238,715 lb/h · v_o 0.3116 · v₉ 0.3629 ft³/lb · P_o 80.7 psia · K_d 0.85 | 19.0114 in² → orifice T; ω 1.4817; η_c 0.6564; P_c 52.971 psia; G 590.891 |

### Pressure conversion (Day 1)

| Quantity | Value |
|---|---|
| 1 atm | 101,325 Pa (exact) |
| 1 psi | 6,894.75729 Pa |
| 1 bar | 100,000 Pa |
| **10 barg → psia** | **159.73369 psia** (display) → quote as **159.73** |
| Same figure mis-declared as absolute | 145.03774 psia → quote as **145.04** |
| Gap | **14.696 psi** (= 101,325 Pa exactly) |

### Other verified figures

- Crane TP-410 fittings (Vector 7): ΣK 5.3760 · ΔP_fittings 695.853 Pa · L_eq 29.7586 m · ΔP_total 177.625 kPa
- Steam IF97 @ 4 MPa abs / 300 °C: Region 2, superheat 49.64248 K · h 2,961.65148 kJ/kg · s 6.36383 kJ/(kg·K) · ρ 16.98717 kg/m³ · T_sat 250.35752 °C
- Gas properties (SG 0.65, 2,000 psi, 150 °F, k 1.3): Z 0.8646 · μ 0.016663 cP · c 410.0269 m/s · μ_JT 0.3279 K/bar
- NPSHa (water 80 °C, open tank, z +3 m, h_f 1.2 m): **7.45697 m**; P_v 47.41472 kPa; ρ 971.77879 kg/m³; g = 9.80665 m/s²
- Test suite: **242 tests** (165 test functions, parametrised) across 13 modules; 434 assertions. *(README corrected 2026-08-11 — it had said "183 pytest assertions", wrong in both number and kind.)*

---

## 5. Corrections applied during planning

An adversarial fact-check of the draft plan against the codebase found ten defects (C1–C10).
Two more (C11–C12) were caught later, at publish time, by re-verifying against the running app.
All are corrected in the day sheets below; recorded here so they are not silently reintroduced.

| # | Day | Defect | Correction |
|---|---|---|---|
| C1 | 1 | Headline "10 barg = 159.74 psia" | **159.73** (159.73369 displayed). Verified live. |
| C2 | 2 | "the only card that renders finished numbers on share-link open" | False. `recomputeAll()` runs seven client-side calculators. Say "one of several". |
| C3 | 4 | 174.6 kPa static head presented as settled fact | It is **homogeneous no-slip** (ρ_mix from HEM, no holdup model) — and Day 9 proves the same line is Churn/Slug at +45°, where slip matters most. State the caveat in the post. |
| C4 | 8 | "the L/D shortcut runs low because f_T = 0.017 < flowing f" | Backwards — that effect makes the shortcut run **8 % high**. The whole shortfall is **entrance + exit** (K = 1.5, no L/D at all). |
| C5 | 10 | "the badge drops to awaiting-calculation, the old answer does not get to sit there" | `markResultStale()` **appends** "· inputs changed — recalculate" and recolours amber. Outputs stay on screen. |
| C6 | 12 | Hook states the broken branch became the default path | It never did — both fixes shipped together in v3.0 PR-1. Rewrite in the conditional. |
| C7 | 14 | "c = √(kZRT/M), the real-gas form API 520 uses" | Misattribution. API 520 sizes on C and the critical pressure ratio. Frame as a first-order real-gas correction. |
| C8 | 19 | Share-link length guessed at 4,600 | **Measured: 4,627** chars (stock, empty state). Use the compact recipe in §3. |
| C9 | 17 | "183 tests" | **242** today. |
| C10 | 2 | Intermediate Wobbe value "55.997" | Wrong: 44.59/√0.634 = **56.000621** → **56.00**. Do not publish an intermediate. |
| C11 | 2 | CH₄'s unrounded mole fraction given as "0.888712…" | Fabricated digits. The app computes **0.888658452** → 0.8887. Caught 2026-08-12 while grounding the post; the published copy and the graphic both carry the correct value. |
| C12 | — | **Day sheets were never renumbered after the 2026-08-11 reflow.** §2's tracker carries the reflowed schedule; the `### Day N` sheets below still carry the pre-reflow order. Days 1, 2, 4 and 6–15 happen to agree; **Days 3, 5, 16, 17, 18 and 20 do not.** Tracker Day 18 appeared to have no sheet at all. | ✅ **Resolved 2026-08-12** (Naoto). No topic was lost — tracker Day 18 is the material in `### Day 20`, which editorial decision 2 had already moved out of the closing slot. The mapping table under §2 is now complete, and the `### Day 20` sheet has been reframed as a Day 18 capability tour (the "twenty posts in" retrospective framing was cut, since the campaign is not over on Day 18). The sheets keep their pre-reflow numbers deliberately: renumbering twenty headings would break every cross-reference in this file for no gain. **Read sheets by title, via the §2 mapping.** |

### Editorial decisions — ✅ both approved by Naoto 2026-08-11

1. ~~The trust argument is entirely in week 4.~~ **Applied: Days 3 and 16 are swapped.**
   The LGE coefficient-provenance post ("three versions of these coefficients") now runs on
   **Day 3**, because a skeptic decides whether to trust a free, solo-built sizing tool in the
   first three days, not in week 4. It works cold and needs no setup. The tonnes-to-MMBtu
   engagement post moves to **Day 16**.
   *Knock-on:* the campaign's first engagement post is now Day 10, not Day 3 — so Days 1–5 read
   as five straight substance posts. That is the right trade for a cold audience, but do reply
   hard in the comments on Days 1–3 to compensate.
2. ~~Day 20 closes on a roadmap poll.~~ **Applied: Days 18 and 20 are swapped.**
   The campaign now closes on **"Five things this calculator refuses to do"** — the strongest
   evergreen post in the set, and the one most likely to be shared after the campaign ends.
   The toolbox sweep moves to **Day 18**. The roadmap question is cut from the closing slot
   entirely; hold it for a standalone post a fortnight later, when there is something concrete
   to decide.

> Week themes still hold: Day 3's post is standards-credibility (week 1 = "everyday numbers,
> quiet failures" now reads as "everyday numbers and where they come from"), and Day 16 is
> pain-workflow inside week 4's provenance-and-trust block. The no-two-consecutive-lenses rule
> is preserved in both new orderings — verify again if you reorder further.
3. ~~**Two documentation contradictions the campaign will expose.**~~ ✅ **Both fixed 2026-08-11**
   in the same PR as the OG tags: `SPECIFICATION.md` §4.1 said custom modules were "not included
   in Share links" (they have travelled since v2.8, state v:2, capped at 20 modules / 40-char
   labels), and `README.md` claimed "183 pytest assertions" (it is 242 tests across 13 modules).
4. **`exportReport()` coverage** (Day 10) omits Steam, NPSHa, Compressor **and** the Gas
   Property Estimator and the fittings/line-sizing row. Either state the full list in the post
   or add the five rows to the export first.

---

## 6. Japanese pairing

Each post ships as an **English post and a separate Japanese post**, not one bilingual post —
LinkedIn's feed truncates at ~2 lines and a bilingual body wastes the hook on the language
the reader does not use.

- **English post:** morning CET / evening JST — catches Europe and the Middle East.
- **Japanese post:** next morning JST, with `lang: 'ja'` in its share link so the tool opens in
  Japanese. The app has shipped full Japanese since v2.7 — working tool *and* both manuals.
- The Japanese version is a **rewrite, not a translation**. JIS K 2301 posts in particular
  should lead differently for a domestic audience: it is their standard, not an exotic one.
- Japanese hashtags: `#プロセスエンジニアリング #LNG #配管設計 #石油ガス`

---

## 7. Day sheets

Each sheet carries: hook (the literal first two lines), body, mockup spec, verified numbers,
share link, CTA and hashtags. Draft the Japanese version underneath when the English is final.

---

### Day 1 — Wed 12 Aug 2026

**Title:** The 1.013 bar error that never looks like an error
**Lens:** pain-workflow · **Format:** worked example · **Feature:** General → Pressure card

**Why this is Day 1:** it must work for someone who has never heard of the tool. No domain
setup, every engineer over five years has shipped or caught this error, and the feature is
almost incidental — which is exactly why it reads as a colleague rather than an ad.

#### English post

> A barg/bara mix-up is a 1.013 bar error that never looks like an error. It just looks like a
> slightly conservative number.
>
> Most free pressure converters never ask you which one you meant.
>
> The failure mode isn't arithmetic. It's an undeclared basis — and it survives review because
> nothing about the number looks wrong.
>
> Take 10 barg.
>
> • Declared correctly → 159.73 psia
> • Same figure assumed absolute → 145.04 psia
>
> A 14.696 psi gap. That's exactly one atmosphere, and it lands in the direction that makes an
> under-designed line look acceptable.
>
> Two constants worth keeping in your head:
> • 1 atm = 101,325 Pa, exactly
> • 1 psi = 6,894.75729 Pa
>
> The working rule I use: convert through absolute pascals, and tag the basis at every handoff —
> not just in the final report. "159.73 psia" travels. "159.73 psi" does not.
>
> On the converter I build, each side of the pressure card carries its own Abs/Gauge toggle, so
> barg → psia is one step instead of two and a subtraction. It won't stop you choosing the wrong
> basis — nothing can — but it makes the basis something you have to state rather than something
> you can leave implicit.
>
> It's free, there's no sign-up, and every reference calculation it ships with is published so
> you can check it against your own.
>
> What's the unit mix-up that has actually cost your project time — barg/bara, gauge/abs, or
> something worse?

**Length check:** ~1,450 characters — under LinkedIn's 3,000 limit, ~5 lines above the
"see more" fold. ✓

#### Mockup spec

Annotated screenshot, 1200 × 675 (LinkedIn's 16:9 sweet spot).

- **Main frame:** the real General-tab Pressure card, left side `10` / `bar` / **GAUGE**,
  right side `159.73369` / `psi` / **ABS**.
- **Annotation A** — amber arrow to each Abs/Gauge toggle: *"each side carries its own basis —
  that's the whole point"*.
- **Annotation B** — keep the card's own atmospheric-reference strip in frame, so 101,325 Pa is
  *shown*, not asserted.
- **Lower strip** (designed, below the screenshot): two rows —
  green `declared correctly → 159.73 psia` above red `both sides assumed absolute → 145.04 psia`,
  with `−14.696 psi — and it reads as conservative` between them.
- Do **not** crop out the app's version string; provenance is part of the pitch.

#### Verified numbers

10 barg = 1,000,000 + 101,325 = 1,101,325 Pa → ÷ 6,894.75729 = **159.73369 psia**.
Mis-declared: 1,000,000 ÷ 6,894.75729 = **145.03774 psia**. Gap **14.69595 psi**.
*(Confirmed against the live card, which displays 159.73369.)*

#### Share link — ✅ built and verified

State (note `p1`/`p2` carry the Abs/Gauge modes — they are **not** in `inputs`):

```json
{"v":2,"p1":"gau","p2":"abs","inputs":{"press-input1":"10","press-select1":"100000","press-select2":"6894.75729"}}
```

Append this **166-character** fragment to the production URL:

```
/index.html#s=eyJ2IjoyLCJwMSI6ImdhdSIsInAyIjoiYWJzIiwiaW5wdXRzIjp7InByZXNzLWlucHV0MSI6IjEwIiwicHJlc3Mtc2VsZWN0MSI6IjEwMDAwMCIsInByZXNzLXNlbGVjdDIiOiI2ODk0Ljc1NzI5In19
```

**Verified on a real page load (2026-08-11):** restores side A = 10 bar **Gauge**, side B =
**159.73369 psi Abs**, both toggles correctly highlighted. Total URL ≈ 192 characters with a
typical domain — comfortably inside LinkedIn's 1,250-character comment limit.

*(Japanese post: add `"lang":"ja"` to the state object and regenerate.)*

#### CTA & placement

Question in the body (above). **App link in the first comment**, phrased:
> Free, no sign-up, no tracking: https://engineering-converter.com
>
> This exact case, pre-filled — 10 barg on the left, psia on the right:
> https://engineering-converter.com/index.html#s=eyJ2IjoyLCJwMSI6ImdhdSIsInAyIjoiYWJzIiwiaW5wdXRzIjp7InByZXNzLWlucHV0MSI6IjEwIiwicHJlc3Mtc2VsZWN0MSI6IjEwMDAwMCIsInByZXNzLXNlbGVjdDIiOiI2ODk0Ljc1NzI5In19
>
> Source and the published reference values: https://github.com/petronaoto/unit-converter

*(Comment is 341 characters — well inside LinkedIn's 1,250 limit.)*

**Hashtags:** `#ProcessEngineering #OilAndGas #PipingDesign #EngineeringTools`

#### Mockup files — ✅ built and verified

| File | What it is |
|---|---|
| [`linkedin/day01-mockup.html`](linkedin/day01-mockup.html) | **The generator.** Loads `index.html` in an off-screen iframe, drives it with the app's own JS, and clones the resulting card. Must be served over HTTP. |
| [`linkedin/day01-standalone.html`](linkedin/day01-standalone.html) | **The deliverable.** A frozen 1200 × 675 snapshot with every style inlined — zero scripts, zero external references. Open it anywhere and screenshot the frame. |

Nothing is re-implemented: **159.73369 is computed by `index.html`**, not typed by hand.
Callout arrows self-align by measuring the real toggle positions.

```bash
python devserver.py .   # then open:
# http://127.0.0.1:8000/docs/linkedin/day01-mockup.html      <- regenerate
# http://127.0.0.1:8000/docs/linkedin/day01-standalone.html  <- screenshot this
```

Verified: 1200 × 675 exactly · side A **Gauge** active, side B **Abs** active · `10` → `159.73369` ·
units bar / psi · English · all four copy points visible · card inside the frame.

##### Producing the image — ✅ automated

The browser tooling could not produce a pixel-exact PNG: the in-app pane never composites frames,
and the Chrome screenshot pipeline does not paint CSS `transform`/`zoom`, so scaled layouts
captured as stale frames. What works, reliably and without touching any other window:

```powershell
# 1. Serve the repo (python devserver.py <repo>), then open the graphic in an ISOLATED,
#    chrome-less window. A fresh --user-data-dir matters: Chrome otherwise restores the
#    previous window size and silently gives you the wrong client area.
chrome.exe --user-data-dir=$env:TEMP\og_cap_new --no-first-run --disable-extensions `
           --force-device-scale-factor=1 --window-position=0,0 --window-size=1530,920 `
           --app=http://127.0.0.1:8000/docs/linkedin/day01-standalone.html

# 2. Capture THAT window with PrintWindow(hwnd, hdc, 2). It reads the window's own pixels, so it
#    needs neither focus nor visibility — and cannot capture anything else on screen.
#    CopyFromScreen is the wrong tool: Windows refuses SetForegroundWindow from a background
#    process, so it silently grabs whatever is on top.
```

Then crop: detect the first row/column that is >85 % dark and take 1200 × 675 from there (the
window border and title bar sit outside it). `docs/linkedin/day01.png` was made this way.

##### Attaching the image — it works, via the OS clipboard

Everything scripted fails, and it is worth knowing why so nobody retries them: synthetic
drag-and-drop is ignored by LinkedIn's uploader; the `<input type="file">` exists only while the
media Editor is open and is hidden from the accessibility tree; injecting a `File` via
`DataTransfer` needs the bytes in the page and LinkedIn's CSP blocks `connect-src` to localhost;
and a synthetic Ctrl+V does not carry the OS clipboard.

**What does work:** put the PNG on the Windows clipboard, then paste into the composer.

```powershell
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$img = [System.Drawing.Image]::FromFile("docs\linkedin\day01.png")
[System.Windows.Forms.Clipboard]::SetImage($img)   # needs an STA thread; PowerShell 5.1 is STA
$img.Dispose()
```

Then click into the post body and press Ctrl+V. **The attach is not instant and the toolbar
changes as it lands** — the media icons are replaced by the image preview, which looks like the
paste failed. It did not. Scroll the composer down and confirm the preview before concluding
anything.

##### Composing the post

- Type the English body first, then paste the image, then append the Japanese section — appending
  text after the image is fine, the image stays attached below the text block.
- **The URL goes in the post body**, not only the first comment (maintainer's decision — a reader
  who never opens the comments still needs to know where the tool lives). LinkedIn rewrites it to
  an `lnkd.in` short link automatically; it still resolves.
- The pre-filled share link goes in the **first comment**, posted immediately after publishing.

##### Seven traps in this pipeline — read before building Day 2's graphic

**Trap 0, and the one that matters most: programmatic checks are not verification.** Values,
element sizes, arrow counts and colours all passed while the image was visibly broken — a white
3 px box around every element, a clipped footer, arrows pointing at nothing. *Look at the
picture before shipping it.*

The rest cost real debugging time and will recur on every card:

1. **Kill CSS transitions in the iframe first.** The Abs/Gauge buttons carry `transition-colors`.
   A transition is driven by the compositor's frame clock, so in any context that is not painting
   frames (headless capture, background tab, undisplayed pane) it **never advances** and
   `getComputedStyle` keeps returning the *starting* colour. The snapshot then shows the state you
   navigated away from — Abs/Abs on a graphic whose whole point is barg → psia. Inject
   `*{transition:none !important;animation:none !important}` before touching anything.
2. **Give the staging iframe a real desktop viewport** (1280 × 1000, parked off-screen). At 1 px
   wide the app renders its mobile layout and every computed width collapses — the card baked out
   2 px wide.
3. **`setLanguage()` is async and re-renders the card**, resetting the Abs/Gauge buttons. Set the
   language first, wait, *then* set modes and values. Also: the app persists language in
   `localStorage`, so a previous session in Japanese silently renders the English graphic in
   Japanese. Force the language explicitly every time.
4. **Tailwind's CDN JIT does not style markup injected after load.** Freeze computed styles inside
   the iframe, where the app's own build is applied — not in the mockup document. And because
   freezing strips `class` attributes, tag anything the annotation layer needs to find (element
   **IDs survive**; class-based selectors do not).
5. **A zero border width must still be written when freezing styles.** Tailwind's preflight sets
   `border-style: solid` with `border-width: 0` on every element. Drop the `0px` as "empty" and
   the browser falls back to `border-width: medium` — a 3 px box around *every node* in the
   snapshot. Skip zeros everywhere else, never on `border-*-width`.
6. **Freeze `transform` and `transform-origin` too.** The card carries `scale(1.18)`. Omit them
   and the frozen copy renders at 1.0 while the arrow coordinates were measured at 1.18, so every
   connector points at empty space.
7. **`<svg>` is a replaced element** — `position:absolute; inset:0` does *not* stretch it. It keeps
   its intrinsic 300 × 150 and silently clips every connector drawn beyond that. Set explicit
   `width`/`height` and a matching `viewBox`.

#### Japanese version

> ゲージ圧と絶対圧の取り違えは、1.013 bar の誤差です。
> やっかいなのは、その数字が「少し保守的な値」にしか見えないこと。
>
> 原因は計算ミスではありません。**基準を明記していないこと**です。だからレビューも通ってしまう。
>
> 10 barg を例に。
>
> ・基準を正しく宣言 → 159.73 psia
> ・絶対圧と思い込んだ場合 → 145.04 psia
>
> 差は 14.696 psi。ちょうど 1 気圧です。しかも「安全側に見える」方向にずれます。
>
> 覚えておく価値のある定数は 2 つだけ。
> ・1 atm = 101,325 Pa（定義値）
> ・1 psi = 6,894.75729 Pa
>
> 実務ルールとしては、**換算は絶対圧（Pa）を経由し、基準は最終報告書だけでなく受け渡しのたびに書く**。
> 「159.73 psia」は伝わりますが、「159.73 psi」は伝わりません。
>
> 自作の換算ツールでは、圧力カードの左右それぞれに独立した Abs/Gauge の切り替えを付けています。
> barg → psia が、引き算を挟まず 1 ステップで済む。
> 基準の選択ミス自体を防ぐことはできませんが、**基準を「書かずに済ませられない」形にはできます**。
>
> 無料・登録不要。収録している参照計算値はすべて公開しているので、手元の値と突き合わせて確認できます。
>
> 実際に工数を食われた単位の取り違え、何がありましたか。barg/bara か、ゲージ/絶対か、あるいはもっと厄介なものか。

**Japanese share link:** same state object with `"lang":"ja"` added, so the tool opens in Japanese.
**Hashtags:** `#プロセスエンジニアリング #LNG #配管設計 #石油ガス #エンジニアリング`

*Note: this is a rewrite, not a translation — it drops the "most free converters never ask"
line, which reads as a swipe in Japanese, and leads on the review-passes-anyway point instead.*

---

### Day 2 — Wed 12 Aug 2026 · ✅ POSTED

**Live:** https://www.linkedin.com/feed/update/urn:li:share:7493067132373499904/
(published 2026-08-12, one bilingual post + annotated graphic + first comment).

> **Shipped as ONE bilingual post**, not the EN/JA pair this sheet was originally drafted for —
> Day 1 established that pattern. Combined length **2,318 characters**, inside LinkedIn's 3,000.
> The Japanese section is a rewrite, not a translation, and carries the URL in its own right so a
> reader who scrolls straight to it still gets the link.
>
> **Defect found and fixed at draft time (C11):** the original draft said CH₄'s unrounded mole
> fraction was "0.888712…". It is **0.8886584…** (`0.888658452`, verified against the running app).
> The published post carries the correct figure. This is exactly what rule 2 — reproduce every
> number against the app, never copy it from the docs — exists to catch.

**Original sheet (as drafted) follows.**

**Title:** Why your HHV and the plant's HHV disagree in the second decimal
**Lens:** standards-credibility · **Format:** mini-tutorial · **Feature:** Advanced → JIS K 2301 engine

**Why this is Day 2:** it is the single most differentiated calculation in the product, and it
runs while Day 1's attention is still live. It also sets up the account's core promise — that
every number it shows can be traced to a rule someone wrote down.

#### English post

> Your gas analysis gives HHV 44.59 MJ/Nm³. A generic online calculator gives 44.6-something.
> Neither of you is doing the physics wrong.
>
> JIS K 2301 rounds five separate times, in a specific order — and that order is the entire answer.
>
> Walk it with me, on a normal pipeline gas (CH₄ 89, C₂H₆ 7, C₃H₈ 2.5, iC₄ 0.7, nC₄ 0.5, N₂ 0.3 vol%):
>
> 1. Volume → mole fractions, rounded to 4 d.p. CH₄ becomes 0.8887. Not 0.8886584…
> 2. Each component's Cm·√b is rounded to 5 d.p. **before** the sum, not after.
> 3. Z splits in two. Z_exact = 0.996759 drives HHV, LHV and SG. Z_rounded = 0.9968 drives the
>    standard density — and nothing else.
> 4. HHV and LHV land at 2 d.p. SG at 3 d.p.
> 5. Wobbe is built from the **already-rounded** HHV and the **already-rounded** SG.
>    44.59 / √0.634 = 56.00.
>
> Step 5 is the one that catches people. If you carry full precision into Wobbe you will get a
> defensible number that does not match the worksheet your gas quality is contractually judged
> against. The "more accurate" calculation is the one that fails traceability.
>
> One more that surprises people: Wobbe is always HHV-based per §7, whichever basis you happen to
> be reporting elsewhere.
>
> This is JIS K 2301:2011 specifically. ISO 6976 rounds differently and will correctly disagree —
> if your plant works to ISO, none of the above is your rule.
>
> I built the compositional engine in my converter to follow that cascade exactly, because
> matching the regulated worksheet digit-for-digit matters more than looking precise. The full
> reference case is published, so you can check it against your own sheet rather than trust me.
>
> If your spreadsheet disagrees in the second decimal, the rounding order is where to look.

**Length:** ~1,650 characters. ✓

#### Mockup spec

Two panels, 1200 × 675.

- **Left:** real screenshot of the Advanced composition column, the six components entered, results
  block in frame — HHV 44.59, LHV 40.25, SG 0.634, WI 56.00, MW 18.305, ρ_std 0.81930.
- **Right:** designed five-node cascade down a spine —
  (1) mole fractions → 4 d.p., showing `CH₄ 0.8887`;
  (2) Cm·√b → 5 d.p., annotated *"rounded BEFORE summing"*;
  (3) **the Z fork** — `Z_exact 0.996759 → HHV / LHV / SG` in amber, `Z_rounded 0.9968 → ρ_std only`
  in cyan. This is the visual payload of the whole post;
  (4) HHV/LHV → 2 d.p., SG → 3 d.p.;
  (5) `WI = 44.59 / √0.634 = 56.00`, annotated *"rounded inputs, by rule — not by sloppiness"*.
- Reproduce **no JIS table content** — arithmetic structure only.
- Reuse the Day 1 footer strip (URL + free / no sign-up / no tracking).

#### Mockup files — ✅ built, captured and published

| File | What it is |
|---|---|
| [`linkedin/day02-mockup.html`](linkedin/day02-mockup.html) | **The generator.** Loads `index.html` in an off-screen iframe, clears every composition field, enters the six components through the app's own inputs, and clones the resulting "3. Physical & Combustion Properties" card. Must be served over HTTP. Call `buildStandalone()` once `data-ready` is set to regenerate the deliverable. |
| [`linkedin/day02-standalone.html`](linkedin/day02-standalone.html) | **The deliverable.** A frozen 1200 × 675 frame, every style inlined — zero scripts, zero external references. |
| [`linkedin/day02.png`](linkedin/day02.png) | The published 1200 × 675 graphic. |

**As built, it differs from the spec above in two deliberate ways:**

- The left panel is the **properties card only** (HHV / MW / SG / WI / MCP / liquid density).
  ρ_std has no field on that card, and LHV is behind the HHV/LHV toggle, so both live in the
  cascade on the right instead of being claimed twice.
- A **standard caveat block** was added under the card: *"This is JIS K 2301:2011 specifically.
  ISO 6976 rounds differently and will correctly disagree."* A screenshot travels without its
  caption, and an image asserting 44.59 with no named standard is a claim the reader cannot check.

Only the sum `Σ = 0.056930` is shown for step 2, never the per-component √bᵢ coefficients —
that is what keeps "no JIS table content" true.

#### Verified numbers — *re-confirmed against the running app 2026-08-12, at publish time*

Mole fractions 0.8887 / 0.0704 / 0.0254 / 0.0073 / 0.0052 / 0.0030 · Z_exact 0.996759 ·
Z_rounded 0.9968 · **HHV 44.59** MJ/Nm³ · LHV 40.25 MJ/Nm³ · SG 0.634 · **WI 56.00** ·
MW 18.305 g/mol · ρ_std 0.81930 kg/Nm³ · MCP 36.9.

Intermediates behind the graphic, all reproduced from the app's own `gasComps` table:

| Quantity | Value |
|---|---|
| CH₄ mole fraction, **unrounded** | `0.888658452` → 0.8887 *(not 0.888712… — see C11)* |
| Σ ROUND(Cmᵢ·√bᵢ, 5) | **0.056930** |
| Z_exact, full precision | 0.99675898 |
| MW, full precision | 18.3049839 g/mol |
| ρ_std, full precision | 0.819299 kg/Nm³ |
| WI before rounding | 56.000621 → **56.00** |

Two behaviours confirmed live, both of which the post asserts:

- Toggling the card to **LHV** shows 40.25 **and leaves WI at 56.00** — Wobbe stays HHV-based
  per JIS K 2301 §7, exactly as the post claims.
- The share link restores on a **genuine page load** with HHV 44.59 / SG 0.634 / WI 56.00 /
  MW 18.305 / MCP 36.9 already rendered, zero clicks.

⚠️ **C10:** publish **WI = 56.00** and the division that produces it. Do **not** publish an
intermediate "55.997" — the true value is 44.59/√0.634 = **56.0006**, which rounds to 56.00.
⚠️ **C2:** do not claim this is the only card that renders on share-link open. `recomputeAll()`
runs seven client-side calculators.

#### Share link — ✅ built and verified on production

Opens the Advanced tab with this exact analysis already computed (**227 chars** — the sheet
previously said 235; re-counted at publish time):

```
https://engineering-converter.com/index.html#s=eyJ2IjoyLCJ0YWIiOiJhZHZhbmNlZCIsImlucHV0cyI6eyJjb21wLWNoNCI6Ijg5IiwiY29tcC1jMmg2IjoiNyIsImNvbXAtYzNoOCI6IjIuNSIsImNvbXAtaWM0IjoiMC43IiwiY29tcC1uYzQiOiIwLjUiLCJjb21wLW4yIjoiMC4zIn19
```

Japanese version (adds `"lang":"ja"`, **243 chars**):

```
https://engineering-converter.com/index.html#s=eyJ2IjoyLCJ0YWIiOiJhZHZhbmNlZCIsImlucHV0cyI6eyJjb21wLWNoNCI6Ijg5IiwiY29tcC1jMmg2IjoiNyIsImNvbXAtYzNoOCI6IjIuNSIsImNvbXAtaWM0IjoiMC43IiwiY29tcC1uYzQiOiIwLjUiLCJjb21wLW4yIjoiMC4zIn0sImxhbmciOiJqYSJ9
```

*Verified 2026-08-11 on a real load: opens on Advanced, HHV 44.59 / WI 56.00 / SG 0.634 / MW 18.305
already rendered, zero clicks.*

#### First comment

> The exact case above, already computed — swap in your own composition:
> https://engineering-converter.com/index.html#s=eyJ2IjoyLCJ0YWIiOiJhZHZhbmNlZCIsImlucHV0cyI6eyJjb21wLWNoNCI6Ijg5IiwiY29tcC1jMmg2IjoiNyIsImNvbXAtYzNoOCI6IjIuNSIsImNvbXAtaWM0IjoiMC43IiwiY29tcC1uYzQiOiIwLjUiLCJjb21wLW4yIjoiMC4zIn19
>
> The published reference values and the test suite that pins them:
> https://github.com/petronaoto/unit-converter

**Hashtags:** `#LNG #GasQuality #JISK2301 #ProcessEngineering`

#### Japanese version

> ガス分析値から HHV 44.59 MJ/Nm³。汎用のオンライン計算では 44.6 前後。
> どちらも物理を間違えているわけではありません。
>
> JIS K 2301 は**5 か所で、決められた順に丸める**。その順序こそが答えです。
>
> 標準的なパイプラインガス（CH₄ 89、C₂H₆ 7、C₃H₈ 2.5、iC₄ 0.7、nC₄ 0.5、N₂ 0.3 vol%）で追ってみます。
>
> 1. 体積分率→モル分率は **4 桁**に丸める。CH₄ は 0.8887。0.8886584… ではありません。
> 2. 各成分の Cm·√b は、**合計する前に** 5 桁へ丸める。後ではありません。
> 3. ここで Z が二手に分かれます。Z_exact = 0.996759 は HHV・LHV・SG に、
>    Z_rounded = 0.9968 は**標準密度にだけ**使われます。
> 4. HHV・LHV は 2 桁、SG は 3 桁。
> 5. ウォッベ指数は、**すでに丸めた** HHV と **すでに丸めた** SG から計算する。
>    44.59 / √0.634 = 56.00。
>
> 引っかかるのは 5 番です。フル桁のまま計算すれば、理屈の通った値は出ます。しかし、
> ガス品質が契約上照合される元の計算書とは合わなくなる。
> **「より正確な」計算のほうが、トレーサビリティを失う**わけです。
>
> もう一点。ウォッベ指数は §7 により常に HHV 基準です。他所で何基準を報告していても変わりません。
>
> これは JIS K 2301:2011 の話です。ISO 6976 は丸め方が異なり、当然違う値になります。
> ISO 準拠の設備であれば、上のルールはあなたの現場のものではありません。
>
> 自作の換算ツールの組成計算は、この丸めの連鎖をそのまま実装しています。
> 「精度が高そうに見えること」より、**元の計算書と桁まで一致すること**のほうが実務では重要だからです。
> 参照ケースの数値は公開しているので、私を信用せずに手元のシートと突き合わせて確認できます。
>
> 手元の計算が小数第2位で合わないなら、まず丸めの順序を見てください。

*Note: leads on the domestic reality — JIS is their governing standard and the contractual
worksheet is a real artifact, not an exotic one. The "generic online calculator" framing is kept
because it is factual, not a swipe at a named competitor.*

**Japanese hashtags:** `#プロセスエンジニアリング #LNG #都市ガス #JIS #ガス品質`

---

### Day 3 — Fri 14 Aug 2026 · *engagement post 1*

**Title:** There is no such thing as a tonnes-to-MMBtu factor
**Lens:** pain-workflow · **Format:** poll/question · **Feature:** General → Gas Volume + Custom Modules

> **Scope narrowed during review.** The original draft toured five converter cards and read as a
> catalogue. Cut to **one idea and one card**: mass→energy is not a conversion, it is your
> composition. Petroleum Gravity, Mass↔Vol Flow and the Advanced pointer are dropped.

**Hook**
> Tonnes in the shipping email, bcf on the terminal sheet, MMBtu on the invoice. Same cargo.
> Three people each converted it with their own factor, and the reconciliation is on Friday.

**Angle.** Two problems constantly get confused. The first is definitional and must never drift:
1 Nm³ = 37.3258 scf, one constant, used everywhere in the app including the JIS engine. The second
is **not a conversion at all** — mass to energy runs through the actual composition via HHV and
ρ_std, so any single "tonnes to MMBtu" factor pasted into an email is one composition frozen at one
moment. Saying that out loud in a meeting is usually the whole fix.

**Mockup.** Real screenshot: Gas Volume card, 1,000 kNm³ → 37.3258 mscf, annotated *"one constant,
shared with the JIS engine two tabs over"*; beside it the Custom Modules builder mid-build, with the
factor field circled — *"build the factor your contract actually uses, then send the card, not the number"*.

**Numbers.** 1 Nm³ = 37.3258 scf. Custom-module import limits: 20 modules per shared link,
40 characters per label (`MOD_MAX_SHARED` / `MOD_MAX_TEXT_LEN`).

**CTA.** "What's the unit argument your team keeps re-having?"

**Hashtags:** `#LNG #GasTrading #TerminalOperations #ProcessEngineering`

---

### Day 4 — *tracker **Day 4**, Fri 14 Aug 2026* · ✅ POSTED

> **Published Fri 14 Aug 2026 08:00 JST**, as scheduled on 2026-08-13. One bilingual post,
> **2,756 characters**, graphic attached, `engineering-converter.com` in the body of both language
> sections. No first comment — see the Day 3 sheet; that is the standing choice now.
> https://www.linkedin.com/feed/update/urn:li:share:7493672957697806337/
>
> Sheet number happens to match the tracker for this day (C12 affects Days 3, 5, 16, 17, 18, 20).

**Title:** 176.9 kPa of ΔP, and 2.3 kPa of it is friction
**Lens:** teach-theory · **Format:** worked example · **Feature:** Advanced → Pipe ΔP

**Hook**
> This line drops 176.9 kPa. Friction is responsible for 2.3 kPa of it. The other 174.6 kPa is
> just the fact that the pipe goes uphill.
> Only one of those two numbers is a line-sizing criterion, and it is not the big one.

**Angle.** A single-number ΔP tool is dangerous in opposite directions depending on which term
dominates. On this 45° riser 98.7 % of the drop is static head: a friction-only tool says the line
is fine while your pump is short of head; a lumped-total tool tells you to upsize a line whose
friction is already negligible. **Rule worth stealing:** size on frictional ΔP per 100 m and
velocity; put static head in the pump duty, not the line size.

**⚠️ C3 — state this in the post body, first person.** The static term is computed as
ρ_no-slip · g · Δz with a homogeneous mixture density and **no holdup model**. Day 9 then shows the
same line is Churn/Slug at +45°, precisely where slip is largest. So: the 174.6 kPa is *indicative
only*; a real case needs a mechanistic model. Then pivot to what survives — the friction sliver and
the velocity are far less slip-sensitive, and the line-sizing verdict deliberately reads the sliver.
Owning this makes the post stronger, not weaker.

**Mockup.** Left: pipe schematic — ID 4 in, L 100 m, Δz 70.711 m, θ = +45°, two-phase feed labelled.
Right: one 100 %-width stacked bar totalling 176.93 kPa — friction 2.338 kPa as a barely visible
sliver labelled 1.3 %, static 174.59 kPa filling the rest.

**Numbers.** §4 ΔP table. **Re-verified against the running app 2026-08-13** — the card was driven
with `calcDeltaPressure()` and `fetch` was wrapped to capture the endpoint's own response, because
`dpFric` / `dpStatic` exist only in the JSON and never reach the DOM:

| Quantity | Source | Published as |
|---|---|---|
| `dpPa` 176 928.8030035003 Pa | API | 176.9288 kPa (`#dp-out-total`), "176.9 kPa" in prose |
| `dpFric` 2 338.32734471651 Pa | API | **2.338 kPa · 1.3 %** (1.3216 % exact) |
| `dpStatic` 174 590.4756587838 Pa | API | **174.590 kPa · 98.7 %** (98.678 % exact) |
| `#dp-out-len` | DOM | 176.9288 **kPa/100 m** — the total, and the trap the post names |
| `#dp-out-dpfric100` | DOM | **0.0234 bar/100 m** — note the sizing screen shows this in **bar**, not kPa |
| `#dp-out-vratio` / `#dp-out-sizing-badge` | DOM | `v / v_max = 0.09` → **WITHIN LIMIT** (v_max 11.54 m/s) |
| `fr-badge` | DOM | **Churn / Slug Flow · θ = +45.0°** — re-run live, not quoted from §4 |
| `k_total` | API request | **0** — fittings untouched, so this is the clean Vector 2 case |

**No share link.** Every input in the reference case (`dp-id` 4, `dp-len` 100, `dp-elev` 70.711,
`dp-rough` 0.045, `dp-cfactor` 100, `dp-v-flow` 150, `dp-v-den` 10, `dp-v-visc` 0.012, `dp-l-flow`
7300, `dp-l-den` 500, `dp-l-visc` 0.12) is a hard-coded `value=` default in `index.html` — verified
by grep, not assumed. A pre-filled link would therefore carry nothing, so the post says "there is
nothing to type, open Advanced → Pipe ΔP and press Calculate" and links the bare domain instead.
That also keeps the body to one link. **If those defaults ever change, this post's claim breaks** —
re-check before reusing this copy.

**Mockup files.** `day04-mockup.html` (generator) → `day04-standalone.html` → `day04.png`.
Left is the app's real "3. HYDRAULIC OUTPUTS" block, cloned after a genuine round-trip to
`dp_calculator`; right is a designed decomposition fed from the captured API response. Two
departures from the mockup spec above, both deliberate:

- **No pipe schematic.** The spec's left panel was a drawn pipe with the inputs labelled. Showing
  the app's own output block instead makes the post's central claim — that the sizing verdict reads
  0.0234 bar/100 m and *not* the 176.9288 kPa/100 m sitting next to it — visible rather than
  asserted. The conditions moved to a one-line subtitle.
- **No connector arrow.** The obvious one runs from "dP / LENGTH" across to the amber callout and
  would cross the stacked bar, which is the one thing the graphic is about. Same reasoning as
  Days 1 and 3; `drawArrows()` is left empty with the explanation in place.

**Hashtags:** `#Hydraulics #LineSizing #FlowAssurance #ProcessEngineering #プロセスエンジニアリング #配管設計`

---

### Day 5 — *this sheet runs as tracker **Day 3**, Thu 13 Aug 2026* · ✅ POSTED

> **Published Thu 13 Aug 2026 08:00 JST**, exactly as scheduled 2026-08-12 via LinkedIn's own
> scheduler (the clock icon beside Post). One bilingual post, **2,263 characters**, graphic
> attached, URL in the body of both language sections. Scheduling worked end to end and is now the
> normal way to ship a day.
> https://www.linkedin.com/feed/update/urn:li:share:7493228666642923520/
>
> **No first comment was posted, and that is now the standing choice** (Naoto, 2026-08-13): the
> pre-filled share links below are optional extras, not a required step. A scheduled post cannot
> carry a comment, and the post already carries the URL in its body, so the day is complete without
> one. The drafted comment stays below for anyone who wants to add it by hand.
>
> Sheet number is pre-reflow (C12); the tracker slot is Day 3.

**Title:** The steam spreadsheet nobody owns
**Lens:** story-community · **Format:** behind-the-scenes · **Feature:** Basic Eng → Steam Properties (IF97)

**Hook**
> Every plant has one steam-property spreadsheet. Nobody remembers who wrote it, everyone uses it,
> and it dies the day IT tightens the macro policy.
> 4 MPa abs, 300 °C → h = 2,961.65 kJ/kg. No macro, no install, no login.

*(Pressure basis stated explicitly — the campaign opens on undeclared basis being the cardinal sin.)*

**Angle.** Two things worth saying. First, **state classification matters more than the numbers**:
at 4 MPa / 300 °C you are 49.6 K into superheat, and knowing that — plus T_sat and h_fg at the same
pressure — is usually the real question behind "what's the enthalpy". Second, the honest boundary:
IF97 **Region 3 is not implemented**, and the card returns a structured out-of-scope message rather
than extrapolating a confident wrong number.

**Mockup.** Real screenshot of the Steam card at 4 MPa / 300 °C with the full output grid.
Annotate: the STATE chip *"Region 2, superheat 49.64248 K"* — *"this is the answer to the question
you were actually asking"*; h and s boxed; the T_sat / h_fg row boxed. Second panel: the Region 3
refusal message.

**Numbers.** §4 steam row.

**Hashtags:** `#SteamSystems #Utilities #IAPWS #ChemicalEngineering #プロセスエンジニアリング`

#### Verified numbers — *reproduced against the running app 2026-08-12, at build time*

Every §4 steam value reproduced exactly. Full output grid at **4 MPa abs / 300 °C**:

| Quantity | Value |
|---|---|
| State | Superheated steam — **Region 2** |
| Superheat above T_sat | **49.64248 K** |
| Density ρ | 16.98717 kg/m³ |
| **Enthalpy h** | **2,961.65148 kJ/kg** |
| Entropy s | 6.36383 kJ/(kg·K) |
| Heat capacity c_p | 2.81995 kJ/(kg·K) |
| Sonic velocity w | 550.23169 m/s |
| **T_sat @ P** | **250.35752 °C** |
| **h_fg @ P** | **1,713.4713 kJ/kg** (h_f 1,087.42602 · h_g 2,800.89732) |

**Region 3 refusal, confirmed live.** At **25 MPa / 380 °C** (and again at 18 MPa / 360 °C) every
output blanks to `—` and the card shows, verbatim:

> ⚠ Region 3 (dense/near-critical) not covered — use full IF97 or vendor steam tables

20 MPa / 400 °C is still Region 2 (h 2,816.8362, 34.25409 K of superheat), so the boundary is real,
not a blanket refusal above some pressure.

**Provenance claim, checked before publishing:** `tests/test_steam_if97.py` (23 tests) extracts the
`const IF97` literal from `index.html` and re-runs the Release's own verification tables — Table 5
(Region 1), Table 15 (Region 2), Tables 35/36 (Region 4, both directions) and the B23 boundary —
at `REL_TOL = 5e-9`, i.e. the 9 significant figures the tables print. A separate test asserts the
"259 coefficients" claim is arithmetically true (34×3 + 9×2 + 43×3 + 10). Full suite: 242 passed.

#### Share link — ✅ built and verified on a real page load

Opens Basic Eng with the steam card already computed (**159 chars** — the shortest of the campaign
so far, because the card needs only four keys):

```
https://engineering-converter.com/index.html#s=eyJ2IjoyLCJ0YWIiOiJiYXNpYyIsImlucHV0cyI6eyJzcC1wIjoiNCIsInNwLXAtdSI6IjEiLCJzcC10IjoiMzAwIiwic3AtdC11IjoiQyJ9fQ==
```

Japanese version (adds `"lang":"ja"`, **175 chars**):

```
https://engineering-converter.com/index.html#s=eyJ2IjoyLCJ0YWIiOiJiYXNpYyIsImlucHV0cyI6eyJzcC1wIjoiNCIsInNwLXAtdSI6IjEiLCJzcC10IjoiMzAwIiwic3AtdC11IjoiQyJ9LCJsYW5nIjoiamEifQ==
```

*Verified 2026-08-12 on a genuine load with `localStorage` cleared: lands on Basic Eng with
Region 2 / h 2,961.65148 / T_sat 250.35752 / h_fg 1,713.4713 already rendered, zero clicks.*

#### First comment — ⏳ post this by hand once the scheduled post is live

> The exact case above, already computed — 4 MPa abs / 300 °C:
> https://engineering-converter.com/index.html#s=eyJ2IjoyLCJ0YWIiOiJiYXNpYyIsImlucHV0cyI6eyJzcC1wIjoiNCIsInNwLXAtdSI6IjEiLCJzcC10IjoiMzAwIiwic3AtdC11IjoiQyJ9fQ==
>
> 日本語で開く場合:
> https://engineering-converter.com/index.html#s=eyJ2IjoyLCJ0YWIiOiJiYXNpYyIsImlucHV0cyI6eyJzcC1wIjoiNCIsInNwLXAtdSI6IjEiLCJzcC10IjoiMzAwIiwic3AtdC11IjoiQyJ9LCJsYW5nIjoiamEifQ==
>
> The IF97 coefficient extraction test that re-runs the Release's own tables:
> https://github.com/petronaoto/unit-converter/blob/main/tests/test_steam_if97.py

*(564 characters, inside the 1,250 limit. The GitHub link was checked — HTTP 200 on `main`.)*

#### Mockup files — ✅ built, captured and attached to the scheduled post

| File | What it is |
|---|---|
| [`linkedin/day03-mockup.html`](linkedin/day03-mockup.html) | **The generator.** Clones the real `#basic-steam` card out of a live `index.html`, then drives the same card to 25 MPa / 380 °C and reads `#sp-warn` so the Region 3 quotation cannot drift from what the app says. |
| [`linkedin/day03-standalone.html`](linkedin/day03-standalone.html) | **The deliverable.** Frozen 1200 × 675 frame, styles inlined, no scripts, no external refs. |
| [`linkedin/day03.png`](linkedin/day03.png) | The attached 1200 × 675 graphic. |

Two deliberate departures from the mockup spec above:

- **The Region 3 panel is a designed quotation, not a screenshot.** Two full card screenshots will
  not both fit legibly in 1200 × 675 — at any scale that fits, the 10px warning text is unreadable.
  The panel quotes the app's exact string (read from `#sp-warn` at build time) and is styled
  unlike the app's chrome, so it reads as a quotation rather than a fake screenshot.
- **The card's 10px footnote paragraph is cropped out.** It does not survive LinkedIn's
  downscaling; its content (259 coefficients, Tables 5/15/35/36, the Region 3 scope) is carried by
  the copy instead.

No connector arrow: the only sensible one ran diagonally across the output grid and over the
enthalpy and entropy values. The left panel quotes the STATE chip's own wording instead.

---

### Day 6 — *tracker **Day 6**, Tue 18 Aug 2026* · 🕗 SCHEDULED

> **Scheduled 2026-08-15 for Tue 18 Aug 08:00 JST.** One bilingual post, **2,959 characters**,
> graphic attached, `engineering-converter.com` in the body of both language sections. Confirmed in
> *Scheduled posts* alongside Day 5. No first comment, per the standing choice on the Day 3 sheet.
>
> Sheet number matches the tracker for this day (C12 affects Days 3, 5, 16, 17, 18, 20).

**Title:** You cannot rearrange Colebrook-White. Here is what the solver is actually doing.
**Lens:** teach-theory · **Format:** mini-tutorial

**Hook**
> Colebrook-White has f on both sides of the equals sign. You cannot rearrange it into elementary functions.
> Every friction-factor formula you memorised is a curve fit to something that has to be iterated.

**Angle.** A genuine numerical-methods lesson in a piping context. The fixed-point loop, concretely:
start at f = 0.02, substitute into 1/√f = −2·log₁₀(ε/3.7D + 2.51/(Re√f)), take the new f, repeat to
1e-6 with a hard 100-iteration cap so it can never hang. Below Re = 2300 it does not iterate at all —
it short-circuits to the exact laminar f = 64/Re, because Colebrook is a turbulent correlation.

**Mockup.** Left: the equation rendered large, both occurrences of f circled in red, joined by an
arrow — *"this is why it is implicit"*. Right: an iteration table (iteration, f_guess, RHS, |Δf|)
starting at 0.02 and converging to 0.0183544.

**Numbers.** Converged f = 0.0183544 at Re = 2.2011 × 10⁵, ε = 0.045 mm, D = 0.1016 m.

**Verified against the running app 2026-08-15.** The endpoint returns only the converged f, never
the trace — so the trace was obtained by replaying `get_darcy_friction_factor` from
`api/dp_calculator.py` and **checking the replay's final f against the endpoint's own f to full
double precision** (`match=true` in the generator's `data-ready`). ε/D = 4.4291338582677165e-4,
Re = 220105.6680055071:

| iter | f in | f out | \|Δf\| |
|---|---|---|---|
| 1 | 0.020000000 | 0.018279010 | 1.72e-3 |
| 2 | 0.018279010 | 0.018358052 | 7.90e-5 |
| 3 | 0.018358052 | 0.018354202 | 3.85e-6 |
| 4 | 0.018354202 | 0.018354389 | 1.87e-7 → **below 1×10⁻⁶, stop** |

Converged f = **0.01835438889630599**; **the card displays 0.01835**, which is what the post quotes
in prose (the 9-decimal values appear only in the trace, where they are the point). Four iterations
— the 100-iteration cap never fires.

**Laminar branch, confirmed end-to-end** (not just by reading the source): the same line with the
liquid viscosity raised to 50 cP returns Re = **508.238**, `re_regime` = **Laminar**, f =
**0.12592526133946247**, which equals 64/Re exactly — `f == 64.0/Re` is `True` in Python, not merely
close. Zero iterations.

**Haaland and Swamee-Jain are NOT app features.** They were computed for the comparison panel and
the post says so explicitly. Formulas used, so anyone can check:
`1/√f = −1.8·log₁₀[(ε/3.7D)^1.11 + 6.9/Re]` → **0.0181738 (−0.98 %)**;
`f = 0.25/[log₁₀(ε/3.7D + 5.74/Re^0.9)]²` → **0.0184608 (+0.58 %)**.
This is the one place the campaign quotes a number the tool does not produce — keep the disclaimer
if the copy is reused.

**No share link.** Same reasoning as Day 4: this is the ΔP card's default case, so a pre-filled link
would carry nothing, and the ΔP card is server-backed and needs a Calculate click regardless.

**Mockup files.** `day06-mockup.html` → `day06-standalone.html` → `day06.png`. Left is the **real
Theory §4.2 block** (`data-i18n-html="docs.theory.b021"`), cloned live — it already states the
equation, the laminar branch and the tolerance/cap, so the post's claims appear in the app's own
words. Its two-phase HEM sub-box is cropped (different subject, and it would take the table's
space). **The Colebrook equation is additionally quoted at readable size in the right-hand panel**:
inside the cloned block it renders at 10px × 0.72 ≈ 7px and does not survive LinkedIn's downscaling,
and that equation *is* the post. Same call Day 3 made for the Region 3 refusal — text read from the
DOM, styling not pretending to be app chrome. Both occurrences of `√f` are marked, and the generator
**asserts there are exactly two** (`eq_f_occurrences=2`) rather than trusting the string split.

**CTA.** "If you use Haaland or Swamee-Jain in production, tell me where you've actually seen the
difference matter — I want the counter-argument."

**Hashtags:** `#FluidMechanics #NumericalMethods #Hydraulics #EngineeringEducation #プロセスエンジニアリング`

---

### Day 7 — Thu 20 Aug 2026

**Title:** The constant that looked precise and was wrong
**Lens:** story-community · **Format:** teardown · **Feature:** Advanced → ΔP erosional-velocity row

**Hook**
> From v2.4 until v2.8, my API RP 14E erosional-velocity check was 0.40 % non-conservative.
> The cause: I had "precisioned" a rounded 1.22 into √1.5.

**Angle.** RP 14E is written in field units — V_e = C/√ρ with ρ in lb/ft³ — and porting it to SI
needs an **exact unit conversion, not a tidy closed form**. The right constant is
0.3048·√16.0184634 = 1.2199032517, where 16.0184634 = 0.45359237/0.3048³: pure definitions, nothing
fitted. What shipped was 1.2247448714 — exactly √1.5, a rounded "1.22" reverse-engineered into a
plausible-looking radical. This is the most credibility-positive post in the campaign: it is a
public, specific, self-reported error with the fix and the reference value that moved.

**Mockup.** Top: a "constant autopsy" — 1.2247448714 struck through, *"= √1.5 exactly. That's the
tell."*; beside it 1.2199032517 with its derivation. Arrow between: *"+0.40 %, in the
non-conservative direction"*. Bottom: the ΔP erosion row before/after, V_e 7.72 → **7.689 m/s**.

**CTA.** "What do you actually do when a line screens above V_e — override with a corrosion study,
upsize, or change material? And does your company have a standing C-factor?"

**Hashtags:** `#FlowAssurance #API14E #ProcessSafety #Traceability`

---

### Day 8 — Fri 21 Aug 2026

**Title:** Your fittings are worth 30 m of pipe, not 23 m
**Lens:** teach-theory · **Format:** worked example · **Feature:** Advanced → ΔP fittings block

**Hook**
> Four elbows, a gate valve, a swing check, an entrance and an exit on a 4-inch line.
> The L/D shortcut says 23.16 m of equivalent length. The K method says 29.76 m.

**⚠️ C4 — the original "two reasons" framing was backwards.** Correct version:

- **The cause of the shortfall is entrance + exit.** They have no L/D at all — direct-K terms
  contributing **1.5** of the ΣK 5.3760, worth **8.3 m** of equivalent length and 194 Pa.
- **Separately, and in the opposite direction:** the n values assume fully-rough turbulent flow
  (f_T = 0.017 for 4-inch), but this line runs at f = 0.0183544. Since L_eq = ΣK·D/f, that makes the
  shortcut over-predict the valve and elbow losses by ~8 %.
- **The two errors partly cancel** — which is exactly why the shortcut's tally looks plausible.

*(Fix the corresponding paragraph in `SPECIFICATION.md` in the same pass.)*

**Mockup.** Two-column ledger. Left, K METHOD: 4× 90° elbow 4 × 0.5100 = 2.0400; gate 0.1360;
swing check 1.7000; entrance 0.5000; exit 1.0000; ΣK = 5.3760; ΔP_fittings = 5.376 × 129.4370 Pa =
695.85 Pa; L_eq = 29.75863 m at flowing f. Right, L/D SHORTCUT: Σn·D = 228 × 0.1016 = 23.16 m, with
entrance and exit greyed out and marked *"no n exists"*.

**Numbers.** §4 Crane row.

**Hashtags:** `#PipingDesign #Hydraulics #CraneTP410 #LineSizing`

---

### Day 9 — Mon 24 Aug 2026

**Title:** The pressure drop was fine. The flow regime wasn't.
**Lens:** pain-workflow · **Format:** mini-tutorial · **Feature:** Advanced → Flow Regime

**Hook**
> Same line, same 176.9 kPa, same WITHIN LIMIT badge. The map says Churn / Slug.
> ΔP is a number. Regime is a behaviour, and it's the one that wakes the control room.

**Angle.** A hydraulic result can be perfectly acceptable while the flow pattern is the actual
problem — slugging is a separator-level, pipe-support and control-valve-cycling problem, and no ΔP
number will tell you it is coming. Teach the geometry gate most tools hide: **θ = asin(Δz/L)**, and
at |θ| ≥ 30° the physics is vertical, so a Hewitt & Roberts type j_G vs j_L map is the right chart.

**⚠️ Caveat to state in the body:** the app's regime boundaries are **simplified and
piecewise-linear — qualitative orientation only**, not a transition criterion. The transferable
point is the inclination gate, which stands regardless of boundary fidelity. Publishing a plotted
point on a hand-simplified map one day after the Colebrook post, without this, is the campaign's
easiest own-goal.

**Mockup.** Left: the real rendered map, plotted point circled — *"Churn / Slug, θ = +45.0°"*, axes
annotated *"j_G vs j_L — vertical map, chosen because |θ| ≥ 30°"*. Right: a frame from the Three.js
3D animation.

**Numbers.** §4 flow-regime row.

**Hashtags:** `#FlowAssurance #TwoPhaseFlow #ProcessEngineering #Commissioning`

---

### Day 10 — Tue 25 Aug 2026 · *engagement post 2*

**Title:** Which roughness did you use?
**Lens:** story-community · **Format:** poll/question · **Feature:** Export PDF + Share links

> **Reframed during review.** The original read as a reproducibility platitude plus a feature tour.
> Lead instead with the **stale-result guard** — the genuinely uncommon idea — and ground the post in
> one real artifact: the exported report for the Day 4 case, disclaimer footer and gaps visible.

**Hook**
> Three weeks after handover, someone asks which roughness you used. The result is in the report.
> The input isn't.

**⚠️ C5 — describe the stale guard accurately.** `markResultStale()` **appends**
"· inputs changed — recalculate" to the existing badge and recolours it amber. It does **not**
replace the badge and does **not** clear outputs — the ΔP total, velocity, Re, f and V_e all stay on
screen. Correct line: *"the badge flags the result as stale; the figures stay visible."*

**⚠️ Export coverage — state the full omission list.** `exportReport()` covers composition and gas
quality, ΔP (incl. Re, f, erosion), the flow-regime map, PRV mode and orifice, and a Basic Eng subset
(pipe volume, Z-factor, API gravity, viscosity, mass/vol flow). **Not covered:** Steam, NPSHa,
Compressor, **Gas Property Estimator**, and the **fittings / line-sizing row**. A post about being
honest about scope must get its own scope list right.

**CTA.** "How does your team currently record which inputs produced a number — and has a stale
result ever made it into a document you signed?"

**Hashtags:** `#EngineeringManagement #DesignReview #Traceability #ProcessEngineering`

---

### Day 11 — Wed 26 Aug 2026

**Title:** Required area 5.7047 in². The letter is the easy part.
**Lens:** standards-credibility · **Format:** worked example · **Feature:** Safety → API 520 §5.6 gas

**Hook**
> Required area 5.7047 in². Nearest API 526 orifice: P, at 6.38 in².
> Nobody has ever queried the letter in a review. They query the C, the P_cf, and whether you were
> really in critical flow.

**Angle.** Relief sizing is twenty minutes of arithmetic and five seconds of picking a letter, and
the arithmetic is where the audit trail lives. Give the four numbers a reviewer actually asks for:
the critical pressure ratio (2/(k+1))^(k/(k−1)) = 0.5457 at k = 1.3; P_cf = 53.045 psia;
C = 346.9764; and therefore **critical flow — because P₂ sits below P_cf**, not because the tool
defaulted there.

**Mockup.** Real screenshot, Safety tab in gas mode with the published case loaded. Annotate the
output block and pull out the three intermediates.

**Numbers.** §4 PRV table, §5.6 row.

**CTA.** "Open the case, raise P₂ until it crosses P_cf, and watch the branch flip from critical to
subcritical — the fastest way to see where the equation actually switches."

**Hashtags:** `#ProcessSafety #ReliefSystems #API520 #PressureRelief`

---

### Day 12 — Thu 27 Aug 2026

**Title:** The bug that was unreachable until I fixed a default
**Lens:** story-community · **Format:** teardown · **Feature:** Safety → §5.10 two-phase (Omega)

**⚠️ C6 — the hook must be conditional.** The broken branch **never became the default path in any
released version**: the atmospheric-default fix (§11 #5) and the Leung-bracket fix (§11 #12) shipped
together in v3.0 PR-1, and #12 was found by adversarial review of PR-1.

**Corrected hook**
> A relief-sizing error sat in my two-phase code from v2.0 onward and literally nobody could trigger it.
> Fixing an unrelated default would have made it the default path — so both fixes shipped in the same PR.

**Angle.** Two coupled defects, one hiding the other. First: an omitted back-pressure defaulted to
zero — a perfect vacuum, not a conservative simplification but a physically impossible boundary
condition that forces the choked branch unconditionally, leaving the subcritical equation as dead
code for years. Second, inside that dead code, Leung's bracket was mis-coded: the −2 multiplied only
the log term instead of the whole bracket, giving subcritical flux **above** choked flux and
under-sizing valves 20–30 % on that branch. The continuity test now pins it: at η_a = η_c the
subcritical G must reproduce the critical-branch G, because that is how η_c is defined.

**Mockup.** A G-vs-η plot, η running 1 → 0. Old subcritical curve in red crossing **above** the
choked plateau, hatched *"physically impossible — choked flow is maximal"*; corrected curve meeting
the plateau exactly at η_c = 0.6564.

**Numbers.** §4 PRV table, §5.10 row *(this case is on the critical branch and is unchanged by the fix — say so)*.

**Hashtags:** `#ProcessSafety #ReliefSystems #API520 #TwoPhaseFlow`

---

### Day 13 — Fri 28 Aug 2026

**Title:** Napier, and the viscosity correction you cannot do in one pass
**Lens:** standards-credibility · **Format:** mini-tutorial · **Feature:** Safety → §5.7 steam, §5.8/§5.9 liquid

**Hook**
> Above 1,500 psia, steam relief needs the Napier correction. On this case it's 1.0115 — a 1.15 %
> change nobody notices when it's missing.
> And liquid sizing cannot be done in a single pass at all.

**Angle.** Two modes that get less attention than gas and two-phase, both hiding a loop.
**Steam:** A = W/(51.5·P₁·K_d·K_b·K_c·K_N·K_SH), with K_N switching on automatically above 1,500 psia
— reported as its own number so you can see that it acted. **Liquid:** you cannot correct for
viscosity in one pass, because the Reynolds number depends on the orifice area you haven't chosen
yet. The honest loop: size without K_v, select the orifice, compute Re on **that** area, apply K_v,
re-check.

**Mockup.** Left: real screenshot, steam mode, K_N = 1.0115 circled — *"fires automatically above
1,500 psia, and is shown as its own number"*. Right: a four-step loop diagram for liquid mode.

**Numbers.** §4 PRV table, §5.7 / §5.8 / §5.9 rows.

**Hashtags:** `#ProcessSafety #ReliefSystems #API520 #SteamSystems`

---

### Day 14 — Mon 31 Aug 2026

**Title:** Ideal gas costs you 7.5 % on the speed of sound
**Lens:** teach-theory · **Format:** myth-buster · **Feature:** Basic Eng → Gas Property Estimator

**Hook**
> Speed of sound in a 0.65-gravity gas at 2,000 psi and 150 °F: 441.0 m/s if you assume ideal gas,
> 410.0 m/s if you carry Z.
> 7.5 %, and it goes straight into your Mach number.

**⚠️ C7 — drop the API 520 attribution.** API 520 Part I sizes on the coefficient C and the critical
pressure ratio; it does **not** publish this sonic-velocity expression. Correct framing:
c = √(kZRT/M) is a **first-order real-gas correction** to the ideal-gas form — it carries Z but not
its pressure and temperature derivatives. Enough to show that ignoring Z at 2,000 psi is a 7.5 %
error; **not** a substitute for an EOS. Keep the SCREENING chip legible in the screenshot.

**Angle.** Since c scales as √Z, dropping Z at Z = 0.8646 inflates the answer by 1/√0.8646. High
pressure makes it worse, not better — the opposite of most people's intuition about when ideal gas
is "fine". Practical takeaway for flare headers, blowdown lines and Mach checks.

**Numbers.** §4 gas-properties row.

**Hashtags:** `#FlareSystems #Blowdown #GasProperties #ProcessEngineering`

---

### Day 15 — Tue 1 Sep 2026

**Title:** The calculator that refuses to tell you whether it passes
**Lens:** pain-workflow · **Format:** worked example · **Feature:** Basic Eng → Pump Suction NPSHa

**Hook**
> NPSHa = 7.457 m. That is the entire output. It will not tell you whether that passes.
> Not a missing feature: NPSHr is on the vendor's curve, and the margin tables belong to somebody else.

**Angle.** Separate the three things that get mashed together in every NPSH argument. **NPSHa is
arithmetic** — pressure head plus static minus friction, g = 9.80665 m/s² exactly — and every term
should be visible so a reviewer can check it in ten seconds. **NPSHr is data**; it comes off the pump
curve and no calculator can invent it. **The margin between them is judgement**, governed by
documents I will not paraphrase into a green tick.

**Mockup.** Real screenshot of the NPSHa card, water 80 °C, open tank, z = +3 m, h_f = 1.2 m, with
the breakdown boxed term by term and an arrow to the empty space where a verdict badge would go.

**Numbers.** §4 NPSHa row.

**CTA.** "The blank space is the feature. Where else should a calculator stop and hand the question back to you?"

**Hashtags:** `#RotatingEquipment #PumpDesign #Cavitation #ProcessEngineering`

---

### Day 16 — *this sheet runs as tracker **Day 5**, Mon 17 Aug 2026* · 🕗 SCHEDULED

> **Scheduled 2026-08-14 for Mon 17 Aug 08:00 JST.** One bilingual post, **2,972 characters**
> (the longest of the campaign so far — 28 under the limit), graphic attached,
> `engineering-converter.com` in the body of both language sections. Confirmed in *Scheduled posts*
> as "Posting Mon, Aug 17 at 8:00 AM". No first comment, per the standing choice recorded on the
> Day 3 sheet.
>
> Sheet number is pre-reflow (C12); the tracker slot is Day 5. Editorial decision 1 moved this
> material into week 1 — it works cold and needs no setup, and a skeptic decides about a free
> solo-built sizing tool in the first week, not the fourth.

**Title:** There are three versions of these coefficients on the internet
**Lens:** standards-credibility · **Format:** teardown · **Feature:** Basic Eng → Gas Property Estimator (viscosity)

**Hook**
> Lee-Gonzalez-Eakin gas viscosity has at least three coefficient sets in circulation.
> The tidy, rounded one is the one most people copied — and it is not what the paper says.

**Angle.** SPE 1340 (1966) published unrounded coefficients. What propagates through textbooks and
websites is a cleaned-up variant that is easier to type and measurably different — and two further
corruptions exist in the wild: **X = 3.488 instead of 3.448** (a transposed digit that survived
because it looks right) and **0.001·M in place of 0.01·M** (an order of magnitude, quietly). None of
them announce themselves. The project pins all nine original literals in tests and forbids the three
known-bad forms outright.

**Mockup.** Coefficient provenance table, three columns: ORIGINAL SPE 1340 (green), ROUNDED VARIANT
(amber), CORRUPTED VARIANTS (red).

**Numbers.** Original form: K = (9.379 + 0.01607M)T^1.5/(209.2 + 19.26M + T); X = 3.448 + 986.4/T +
0.01009M; Y = 2.447 − 0.2224X.

> ✅ **The caveat on this sheet is resolved.** It read: *"the ≈ −2.1 % shift for the rounded variant
> is the project's own figure with no stated basis state — publish it as 'about −2 % on our
> reference state', or recompute and quote case-specific."* It was recomputed, on 2026-08-14, and
> the docs' figure holds: **−2.1468 %** on the §9 Vector 6 state. The post quotes −2.15 % **with the
> state attached**, which is what the caveat asked for.

**Verified against the running app 2026-08-14.** All four rows were evaluated from the app's *own*
ρ, T_R and M — `toPsia()`, `toRankine()`, `papayZ()`, `MW_AIR_GP`, `R_PSIA_GP`, `LB_FT3_PER_G_CM3` —
so the only thing differing between rows is the nine coefficients. State: SG 0.65 · 2,000 psi ·
150 °F · k 1.3 → Z = 0.8645842, ρ = 0.10662709 g/cm³, M = 18.827055 g/mol.

| Coefficient set | μ (cP) | vs original |
|---|---|---|
| Original SPE 1340 — 9.379 / 0.01607 / 209.2 / 19.26, X = 3.448 + 986.4/T + 0.01009M, Y = 2.447 − 0.2224X | **0.01666** (0.016663471) | — |
| Rounded — 9.4 / 0.02 / 209 / 19, X = 3.5 + 986/T + 0.01M, Y = 2.4 − 0.2X | **0.01631** (0.016305747) | **−2.15 %** |
| Corrupted — X = 3.488 | **0.01680** (0.016803750) | **+0.84 %** |
| Corrupted — 0.001·M | **0.01611** (0.016113649) | **−3.30 %** |

The card itself displays **0.01666 cP** (5 d.p.), which is what the post and the graphic quote —
*not* the 0.016663 in §4, which is the unrounded value and would not match what a reader sees.
All four variants stay distinguishable at the card's own display precision, so the table needs no
extra digits. Also confirmed live: Z 0.8646, c 410.02694 m/s, μ_JT 0.32787 K/bar; `pytest` 242 passed.

**Share link** (works on a real page load; the Gas Property Estimator is client-side, so it renders
on open with no Calculate click — 203 chars EN / 219 JA). Not used in the body, since the post asks
readers to type four numbers instead and that keeps it to one link per language section. Kept here
for any comment or repurposing:

```
https://engineering-converter.com/index.html#s=eyJ2IjoyLCJ0YWIiOiJiYXNpYyIsImlucHV0cyI6eyJncC1zZyI6IjAuNjUiLCJncC1wIjoiMjAwMCIsImdwLXAtdSI6InBzaSIsImdwLXQiOiIxNTAiLCJncC10LXUiOiJGIiwiZ3AtayI6IjEuMyJ9fQ==
https://engineering-converter.com/index.html#s=eyJ2IjoyLCJ0YWIiOiJiYXNpYyIsImlucHV0cyI6eyJncC1zZyI6IjAuNjUiLCJncC1wIjoiMjAwMCIsImdwLXAtdSI6InBzaSIsImdwLXQiOiIxNTAiLCJncC10LXUiOiJGIiwiZ3AtayI6IjEuMyJ9LCJsYW5nIjoiamEifQ==
```

**Mockup files.** `day05-mockup.html` → `day05-standalone.html` → `day05.png`. The real card on top,
the four-way table underneath. The mockup spec's three-column provenance table (green / amber / red)
became four rows instead — the rounded variant and the two corruptions are three distinct rows, and
a row per set is what lets each carry its own μ and Δ. Colours kept: emerald / amber / rose.

**What the post says about CI**, all verified in `tests/test_js_constants.py`: nine literals pinned
by a parametrized test; a separate test asserting the three known-bad forms are absent **from the
script block only**, via a fixture that strips the prose; and the converse test
`test_theory_tab_names_the_bad_variants`, which *requires* the manual to keep naming X = 3.488.
That pairing — the same string forbidden in code and mandatory in the docs — is the strongest
detail in the post; do not paraphrase it away if this copy is reused.

**Hashtags:** `#GasProperties #Correlations #Traceability #ReservoirEngineering #プロセスエンジニアリング`

---

### Day 17 — Thu 3 Sep 2026

**Title:** A green CI badge is not evidence
**Lens:** story-community · **Format:** behind-the-scenes

**Hook**
> My CI badge was green for an entire release cycle while a large block of my tests never ran.
> Including every guard on the share-link import sanitiser — the security-relevant ones.

**Angle.** The workflow passed an explicit **allowlist of test files**. It was written when there
were four files; more arrived in later PRs and the list was never extended. Local runs were green
because pytest discovers everything; CI was green because it ran what it was told. Nothing was red,
nothing was broken, and a block of tests was decoration for months. The fix: run pytest with a single
discovery command, and never give CI a list of files to trust.

**Mockup.** Top: a mock CI summary panel, green check, *"all checks have passed"*, with a small red
annotation — *"and a third of the suite never ran"*. Bottom: the ten-reference-vector table, one row
each with its headline number.

**Numbers.** **242 tests** collected (verified 2026-08-11), 13 modules, ten documented reference
vectors. **C9: not 183.**

**Hashtags:** `#SoftwareQuality #CI #EngineeringComputing #Traceability`

---

### Day 18 — *this sheet runs as tracker **Day 20**, Mon 7 Sep 2026* · **campaign closer**

**Title:** Five things this calculator refuses to do
**Lens:** standards-credibility · **Format:** myth-buster

> Sheet number is pre-reflow (C12); the tracker slot is **Day 20**. Editorial decision 2 promoted
> this to the closing post — the strongest evergreen piece in the set, and the one most likely to
> be shared after the campaign ends. Write it as an ending.

**Hook**
> The most valuable thing an engineering tool can do is stop.
> Mine stops in five specific places, and every one of them was a decision I can defend.

**Angle.** Busts the genre's assumption that more coverage is better. Five refusals, each with a
reason: (1) NPSHa renders **no pass/fail verdict**; (2) the steam card **refuses IF97 Region 3**
rather than extrapolating; (3) API 526 **over-range is marked**, not silently clamped; (4) Papay and
LGE **warn outside their envelopes**; (5) the line-sizing screen cites **NORSOK only** and the Crane
set omits reducers rather than guessing them.

**➕ Add the sixth, and make it the strongest:** *when to stop using this tool entirely and open the
simulator.* The audience review flagged that nothing in the campaign answers the obvious objection —
why this rather than the company spreadsheet, or HYSYS/Aspen for the two-phase cases. A tool that
names its own ceiling outperforms every feature post.

**Mockup.** Five (six) tiles, each a cropped real screenshot plus one annotation line.

**Hashtags:** `#EngineeringJudgement #ProcessEngineering #Standards #EngineeringTools`

---

### Day 19 — Mon 7 Sep 2026

**Title:** No login, no cookies, and the share link never reaches my server
**Lens:** pain-workflow · **Format:** behind-the-scenes

**Hook**
> There's no sign-up on the tool I built, no cookie banner, and no analytics script.
> The share links don't even reach my server — the whole calculation state rides in the URL fragment.

**Angle.** The transport: a share link is `origin + path + '#s=' + base64(state JSON)`, and everything
after the `#` is a **fragment, which browsers never transmit**. A pre-filled calculation is
reconstructed entirely in the recipient's browser — invisible to the server, to any CDN cache, and to
me. Not privacy bolted on; the cheapest implementation that happens to be private. Pair with:
custom modules live in localStorage only; the Python endpoints are stateless.

**⚠️ C8 — use measured numbers.** Stock full-state link: **4,627 characters** (measured 2026-08-11).
App warns above 2,000. Use a **hand-authored ~300-character link** in the graphic (§3 recipe) and say
plainly why: the full link carries every field by design; for chat, trim it.

**➕ Add:** the ten shipped UI languages and the control-room/phone angle — a no-install browser tool
that opens on a locked-down plant network is where this actually wins.

**Mockup.** Top: one short hand-authored share URL in mono type, split into two coloured segments —
origin and path in grey *"sent to the server"*, the `#s=…` payload in amber *"never leaves the
browser"*, with a dotted line showing the amber part stopping at a boundary marked *"network"*.

**Hashtags:** `#EngineeringTools #Privacy #PlantIT #ProcessEngineering`

---

### Day 20 — *this sheet runs as tracker **Day 18**, Thu 3 Sep 2026* · *engagement post 3*

**Title:** The whole toolbox on one page, and ten published vectors
**Lens:** story-community · **Format:** capability tour + question

> Sheet number is pre-reflow (C12); the tracker slot is **Day 18**, not the closer. Editorial
> decision 2 moved this material forward and gave the closing slot to "Five things this calculator
> refuses to do" (sheet `### Day 18`).
>
> ⚠️ **Do not write this as a retrospective.** The campaign still has two posts to run when this
> goes out, so "twenty posts in / twenty days later" framing is factually wrong here. It is a
> **capability tour**: here is everything, here is the evidence behind it, what's missing?

**Hook**
> Seventeen posts, and I still haven't shown you the pipe-volume card, the LNG density card, or the
> compressor card.
> So here's the whole thing on one page — and the only question I actually want answered.

**Angle.** Lay the toolbox out flat: pipe volume for line packing and hydrotest; three-way °API ↔ SG
↔ density; dynamic ↔ kinematic viscosity; mass ↔ volumetric flow at a stated density; temperature and
heating value; LNG liquid density by ISO 6578 Klosek-McKinley; compressor head and power. Then
restate the spine: ten published reference vectors, 242 tests, no sign-up, no tracking, ten languages.

**Mockup.** One page, two zones. Top: a labelled map of the app — five columns (General, Basic Eng,
Advanced, Safety, cross-cutting) with every card as a chip, the eleven never given a dedicated day
highlighted in amber. Bottom: the ten-vector table.

**Numbers.** LNG liquid density: **name the method, quote no number** — there is no documented
reference vector for it in §9. *(Add one, then write the standalone LNG density post from the bench.)*

**CTA.** "What card is missing? On my list: a calculation notebook with run history, a Cv and orifice
sizing pack, and more languages."

**Hashtags:** `#ProcessEngineering #OilAndGas #EngineeringTools #BuildInPublic`

---

## 8. Ideas bench (not scheduled)

Ready to write when the blocker clears:

- **LNG liquid density (ISO 6578 Klosek-McKinley)** — write it the day a reference vector is added to `SPECIFICATION.md` §9. A post whose central number needs verification should not be scheduled.
- **IF97 Region 3 verification** — a standalone piece on why the region is hard and what refusing it costs.
- **"What a share link cannot do"** — the cards that still require a Calculate click, and why the server-backed ones are drawn that way.
- **Temperature / heating-value beginner post** — for a slower week.
- **Mobile in the control room** — the no-install angle, with a phone screenshot.
- **A Japanese-first post pinned to the `ja` build** — for the Qiita/Zenn crossover audience.

## 9. Cadence notes

- **Best posting window:** 08:00–10:00 in the audience's timezone. English post morning CET
  (evening JST); Japanese post next morning JST.
- **Comments are the campaign.** Reply to every comment in the first 90 minutes — LinkedIn weights
  early engagement heavily. The Day 6, 7, 13 and 15 CTAs are written to invite disagreement; treat a
  well-argued "actually…" as the best possible outcome and say so publicly.
- **Never argue a correction.** If someone catches an error, fix it, credit them, and post the fix.
  Day 7 and Day 17 exist to establish that this is the account's normal behaviour.
- **Repurposing:** Days 2, 6, 8, 13 and 16 are already long-form article material — expand to
  Qiita/Zenn (Japanese) per `MARKETING.md` §4.
- **Do not post the raw Share-button link anywhere.** §3.

---

*Log started 2026-08-11. Update the tracker in §2 the day each post goes live.*
