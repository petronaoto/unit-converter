# Development Plan — O&G Engineering Converter

**Document version:** 1.1 (accompanies app v2.6)
**Maintainer:** Naoto Yamabe (petro.naoto@gmail.com)
**Repository:** <https://github.com/petronaoto/unit-converter>
**Companion documents:** [SPECIFICATION.md](SPECIFICATION.md) (feature-level detail) · [MARKETING.md](MARKETING.md) (promotion strategy)

---

## 1. Vision & Mission

> **A standards-traceable, zero-signup, browser-native engineering partner for gas and LNG facilities — fast enough for the control room, documented enough for the design office.**

The O&G Engineering Converter replaces the fragmented legacy Excel spreadsheets that circulate in gas processing and LNG plants with a single, trustworthy, always-current web application. Every number it produces is traceable to a governing standard (JIS K 2301, ISO 6578, API 520, API RP 14E, …), and every calculation method is documented inside the app itself.

The long-term goal is for the tool to serve as a **career-long partner**: a junior engineer or panel operator should be able to learn *why* a calculation works from the embedded Theory tab, while a senior lead should be able to cite the exact standard clause and rounding chain behind a result.

## 2. Target Users (Personas)

| Persona | Needs | How the tool serves them |
|---|---|---|
| **Junior engineer / panel operator** | Quick, mistake-proof conversions; guidance on which method applies; guardrails against invalid inputs | Live converters, out-of-range warnings (Papay envelope, ISO 6578 temperature range, composition sum), How To Use manual with wireframes |
| **Mid-career process engineer** | ΔP and line screening, PSV sizing checks, flow-regime orientation, handover of calculation cases | Darcy-Weisbach/Colebrook ΔP with erosional-velocity check, API 520 sizing (5 modes), Flow Regime visualizer, Share links, Export PDF |
| **Senior / lead engineer** | Regulatory traceability, exact reproduction of reference worksheets, documented assumptions | Strict JIS K 2301 rounding cascade (matches the Excel reference sheet digit-for-digit), Theory tab with constants tables, reference test vectors under version control |

## 3. Architecture Principles

These principles are deliberate and stable; changes to them are major-version decisions.

1. **Hybrid Edge-Server.** All standard conversions and the JIS K 2301 compositional chain run client-side (instant, offline-tolerant). Iterative or heavy math (Colebrook-White, API 520 critical-flow, regime-map rendering) runs in Python serverless functions on Vercel.
2. **Single-file, no-build frontend.** `index.html` contains all markup, styling (Tailwind via CDN) and JavaScript. There is no bundler, no framework, no node_modules. This maximizes longevity and auditability at the cost of file size.
3. **Standard-library-only APIs where possible.** `api/dp_calculator.py` and `api/psv_calculator.py` use only the Python standard library. Only `api/flowregime.py` carries dependencies (numpy/matplotlib/seaborn) for map rendering.
4. **Element IDs are an API.** JavaScript addresses the DOM by ID throughout; IDs are never renamed or removed without a coordinated change (see CLAUDE.md preservation rules).
5. **Preservation-first change policy.** Surgical, minimal diffs; no speculative refactoring; silent feature loss is treated as the most serious failure mode.
6. **Zero data harvesting.** No accounts, no cookies, no analytics scripts, no server-side logging of user data. State lives only in the browser (`localStorage`) or in explicitly shared URLs.
7. **Self-contained documentation.** Operating manual (How To Use) and calculation theory (Theory) are embedded in the app and updated in the same commit as the feature they describe (Documentation Sync Rule).

## 4. Version History

Reconstructed from the git log and tags (all dates 2026).

| Version | Date | Milestone |
|---|---|---|
| v1.0–v1.2 | Mar 29–31 | Initial dark-mode dashboard; Btu/scf heating-value standard; LNG-plant background |
| v1.3 | Mar 31 | Custom-module presets (flow rate, density, viscosity) |
| v1.4 | Mar 31 | Sticky header, tab navigation, Terms/Privacy legal docs |
| v1.5 | Mar 31 | Interactive **How To Use** manual with embedded CSS wireframes |
| v1.6 | Mar 31 | `localStorage` persistence, copy-to-clipboard, Advanced calculators, Report email integration |
| v1.7 | Mar 31 | First **Pipe ΔP calculator** |
| v1.8 | Apr 1–2 | **Compositional GHV suite** with strict JIS K 2301 routing; **Theory tab** |
| v1.9 | Apr 3–4 | Exact JIS K 2301 formulas, **ISO 6578 LNG density** (Klosek-McKinley), General-tab restoration, TDZ crash fix |
| v1.10.x | Apr 4 | **Python serverless API** to production; CORS; docs corrections; IndentationError hotfixes (v1.10.1–.3) |
| v2.0 / v2.0.1 | Apr 5–6 | **Safety tab — API 520 Part I PRV sizing** (§5.6 gas, §5.7 steam, §5.8/§5.9 liquid, §5.10 + Annex C Omega two-phase); API 526 orifice selection |
| v2.1 / v2.1.1 | Apr 6–7 | Abs/Gauge pressure toggles; unit-onchange and ΔP unit-cache fixes |
| v2.2–v2.2.2 | Apr 11 | **LHV values corrected to JIS K 2301 Table 30** (reference LHV 40.25 MJ/Nm³); HHV/LHV toggle relocation; comma formatting; **README.md created** |
| v2.3 / v2.3.1 | Jun 13 | **Flow Regime visualizer** (server-side seaborn map + Three.js 3D animation); CLAUDE.md project memory; density unit-conversion fix (multiply-to-SI, v2.3.1) |
| v2.4 | Jun 28 | **API RP 14E erosional velocity** on the ΔP card; three new Basic Eng converters (Petroleum Gravity, Viscosity, Mass↔Vol Flow); Export PDF, Share links, session auto-restore; out-of-range guards; Darcy-Weisbach rename; unit-selector consistency fixes |
| v2.5 | Jul 2026 | **Documentation & UX release** — `docs/` folder (this document, SPECIFICATION.md, MARKETING.md); Theory §4.1 corrected to Papay; tab-navigation accessibility (scroll-into-view, ARIA tablist); back-to-top + section anchors in doc tabs; Enter-to-calculate and client-side validation hints on ΔP/PSV; export pop-up fallback; distinct viscosity unit values; stale-input indicator on server-backed cards |
| **v2.6** | Jul 2026 (PR #3) | **Internationalization Milestone 1** — full i18n mechanism (`i18n/en.json`/`ja.json` dictionaries, `tr()`/`applyTranslations()`/`setLanguage()`, two-part header switcher); complete English↔Japanese translation of the working tool (General, Basic Eng, Advanced, Safety, floating action bar, Report form, module modal, every JS-generated dynamic string); settings menu lists 8 more languages as "coming soon". See §5 and SPECIFICATION.md §12 for full detail. |

## 5. Current State (v2.6)

### Feature inventory

- **9 tabs:** General · Basic Eng · Advanced · Safety · How To Use · Theory · Terms of Use · Privacy Policy · Report.
- **General:** Gas Volume (Nm³↔scf), Pressure ×2 with Abs/Gauge toggles, Temperature, Heating Value (MJ/Nm³↔Btu/scf), user-defined Custom Modules with presets.
- **Basic Eng:** Pipe Volume (canonical card layout), Z-Factor (Papay + Standing-Katz), Petroleum Gravity (°API↔SG↔ρ), Viscosity (dynamic↔kinematic), Mass↔Volumetric Flow.
- **Advanced:** Compositional GHV & Flow (JIS K 2301, 14 components, HHV/LHV/SG/WI/MCP/MW, ISO 6578 LNG density, mass↔vol↔mol flow), Pipe ΔP (Darcy-Weisbach + Colebrook-White + HEM two-phase + RP 14E erosion check), Flow Regime (Hewitt & Roberts / Baker maps + 3D animation).
- **Safety:** API 520 Part I PRV sizing, five modes, API 526 orifice letters.
- **Productivity:** copy buttons, Export PDF report, Share links, session auto-restore, out-of-range warnings.
- **Serverless:** `/api/dp_calculator`, `/api/psv_calculator` (stdlib only), `/api/flowregime` (numpy/matplotlib/seaborn).

### Internationalization (i18n) status

Shipped in v2.6 as **Milestone 1** of a multi-milestone program (full technical detail in SPECIFICATION.md §12):

- **Translated (EN ⇄ JA), fully working today:** General, Basic Eng, Advanced, Safety tabs; floating action bar; Report form; module-config modal; every JS-generated dynamic string (calc warnings/badges, toasts, PSV results, the PDF export document, mailto body). Default language is English; a returning visitor's language choice persists; share links can carry an explicit language.
- **English-only for now:** the How To Use, Theory, Terms of Use, and Privacy Policy tabs (~4,300 words of documentation/legal prose) — deliberately deferred, see Milestone 3 below.
- **Scaffolded but not yet translated:** Chinese, Korean, Thai, Indonesian, Russian, Spanish, French, German. The settings menu already lists all 10 languages; the 8 pending ones show as disabled "coming soon" entries — enabling each is a matter of adding its dictionary file, not further engineering.
- **Not yet localized:** the three Python API endpoints still return English prose for server-generated status/error text (see Milestone 4 below).
- Calculation logic was not touched by this work — the JIS K2301 reference vectors (§9 in SPECIFICATION.md) reproduce byte-identically in both languages.

See "Internationalization Program — next milestones" under §6 Roadmap for the decision points on what to do next.

### Known limitations (honest register)

| Limitation | Status |
|---|---|
| No dedicated mobile navigation (tab bar scrolls horizontally) | Roadmap v2.6 |
| Custom modules are not encoded in Share links (localStorage only) | Roadmap v2.6 |
| Mixed interaction model: converters update live, server cards need a button click | Mitigated in v2.5 (stale-input indicator, Enter-to-calculate) |
| Very small label typography in dense cards may fall below WCAG contrast targets | Backlog (needs a careful, sweeping pass) |
| API error responses are not yet schema-harmonized across the three endpoints | Proposed fix awaiting approval (see SPECIFICATION.md §11) |
| dp_calculator input edge cases (zero viscosity/density) can produce an unstructured 500 | Proposed fix awaiting approval (see SPECIFICATION.md §11) |
| No automated test suite; regression relies on the manual reference-vector checklist | Roadmap v2.7 (pytest + CI) |
| How To Use / Theory / Terms of Use / Privacy Policy tabs, and 8 of the 10 planned UI languages, are English-only | Roadmap — i18n Milestones 2 & 3, see §6 |
| Server-generated status/error text (ΔP/PSV/Flow Regime badges) is English regardless of UI language | Roadmap — i18n Milestone 4 (optional), see §6 |

## 6. Roadmap

Each item enters a release only after explicit approval by the maintainer. Effort: L < 1 day · M = 1–3 days · H > 3 days.

### v2.7 — "Junior engineer value pack" (proposed)

(Renumbered from the originally-proposed "v2.6" — that version number was taken by the i18n Milestone 1 release instead; see §4 and §5.)

| Feature | Value | Effort | Notes |
|---|---|---|---|
| Gas viscosity (Lee-Gonzalez-Eakin) | High | L | Client-side; pairs naturally with the Z-Factor card inputs |
| Sonic velocity & Joule-Thomson coefficient | Med | L | Client-side; same input set (SG, P, T, k) |
| Line sizing helper (velocity + ΔP/100 m vs. typical service criteria) | High | M | Reuses ΔP outputs; large value for juniors sizing lines |
| Fittings / K-factor equivalent length in the ΔP card | High | M | Backward-compatible payload extension to dp_calculator |
| pytest + GitHub Actions reference regression (JIS vector, dp/psv cases) | High | M | Directly protects the CLAUDE.md reference values on every push |
| Mobile navigation affordance (hamburger or wrap) | Med | M | Deferred from v2.5 (layout restructure, needs design care) |
| Custom modules in Share links (state format v:2) | Med | M | Deferred from v2.5 (state versioning required) |

### Internationalization Program — next milestones

Milestone 1 (English ⇄ Japanese for the working tool) shipped in **v2.6** (PR #3, merged). The remaining program is independent of the v2.7/v3.0 feature roadmap above and can be sequenced whenever it makes sense:

| Milestone | Scope | Effort | Notes |
|---|---|---|---|
| **M1 — shipped (v2.6)** | i18n mechanism + full EN/JA translation of General, Basic Eng, Advanced, Safety tabs, action bar, Report form, module modal, and all JS-generated strings | — | Merged; see SPECIFICATION.md §12 |
| **M2** | Same scope as M1, remaining 8 languages (Chinese, Korean, Thai, Indonesian, Russian, Spanish, French, German) | M | Mechanically identical to M1 — no new engineering. The settings menu already lists all 10 languages; each pending one just needs an `i18n/<code>.json` dictionary and its `enabled` flag flipped in `LANGUAGES` |
| **M3** | How To Use, Theory, Terms of Use, Privacy Policy tabs — ~4,300 words, up to 9 languages | H | Largest remaining content volume. **Terms of Use and Privacy Policy translations need the maintainer's own legal review before publishing** — mistranslated jurisdiction/liability clauses carry real risk |
| **M4 (optional)** | `api/dp_calculator.py`, `api/psv_calculator.py`, `api/flowregime.py` return machine-readable status/error keys instead of English prose, so server-driven text (flow-regime classification, validation errors) can localize too | M | Backend-only, stdlib-safe additive payload change. `flowregime.py` already returns `regime_key` alongside its English `regime` label (SPECIFICATION.md §5.3) — the other ~10+ message/error branches across the three files remain unkeyed |

**Decision points:** M2 and M3 are independent — either can go first. M2 carries essentially zero engineering risk (pure translation volume against an already-proven mechanism). M3 needs legal-review time budgeted in before publishing. M4 improves consistency for the server-backed cards but isn't a prerequisite for M2 or M3.

### v3.0 — "Professional pack" (proposed)

| Feature | Value | Effort | Notes |
|---|---|---|---|
| Calculation notebook (save/load named scenarios) | High | M | Natural extension of the existing state system |
| PWA / offline mode for client-side tabs | Med | M | Service worker; API cards must degrade gracefully |
| Control valve Cv sizing (IEC 60534 lite, liquid/gas) | Med | M | Client-side |
| Orifice / venturi metering (ISO 5167 lite) | Med | M–H | Iterative; candidate for a fourth API endpoint |
| Steam tables (IAPWS-IF97 lite, regions 1/2/4) | Med | H | Would also feed the PSV steam mode |
| Tank volume / strapping (vertical & horizontal, heads) | Med | M | Client-side |
| NPSH / pump hydraulics screening | Med | M | Client-side |
| Compressor power estimate (adiabatic/polytropic) | Med | M | Uses k and Z already available |
| Unit-aware clipboard (copy value + unit) | Low | L | Copy-button enhancement |
| Dark/light theme toggle | Low | M | App identity is dark; low priority |

### Explicitly out of scope

- **Flash / dew-point (VLE) calculation** — requires an equation of state plus stability analysis; the effort and validation burden are out of proportion for a reference tool, and wrong VLE answers are dangerous. Revisit only if the tool ever gains a rigorous property backend.
- **User accounts / cloud storage** — contradicts the zero-data-harvesting principle.

## 7. Release & QA Process

1. **Branch → PR → merge.** Work happens on a feature branch; a PR to `main` is reviewed by the maintainer. Merging to `main` deploys to production (Vercel) — merges are therefore a deliberate release act.
2. **Reference-value regression (mandatory before any release).** The reference vectors in CLAUDE.md and SPECIFICATION.md §9 must reproduce exactly — since v2.6, this means in **every enabled language** (currently English and Japanese; see SPECIFICATION.md §12), not English only:
   - JIS composition case (CH₄ 89 / C₂H₆ 7 / C₃H₈ 2.5 / iC₄ 0.7 / nC₄ 0.5 / N₂ 0.3): HHV 44.59, LHV 40.25, SG 0.634, WI 56.00, MW 18.305, Z 0.996759/0.9968, ρ_std 0.81930, 100 t/h → 122.056 kNm³/h, 100 kNm³/h → 81.930 t/h.
   - ΔP default case: ΔP_total ≈ 176.9 kPa (2.34 friction + 174.6 static), Re ≈ 2.20×10⁵, f ≈ 0.0184, V_e ≈ 7.72 m/s (C=100).
   - Flow Regime default case: Churn/Slug Flow, θ = +45.0°, vertical map.
3. **Documentation sync.** Any change to a feature, constant, or calculation updates, in the same PR: the How To Use tab, the Theory tab, `docs/SPECIFICATION.md` (affected section), and the roadmap status in this document.
4. **Feature-preservation sweep.** Before merging: all 9 tabs render, all toggles work, copy buttons work, custom modules persist, the 3D animation loads, all three API cards respond, export/share/restore round-trip, and (since v2.6) the language switcher works in both directions with no console errors on any tab.
5. **Versioning.** `feat:`/`fix:`/`docs:`/`chore:` commit types; releases tagged `vX.Y` on the post-merge `main` HEAD (hotfixes `vX.Y.Z`). Version strings updated together in `index.html` (footer, report header, report env), **every enabled language's `i18n/*.json`** (`meta.pageTitle` + `footer.copyright`), `README.md`, `CLAUDE.md`, and the `docs/*.md` version headers. See CLAUDE.md's "Version-bump checklist" for the full, mandatory list — this bullet is the summary, that one is the source of truth.

## 8. Risks & Constraints

| Risk | Mitigation |
|---|---|
| Single 3,400-line HTML file keeps growing | Accepted trade-off for the no-build principle; SPECIFICATION.md maps the file so contributors can navigate it |
| CDN dependencies (Tailwind, Three.js) unavailable | 3D animation already degrades gracefully; core math is CDN-independent; consider self-hosting pinned copies in a future release |
| Vercel serverless cold starts (notably flowregime's matplotlib import) | Frontend shows contextual "API Connection Failed" badges; acceptable for a free reference tool |
| Solo maintainer (bus factor 1) | This `docs/` folder + CLAUDE.md preservation rules exist precisely to make the project transferable |
| Regulatory values drift (standard revisions) | Standards editions are pinned and cited in the Theory tab and SPECIFICATION.md; any edition change is a major, deliberate update |
