# CLAUDE.md — O&G Engineering Converter

Project memory for Claude Code. Read and follow all rules below in every session.

## Project Overview

- **App**: O&G Engineering Converter v2.7 — a control-room-ready unit conversion and engineering calculation suite for the Oil & Gas / LNG sector.
  - Default UI language is English; as of v2.7 all 10 menu languages (en, ja, zh, ko, th, id, ru, es, fr, de) are fully live — working tool AND the four documentation tabs. See "Internationalization (i18n)" below and `docs/SPECIFICATION.md` §12.
- **Developer**: Naoto Yamabe (petro.naoto@gmail.com)
- **Live deployment**: Vercel (auto-deploys from `main` branch on GitHub)
- **Architecture**: Hybrid Edge-Server
  - `index.html` — single-file frontend: vanilla JavaScript + Tailwind CSS via CDN. No build step. All standard conversions and JIS K 2301 compositional calculations run client-side.
  - `api/` — three Vercel serverless Python endpoints: `dp_calculator.py` (pipe ΔP, Darcy-Weisbach + Colebrook-White + HEM two-phase + RP 14E erosion check), `psv_calculator.py` (API 520 Part I PRV sizing), `flowregime.py` (two-phase flow regime map PNG). **Detailed API rules — endpoint specs, dependency constraints, the multiply-to-SI unit-factor convention, and the dp/flowregime reference cases — live in [`api/CLAUDE.md`](api/CLAUDE.md); read it before touching anything in `api/`.**
  - `requirements.txt` — Python deps for flowregime.py only (numpy/matplotlib/seaborn).
  - `i18n/*.json` — translation dictionaries, 10 files as of v2.7 (`en`, `ja`, `zh`, `ko`, `th`, `id`, `ru`, `es`, `fr`, `de`). `en.json` is the canonical source and runtime fallback for any working-tool key missing elsewhere; for `docs.*` keys the fallback is the inline English HTML in `index.html` (cached at runtime by `applyTranslations()` — English doc content is deliberately NOT duplicated into `en.json`). Fetched lazily by `index.html`, not bundled — the no-build-step principle holds.
  - `README.md` — project documentation.
  - `docs/` (v2.7) — `DEVELOPMENT_PLAN.md` (history + roadmap, incl. the i18n program milestones), `SPECIFICATION.md` (full feature & API spec, known-issues register, §12 i18n architecture), `MARKETING.md` (promotion strategy).

## CRITICAL Preservation Rules

1. **NEVER simplify, refactor, remove, or rename any existing feature, function, element ID, or constant unless explicitly instructed.** Silent feature loss is the most serious failure mode in this project.
2. **Make surgical, minimal diffs.** Do not regenerate whole files or whole sections to apply a small change.
3. **Do not "improve" working code** (formatting, style, modernization) unless asked.
4. **Element IDs are an API.** JavaScript references HTML IDs extensively (`out-ghv`, `flow-mass-in-u`, `psv-*`, `dp-*`, etc.). Never change an ID without updating every reference, and only when instructed.
5. **Before committing, verify no feature was dropped**: tabs (General / Basic Eng / Advanced / Safety / How To Use / Theory / Terms / Privacy / Report), custom modules, copy buttons, all toggles (Abs/Gauge, HHV/LHV, VOL/MOL, MASS/MOL), the Flow Regime card (map image + Three.js 3D animation), and all three serverless API integrations must all still exist. v2.4 additions that must also survive: the three Basic Eng converter cards (Petroleum Gravity `api-*`, Viscosity `visc-*`, Mass↔Vol Flow `mf-*`), the ΔP card's Erosion C-factor input (`dp-cfactor`) and second output row (`dp-out-re/-f/-ve/-eratio/-ero-badge` + `dp-out-regime-note`), the out-of-range warnings (`z-warn`, `out-liq-warn`, `comp-warn`), and the floating action bar (Export PDF `exportReport()`, Share `copyShareLink()`, plus `STATE_KEY` persistence/restore). v2.5 additions that must also survive: the How To Use / Theory jump-link strips and section anchors (`howto-new25`, `howto-new`, `howto-1`…`howto-12`, `theory-p1`…`theory-p6`), the back-to-top button (`back-to-top` + scroll listener), the runtime ARIA tablist semantics (`enhanceAccessibility()` + `aria-selected` in `switchTab()`), Enter-to-calculate on `dp-*`/`psv-*` inputs, the client-side validation pre-checks in `calcDeltaPressure()`/`calcPSV()`, the stale-input indicator (`dpResultFresh`/`psvResultFresh`/`markResultStale()`), the export pop-up Blob-download fallback, and the distinct viscosity option values (`0.0010` mPa·s / `0.0000010` mm²/s — string-distinct from cP/cSt, numerically identical). v2.6 additions that must also survive: the i18n engine (`LANGUAGES` config, `loadLanguage()`, `tr()`, `applyTranslations()`, `setLanguage()`, `applyAwaitingBadgeDefaults()`) and the header switcher (EN/日本語 toggle + settings-menu dropdown) — do not rename `tr()` to `t()` or reuse `t` as a local variable name in any function that calls it (it already collides with locals in `exportReport()` and formerly in `calcZFactor()`, renamed to `trr`); every `data-i18n`/`data-i18n-title`/`data-i18n-aria`/`data-i18n-placeholder` attribute in `index.html` must have a matching key in `i18n/en.json` **and every other enabled language's dictionary**; `localStorage['og_lang']` and the `lang` field in `collectState()`/share-link state; the idempotent (unconditional) aria-label setters in `enhanceAccessibility()` — do not reintroduce the old `if (!b.getAttribute('aria-label'))` guard, it silently freezes translations after the first language switch. v2.7 additions that must also survive: the `data-i18n-html` doc-translation mechanism (`i18nHtmlOriginals` cache + the `[data-i18n-html]` loop in `applyTranslations()`) and all 125 `docs.*` block keys across the How To Use / Theory / Terms / Privacy tabs — every `data-i18n-html` attribute must have a matching `docs.*` key in all 9 non-English dictionaries (English lives inline in the HTML, not in `en.json`); all 10 `i18n/*.json` files and all 10 `enabled: true` rows in `LANGUAGES`; the governing-language notes (`docs.terms.langNote`, `docs.privacy.langNote`).

## UI Consistency Rules

The **Pipe Volume Calculator** card in the Basic Eng tab is the canonical reference for converter-card layout. Every conversion card (in any tab) MUST follow its philosophy:

1. **Figure and unit are SEPARATE adjacent boxes**, never a single shared container. The numeric figure sits in its own box (`rounded-l-lg`, holding the input + any copy button); the unit sits in its own box (`rounded-r-lg`) as a sibling in a `flex` row.
2. **They highlight in orange independently.** The figure box uses `focus-within:ring-2 focus-within:ring-amber-500`; the unit `<select>` uses `focus:ring-2 focus:ring-amber-500`. Never wrap both in one `focus-within`/`unit-field` container that lights up the figure and the unit together.
3. **Selectable units** are a native `<select>` styled `bg-slate-800 border-y border-r border-slate-700 rounded-r-lg text-amber-500` and MUST keep the browser's native dropdown arrow — do NOT use `appearance-none` or a custom chevron.
4. **Fixed (non-selectable) units** use a matching static `bg-slate-800 … rounded-r-lg` chip with no arrow, so the layout stays consistent while signalling that the unit is not editable.

This applies to the General tab (Gas Volume, Pressure, Temperature, Heating Value) and any future converter cards; keep them visually identical in philosophy to the Basic Eng Pipe Volume card.

## Calculation Rules (JIS K 2301:2011) — DO NOT ALTER

These rounding rules are mandated to match the Excel reference worksheet exactly. Any change breaks regulatory traceability.

- Vol→Mol: `Cmᵢ = ROUND( (Cvᵢ/Zᵢ) / Σ(Cv/Z), 4 )` — mole fractions rounded to **4 d.p.**
- Per-component `Cmᵢ×√bᵢ` rounded to **5 d.p.** before summing.
- `Z_exact = 1 − (ΣCm√b)²` — used for HHV, LHV, SG.
- `Z_rounded = ROUND(Z_exact, 4)` — used ONLY for ρ_std (flow density).
- HHV/LHV = `ROUND( Σ(Cmᵢ×Hᵢ) / Z_exact, 2 )` — no per-component rounding of products.
- SG = `ROUND( Σ(Cmᵢ×Sᵢ) / Z_exact, 3 )`.
- WI = `ROUND( HHV_2dp / √(SG_3dp), 2 )` — uses the **already-rounded** HHV and SG. WI is always HHV-based per JIS K 2301 §7, regardless of HHV/LHV toggle state.
- ρ_std = `101325 × (MW/1000) / (Z_rounded × 8.31446262 × 273.15)` [kg/Nm³].
- R = 8.31446262 J/(mol·K); T_std = 273.15 K; P_std = 101325 Pa; Nm³↔scf factor = 37.3258.
- LHV component values are from JIS K 2301:2011 Table 30, anchored on CH₄ = 35.818 MJ/Nm³ (implied ΔHvap(H₂O) = 2.011 MJ/Nm³ per mol H₂O at 0°C). Do not recompute or "correct" them.
- LNG liquid density: ISO 6578:1991 Klosek-McKinley, Tables B.2 (molar volumes, linear T interpolation) and C (k₁/k₂, linear MW interpolation).

## Reference Test Values — MUST REPRODUCE EXACTLY

Composition: CH₄=89, C₂H₆=7, C₃H₈=2.5, iC₄=0.7, nC₄=0.5, N₂=0.3 (vol%):

| Quantity | Expected |
|---|---|
| Mole fractions (4 d.p.) | CH₄ 0.8887, C₂ 0.0704, C₃ 0.0254, iC₄ 0.0073, nC₄ 0.0052, N₂ 0.0030 |
| Z_exact / Z_rounded | 0.996759 / 0.9968 |
| HHV | 44.59 MJ/Nm³ |
| LHV | 40.25 MJ/Nm³ |
| SG | 0.634 |
| WI | 56.00 |
| MW | 18.305 g/mol |
| ρ_std | 0.81930 kg/Nm³ |
| 100 ton/h → | 122.056 kNm³/h |
| 100 kNm³/h → | 81.930 ton/h |

After ANY change touching `calcGHV()`, `gasComps`, or related logic, re-verify these values (a quick Python check is acceptable) before committing.

## Documentation Sync Rule

`index.html` contains embedded documentation (How To Use tab, Theory tab). Whenever a feature, constant, or calculation changes, check and update:
- Theory tab: Table 1.1 constants, §1.3–§1.7 worked examples, Part II–VI.
- How To Use tab: section descriptions and reference-value callout boxes.
- `docs/SPECIFICATION.md` (v2.7): the affected module/API section and, if applicable, the Known Issues register.
- `docs/DEVELOPMENT_PLAN.md` (v2.7): roadmap item status when a roadmap feature ships.
- **(v2.7+) all 10 `i18n/*.json` files:** any new or changed user-visible working-tool string needs a matching key added/updated in **every** dictionary in the same commit. Any edit to the How To Use / Theory / Terms / Privacy inline English HTML must be mirrored into the corresponding `docs.*` key in **all 9 non-English dictionaries** (English doc content lives only inline in `index.html`). Missing keys silently fall back to English at runtime rather than erroring, so stale translations are easy to miss; check deliberately.
Numbers in worked examples must match actual calculator output exactly.

## Git Workflow

Always follow this exact sequence:

```bash
git pull origin main
git add <changed files>
git commit -m "<type>: v<version> — <description>"
git push origin main
```

- Commit message types: `feat:`, `fix:`, `docs:`, `chore:`.
- Tag releases: `git tag -a vX.Y -m "..."` then `git push origin vX.Y`. Hotfixes use vX.Y.Z. Tag the actual commit on `main` **after** it lands there — if the change went through a PR, the merged SHA on `main` is very often *not* the same SHA as the feature branch's tip (squash or merge commits both create a new SHA), so tag `origin/main`'s HEAD post-merge, not your local branch.
- Never force-push to `main`. Never commit without showing the diff first.
- Pushing to `main` triggers a live Vercel deployment — confirm with Naoto before pushing anything non-trivial.

### Version-bump checklist — every location, every time

A version number change is **not done** until every one of these is updated together, in the same change. This list exists because v2.6 shipped without it and left the app displaying "Version 2.5" in three places for a full release cycle — treat every entry below as mandatory, not best-effort:

- [ ] `index.html` `<title>` (`meta.pageTitle` key — see below, not the literal HTML text, though update that fallback text too)
- [ ] `index.html` footer copyright line (`footer.copyright` key)
- [ ] `index.html` `exportReport()` — the `{version: '…'}` argument passed to `tr('js.export.versionGenerated', …)`
- [ ] `i18n/*.json` `report.mailtoBody` key — embeds `Env: Browser/Client-Side VX.Y` in the bug-report email body
- [ ] `index.html` How To Use tab heading ("Operations Manual vX.Y") and Theory tab intro paragraph ("…implemented in vX.Y") — update these two, **and (v2.7+) their translated copies in the `docs.howto.b001` / `docs.theory.b001` keys of all 9 non-English dictionaries**; do **not** touch historical `★ New in Version X.Y` changelog headings or `// vX.Y — …` code comments, which correctly describe *when that specific thing was added*, not the current version
- [ ] **`i18n/en.json` and every other enabled language's dictionary** (currently `i18n/ja.json`; will include more files as more languages ship) — both the `meta.pageTitle` and `footer.copyright` keys, in **every** file. This is the location most likely to be missed, since it's data, not markup.
- [ ] `README.md` — the `# … — vX.Y` title line, plus the docs-table row that names the current proposed-roadmap version (keep it in sync with whatever DEVELOPMENT_PLAN.md's roadmap section is currently called — version-bucket names get renumbered when a shipped release takes a number a roadmap proposal was already using, as happened between v2.6 and the "v2.7" pack)
- [ ] `CLAUDE.md` — the `App:` line at the top, and the `docs/ (vX.Y)` reference just below it
- [ ] `docs/DEVELOPMENT_PLAN.md`, `docs/SPECIFICATION.md`, `docs/MARKETING.md` — each file's own `**Document version:** X.Y (accompanies/describes app vX.Y)` header line, plus a new Version History row in DEVELOPMENT_PLAN.md §4
- [ ] Git tag on the post-merge `main` HEAD (see above)

Grep for the outgoing version number across the whole repo (`grep -rn "v2\.5\|V2\.5" .` style, adjusted per bump) before considering a version change finished — treat any hit outside a historical changelog/comment as a miss.

## Local Development & Testing

- `vercel dev` is required to test the two Python API endpoints locally (opening index.html directly breaks the Advanced ΔP and Safety PSV calculators).
- API-side rules — stdlib-only dependency constraints, curl test procedure, the multiply-to-SI unit-factor convention, and the mandatory dp_calculator / Flow Regime reference cases — are maintained in [`api/CLAUDE.md`](api/CLAUDE.md). Re-verify those reference cases after touching any file in `api/`.

## Engineering Standards References

- JIS K 2301:2011 — calorific value, density, SG, Wobbe index from composition.
- ISO 6578:1991 — LNG density (Klosek-McKinley).
- API Standard 520 Part I, 9th Ed. (2014) — PRV sizing; API 526 orifice areas D–T.
- API RP 14E (5th Ed., 1991) — erosional-velocity screening criterion V_e = C/√ρ (ΔP card, v2.4).
- Papay (1968) with Standing-Katz pseudo-criticals — gas Z-factor (Basic Eng); validity 0 < Pr ≤ 15, 1.05 ≤ Tr ≤ 3.0.
- CODATA 2018 — gas constant.
- Colebrook & White (1939) — friction factor.

## Communication Preferences

- Explain proposed changes as targeted diffs before applying.
- When uncertain whether something is a feature or a bug, ASK — do not assume.
- Responses about engineering values should show the verification calculation.
