# CLAUDE.md — O&G Engineering Converter

Project memory for Claude Code. Read and follow all rules below in every session.

## Project Overview

- **App**: O&G Engineering Converter v3.6 — a control-room-ready unit conversion and engineering calculation suite for the Oil & Gas / LNG sector.
- **Licence**: **MIT** (`LICENSE`, added 2026-08-16). The repo was previously public but unlicensed, and the in-app Terms §6 actively *prohibited* redistribution and commercial use — those two facts contradicted each other. Three things must now stay in agreement, and a change to any one of them is a change to all three: the `LICENSE` file, the README licence section, and **in-app Terms §6 (`docs.terms.b008`) in the inline English AND all 9 dictionaries**. The licence covers this project's own code only — the `LICENSE` file's third-party section (engineering standards, GIIGNL LNG data, vendor GT specs) is load-bearing and must not be dropped.
  - Default UI language is English; as of v2.7 all 10 menu languages (en, ja, zh, ko, th, id, ru, es, fr, de) are fully live — working tool AND the four documentation tabs. See "Internationalization (i18n)" below and `docs/SPECIFICATION.md` §12.
- **Developer**: Naoto Yamabe (petro.naoto@gmail.com)
- **Live deployment**: Vercel (auto-deploys from `main` branch on GitHub)
- **Architecture**: Hybrid Edge-Server
  - `index.html` — single-file frontend: vanilla JavaScript + Tailwind CSS via CDN. No build step. All standard conversions and JIS K 2301 compositional calculations run client-side.
  - `api/` — three Vercel serverless Python endpoints: `dp_calculator.py` (pipe ΔP, Darcy-Weisbach + Colebrook-White + HEM two-phase + RP 14E erosion check), `psv_calculator.py` (API 520 Part I PRV sizing), `flowregime.py` (two-phase flow regime map PNG). **Detailed API rules — endpoint specs, dependency constraints, the multiply-to-SI unit-factor convention, and the dp/flowregime reference cases — live in [`api/CLAUDE.md`](api/CLAUDE.md); read it before touching anything in `api/`.**
  - `requirements.txt` — Python deps for flowregime.py only (numpy/matplotlib/seaborn).
  - `i18n/*.json` — translation dictionaries, 10 files as of v2.7 (`en`, `ja`, `zh`, `ko`, `th`, `id`, `ru`, `es`, `fr`, `de`). `en.json` is the canonical source and runtime fallback for any working-tool key missing elsewhere; for `docs.*` keys the fallback is the inline English HTML in `index.html` (cached at runtime by `applyTranslations()` — English doc content is deliberately NOT duplicated into `en.json`). Fetched lazily by `index.html`, not bundled — the no-build-step principle holds.
  - `README.md` — project documentation.
  - `docs/` (v3.6) — `DEVELOPMENT_PLAN.md` (history + roadmap, incl. the i18n program milestones), `SPECIFICATION.md` (full feature & API spec, known-issues register, §12 i18n architecture), `MARKETING.md` (promotion strategy), `POST.md` (the live LinkedIn campaign log — see below).

## Public URL — one domain only

**The app is `https://engineering-converter.com`.** It must appear **in the body** of every
campaign post, not only in a first comment.

The `unit-converter-oil-gas.vercel.app` address is the underlying Vercel deployment and is **not**
the public identity. Never put it in copy, a share link, a graphic, or `index.html` head metadata —
`og:url`, `og:image`, `twitter:image` and `rel=canonical` are all pinned to the real domain, and a
canonical pointing at the Vercel host tells search engines the wrong site is authoritative.

## LinkedIn campaign

A 20-day daily campaign runs from [`docs/POST.md`](docs/POST.md) — schedule, per-day sheets
(hook, angle, mockup spec, verified numbers, CTA, EN + JA copy), the verified reference-value
table, a corrections register, and the tracker where each post URL is recorded once live.
Assets are in `docs/linkedin/`.

**To prepare or publish a day, use the [`linkedin-daily-post`](.claude/skills/linkedin-daily-post/SKILL.md)
skill.** It carries the procedure and the hard-won traps — how to hand-author a compact share link
(the app's own Share output is ~4,600 characters and does not fit a LinkedIn comment), how to
generate the annotated graphic from the *real* app rather than re-implementing the UI, how to
capture it as a PNG (headless Chrome `--screenshot` — the in-app browser pane never composites,
`PrintWindow` returns a blank surface on Chrome 151, and full-screen capture would expose unrelated
private windows), and how to attach it (the OS clipboard is the only route that works).

Two link rules the campaign depends on: a posted share link must use **`?s=`**, because LinkedIn
strips everything after the `#` when it auto-links a URL — and the app's own Share button must
keep emitting `#s=`, because a fragment never reaches the server while a query string lands in
access logs. See `docs/SPECIFICATION.md` §6.

Two rules that outrank convenience:

- **Every figure in a post must be reproduced against the running app before it is written**, never
  copied from the docs. An adversarial review of the original plan found ten defects, including a
  wrong headline number.
- **Look at the rendered graphic before publishing.** Programmatic checks have passed on an image
  that was visibly broken; they are not verification.

## CRITICAL Preservation Rules

1. **NEVER simplify, refactor, remove, or rename any existing feature, function, element ID, or constant unless explicitly instructed.** Silent feature loss is the most serious failure mode in this project.
2. **Make surgical, minimal diffs.** Do not regenerate whole files or whole sections to apply a small change.
3. **Do not "improve" working code** (formatting, style, modernization) unless asked.
4. **Element IDs are an API.** JavaScript references HTML IDs extensively (`out-ghv`, `flow-mass-in-u`, `psv-*`, `dp-*`, etc.). Never change an ID without updating every reference, and only when instructed.
5. **Before committing, verify no feature was dropped**: tabs (General / Basic Eng / Advanced / Safety / How To Use / Theory / Terms / Privacy / Report), custom modules, copy buttons, all toggles (Abs/Gauge, HHV/LHV, VOL/MOL, MASS/MOL), the Flow Regime card (map image + Three.js 3D animation), and all three serverless API integrations must all still exist. v2.4 additions that must also survive: the three Basic Eng converter cards (Petroleum Gravity `api-*`, Viscosity `visc-*`, Mass↔Vol Flow `mf-*`), the ΔP card's Erosion C-factor input (`dp-cfactor`) and second output row (`dp-out-re/-f/-ve/-eratio/-ero-badge` + `dp-out-regime-note`), the out-of-range warnings (`z-warn`, `out-liq-warn`, `comp-warn`), and the floating action bar (Export PDF `exportReport()`, Share `copyShareLink()`, plus `STATE_KEY` persistence/restore). v2.5 additions that must also survive: the How To Use / Theory jump-link strips and section anchors (`howto-new25`, `howto-new`, `howto-1`…`howto-12`, `theory-p1`…`theory-p6`), the back-to-top button (`back-to-top` + scroll listener), the runtime ARIA tablist semantics (`enhanceAccessibility()` + `aria-selected` in `switchTab()`), Enter-to-calculate on `dp-*`/`psv-*` inputs, the client-side validation pre-checks in `calcDeltaPressure()`/`calcPSV()`, the stale-input indicator (`dpResultFresh`/`psvResultFresh`/`markResultStale()`), the export pop-up Blob-download fallback, and the distinct viscosity option values (`0.0010` mPa·s / `0.0000010` mm²/s — string-distinct from cP/cSt, numerically identical). v2.6 additions that must also survive: the i18n engine (`LANGUAGES` config, `loadLanguage()`, `tr()`, `applyTranslations()`, `setLanguage()`, `applyAwaitingBadgeDefaults()`) and the header switcher (EN/日本語 toggle + settings-menu dropdown) — do not rename `tr()` to `t()` or reuse `t` as a local variable name in any function that calls it (it already collides with locals in `exportReport()` and formerly in `calcZFactor()`, renamed to `trr`); every `data-i18n`/`data-i18n-title`/`data-i18n-aria`/`data-i18n-placeholder` attribute in `index.html` must have a matching key in `i18n/en.json` **and every other enabled language's dictionary**; `localStorage['og_lang']` and the `lang` field in `collectState()`/share-link state; the idempotent (unconditional) aria-label setters in `enhanceAccessibility()` — do not reintroduce the old `if (!b.getAttribute('aria-label'))` guard, it silently freezes translations after the first language switch. v2.7 additions that must also survive: the `data-i18n-html` doc-translation mechanism (`i18nHtmlOriginals` cache + the `[data-i18n-html]` loop in `applyTranslations()`) and all 155 `docs.*` block keys across the How To Use / Theory / Terms / Privacy tabs (125 from v2.7 + the 14 v2.8 blocks translated in v2.8.1 + the 16 v3.0 blocks, `docs.howto.b077`–`b086` and `docs.theory.b040`–`b045`) — every `data-i18n-html` attribute must have a matching `docs.*` key in all 9 non-English dictionaries (English lives inline in the HTML, not in `en.json`); all 10 `i18n/*.json` files and all 10 `enabled: true` rows in `LANGUAGES`; the governing-language notes (`docs.terms.langNote`, `docs.privacy.langNote`). **v2.8 additions that must also survive:** the Basic Eng **Gas Property Estimator** (`gp-sg`, `gp-p`/`-u`, `gp-t`/`-u`, `gp-k`, `gp-warn`, `gp-out-z`, `gp-out-mu`/`-u`, `gp-out-c`/`-u`, `gp-out-jt`/`-u`) and the shared real-gas helpers `papayZ()`/`toPsia()`/`toRankine()` that `calcZFactor()` and `calcGasProps()` BOTH route through — never let either card recompute Papay inline again, that duplication is exactly what v2.8 removed; the **Crane fittings** block (`craneFT()`, `updateFittingSum()`, `dp-fit-details` + the twelve `dp-fit-*` count inputs + `dp-fit-ksum`/`-nominal`/`-ft`) and its `k_total` payload key, whose **default of 0 is load-bearing** — it is what keeps every pre-v2.8 share link reproducing Vector 2; the **NORSOK line-sizing screen** (`renderLineSizing()`, `lastDpResult`, `dp-service`, `dp-out-dpfit`/`-leq`/`-dpfric100`/`-vmax`/`-vratio`/`-sizing-badge`) which judges `dpFric` only, never the displayed ΔP/length; `phase_key`/`re_regime_key` from dp_calculator and the `RE_REGIME_I18N` map — do NOT reintroduce branching on the English badge text; the **mobile navigation** (`buildMobileNav()`, `toggleMobileNav()`, `mobile-nav-wrap`/`-btn`/`-menu`/`-current`, and the `hidden md:flex` on the tab `<nav>`); **share-state v:2** (`escModText()`, `sanitizeSharedModule()`, `importSharedModules()`, `MOD_MAX_SHARED`/`MOD_MAX_TEXT_LEN`, `SHARE_URL_WARN_LEN`, the `report-*` exclusion in `collectInputs()`, the guarded `savedModules` parse, and the decodeShareState → importSharedModules → applyState boot order) — **every externally-supplied module MUST pass through `sanitizeSharedModule()`**, because `createCard()` interpolates module text into `innerHTML` and the id into inline `onclick` attributes; and the doc anchors `howto-new28`, `howto-13`…`howto-15`, `theory-p7`. **v3.0 additions that must also survive:** the **Steam Properties card** (`sp-*`) and the IF97 engine — all 259 coefficients live in ONE `const IF97 = JSON.parse(\`…\`)` literal that `tests/test_steam_if97.py` extracts verbatim and re-verifies against the Release's own tables; never convert it to a plain object literal; the **PSV steam advisory** (`psv-T-steam` + `psv-steam-advisory`, advisory-only — an occurrence-count test pins it out of the payload); the **NPSHa card** (`npsh-*`, `calcNPSH()`, `fillNPSHWater()` with its load-bearing `toPrecision(8)` field quantization — Vector 9 is defined through it — and `const NPSH_G = 9.80665;`); its deliberate NO-margin-verdict stance; the **compressor card** (`cmp-*`, `calcCompressor()`) which must keep routing BOTH Z evaluations through the shared `papayZ()` (a `count == 2` test pins it) and never cites ASME PTC 10; the **unit-aware clipboard** (`copyUnitOf()`, the capture-phase `_copyModClick` listener, the delegated long-press with `_lpUnit`/`_lpDone`, `data-unit-src`/`data-copy-unit` attributes) — plain click MUST stay the bare value, and in `createCard()` only the sanitized `m.id` may enter attribute context (unit text stays in element text; a template-scanning test enforces this); the **Basic Eng quick-links strip** (`basic.nav.*` keys, card anchors `basic-pipe`…`basic-cmp` with their `scroll-mt-64 md:scroll-mt-40` clearance); and the doc anchors `howto-new30`, `howto-16`…`howto-19`, `theory-p8`…`theory-p10`. **v3.2 additions that must also survive:** the **Vercel Web Analytics** block — the two `<head>` tags (the `window.va` queue stub, which MUST stay ahead of `<script defer src="/_vercel/insights/script.js">`) and the instrumentation block at the end of the `<script>` (`VA_TOOL_BY_ID_PREFIX`, `vaArmed`, `vaSeenTools`, `trackEvent()`, `vaWrap()`). It is **purely additive by design** — it wraps globals and delegates off `e.target.id` rather than editing any calc function, precisely so it can never cause silent feature loss; keep it that way, and add one map line per new card rather than instrumenting the card itself. Three invariants are load-bearing and are pinned by `tests/test_analytics_privacy.py`: (a) **`report` must never enter `VA_TOOL_BY_ID_PREFIX`** and the block must never read `.value`/`.innerText` — analytics records *that* a tool was used, never *what* was entered; (b) `vaArmed` must stay `false` until the first `pointerdown`/`keydown`, or `recomputeAll()` at boot reports a `localStorage` restore as user activity; (c) `Tool Used` must stay de-duplicated through `vaSeenTools` — the live converters fire on every keystroke. Any change to what is measured must update Privacy Policy §2/§5/§7/§9 **in the same commit**, in the inline English AND all 9 dictionaries (MARKETING.md §5 release rule). **v3.1 additions that must also survive:** the **GT Fuel** section (v3.6: the third Advanced sub-pane `adv-sub-gtfuel` + strip button `advbtn-gtfuel`; `switchTab('gtfuel')` MUST keep mapping onto `switchAdvSub('gtfuel', true)` — pre-v3.6 share links depend on it; `nav.gtfuel` in all 10 dictionaries) with its three panels `gt-select`/`gt-est`/`gt-cat` and every `gt-*` element id (selection `gt-vendor`/`gt-model`/`gt-cycle` + spec chips `gt-spec-*`; estimator `gt-power`/`-u`, `gt-eff`, `gt-hv`/`-u`, `gt-hv-basis`, `gt-hhv-ratio` + `gt-ratio-wrap`, `gt-rho`, `gt-avail`, `gt-import`, `gt-send-mf`, `gt-warn`; outputs `gt-out-q`/`-hr`/`-hr-btu`/`-vol`/`-u`/`-mass`/`-u`, totals `gt-tot-{h,d,m,y}-{vol,mass,e}`; catalogue `gt-cat-grid` + `gt-filt-*` pills); the **GT_MODELS dataset** — all 31 entries live in ONE `const GT_MODELS = JSON.parse(\`…\`)` literal that `tests/test_gt_fuel.py` extracts verbatim (never convert to a plain object literal, never drop an entry's `src` citation, and keep `|hrKJ − 3600/η| ≤ 30 kJ/kWh` when editing specs); the **static `<optgroup>` model option list** — options are hidden/disabled by `gtFilterModelOptions()`, NEVER rebuilt (share-link restore sets `gt-model` before any event fires); the named consts `GT_HV_FACTOR = 0.001055056 * 37.3258` (derived product, mirrors `HV_FACTOR`), `GT_H_YEAR = 8760`, `GT_H_MONTH = 730`; the `lastGHV` bridge assigned inside `calcGHV()` and read by `importGHVToGT()`; `sendGTToMassVol()` targeting `mf-mass`/`mf-rho` + `calcMassVol('mass')`; `calcGTFuel` in `recomputeAll()` AND in the no-stored-state boot branch; the three original SVG `<symbol>` thumbnails `gt-svg-hd/ad/ind` (original art — vendor photos are copyrighted and must never be embedded); the catalogue's `tr()`-based render with the language-sentinel re-render (`gtRenderCatalogueIfStale()`); the totals convention (hourly row = instantaneous, daily/monthly/yearly × availability); the GT export-report section (`js.export.section6Title` + `js.export.gt*` keys ×10); the `gtfuel.*` namespace (56 keys) in all 10 dictionaries; and the doc anchors `howto-new31`, `howto-20`, `theory-p11` with `docs.howto.b087`–`b090` and `docs.theory.b046`–`b047` in all 9 non-English dictionaries. **v3.3 additions that must also survive:** the **LNG reference-composition selector** on the Advanced GHV card — `comp-preset` and its STATIC `<option>` list (never rebuild it; a share-link restore sets the value before any event fires, the same rule as the v3.1 GT model list), `comp-preset-wrap`/`-badge`/`-check` and the three citation spans `comp-preset-src-prefix`/`-warn`/`-text`; the **`LNG_PRESETS` dataset** — all 9 entries in ONE `const LNG_PRESETS = JSON.parse(\`…\`)` literal that `tests/test_lng_presets.py` extracts verbatim (never convert it to a plain object literal, never drop an entry's `src`), plus `LNG_PRESET_TOL = 0.05`; the **three-tier honesty boundary** (`pub`/`ref` carry the source's own `gcv`/`wi`, `asm` must carry `null` for both — a cross-check against an invented number would dress a guess as a citation, and a test pins it); the per-entry `basis` field, which drives `ghv-mode` on load — GIIGNL Table 1 is **mole %** and reading it as volume % puts every row ~0.06 MJ/Nm³ above its published GCV; `lastCompCheck` assigned from **`hhv_mix`, never `hv_mix`** (GCV is the gross value and must not follow the HHV/LHV display toggle — pinned by a test); `renderLNGPresetInfo()` called from inside `calcGHV()` (not only from `applyLNGPreset()`, or a restored share link shows a preset name with no citation) and kept free of `innerHTML`; the delegated `input` listener that drops the selector to Custom on any manual `comp-*` edit; the `data-i18n-label` mechanism in `applyTranslations()` for `<optgroup>` labels (plain `data-i18n` sets textContent, which would delete an optgroup's children) and its matching branch in `test_i18n_parity.py`'s `ATTR_PATTERN`; the `advanced.ghv.preset.*` namespace (19 keys) in all 10 dictionaries; and the doc anchors `howto-21`, `theory-p12` with `docs.howto.b092`–`b093` and `docs.theory.b048`–`b049` in all 9 non-English dictionaries. **Share-link decode (2026-08-16):** `decodeShareState()` reads the payload from the fragment **and** the query string, fragment first, through `normalizeShareB64()` (which undoes percent-encoding, `+`→space and base64url). **`copyShareLink()` must keep emitting `#s=` and must never emit `?s=`** — a fragment never reaches the server, a query string lands in access logs, and generating one would put user inputs into Vercel's logs against the Privacy Policy and the v3.2 analytics boundary. `tests/test_share_state.py` fails if this is flipped. The `?s=` read path exists because LinkedIn strips everything after the `#` when it auto-links a URL. The C4-split sensitivity figure (**≤ 0.03 MJ/Nm³**) is quoted in the on-screen citations, the Theory tab and `C4_SPLIT_MAX_SPREAD` — a test asserts the citation and the enforced number are the same number, so re-measure before tightening the claim. **v3.5 additions that must also survive:** the **LNG Cargo Estimator** card (`adv-lng-cargo`, id prefix `lc-` → analytics slug `lng-cargo`): `lc-vessel` and its STATIC 36-option list (never rebuild — filters `lcFilterVesselOptions()` only hide/disable; share-restore rule), `lc-cap`/`-fill`/`-heel`/`-bor`/`-days`, outputs `lc-out-vliq`/`-mass`/`-gas`/`-e`/`-el` with unit selects `lc-out-mass-u`/`-gas-u`/`-e-u` and the delivered spans `lc-out-*-d`/`-dv`, chips `lc-out-dens`/`-exp`, cross-link `lc-out-gt`, filter pills `lc-filt-t-*`/`lc-filt-c-*`, the vessel panel ids `lc-thumb-*`/`lc-spec-*`/`lc-src`/`lc-credit`/`lc-link-mt`/`lc-link-vf`, catalogue `lc-cat`/`lc-cat-grid`/`lc-cat-count`, and the four original schematics `lc-svg-{membrane,moss,ssp,typec}`; the **`LNG_VESSELS` dataset** — 36 entries in ONE `const LNG_VESSELS = JSON.parse(\`…\`)` literal that `tests/test_lng_cargo.py` extracts verbatim; **every entry must keep its own public `src`/`srcUrl`** (an owner/builder/class-society page or Wikipedia — NEVER an AIS/spotter site, NEVER the IGU report: its Appendix 3 is all-rights-reserved Rystad data and is deliberately not reproduced; the report is cited for fleet context only); `photo`/`credit`/`creditUrl` must agree with `assets/vessels/CREDITS.json` (Wikimedia Commons CC BY-SA / PD thumbnails only, ≤ 130 KB, credited on screen — no MarineTraffic/VesselFinder/ShipSpotting imagery ever, those are linked by IMO as plain hyperlinks); the **`lastLNGProps` bridge** assigned inside `calcGHV()` (kept SEPARATE from the test-pinned `lastGHV`) and `calcLNGCargo()` called at the end of `calcGHV()`, in `recomputeAll()` after `calcGTFuel`, and at the end of `calcGTFuel()` — the card owns no physics and must never touch `gasComps`/ISO 6578 itself; `lcRenderVessel()` stays textContent-only; the explicit `LC_TYPE_KEYS`/`LC_CONT_KEYS` maps (dead-key sweep); export §7 (`js.export.section7Title` + `lc*` keys); the `advanced.lngCargo.*` namespace (89 keys) in all 10 dictionaries. **GT Fuel v3.5:** the named constants `GJ_PER_MMBTU = 1.055056`, `MJ_PER_MWH = 3600`, `KG_PER_LB = 0.45359237`, `RHO_LBSCF_TO_KGNM3 = KG_PER_LB * 37.3258` (test-pinned literals); `gt-rho-u` (kg/Nm³ | lb/scf) — **lb/scf converts with 16.9307, never 16.0185** (standard vs actual volume; `gtLastResult.rho` stays kg/Nm³, `importGHVToGT()` converts back); `gt-out-q-u`, the extended `gt-out-vol-u`/`gt-out-mass-u` lists, the totals-header selects `gt-tot-vol-u`/`gt-tot-q-u`/`gt-tot-e-u` and the new `gt-tot-{h,d,m,y}-q` column (in `outIds`) — defaults must reproduce the Vector 11 strings byte-for-byte; clipboard census now 26 static / 6 literal. Docs: How To Use §16 (`howto-16`, `docs.howto.b102`–`b106`), the GT §21 addendum (`b107`), release entry `howto-new35` (`b108`/`b109`), Theory Part IX (`theory-p9`, `docs.theory.b050`/`b051`) and the Part XII addendum (`b052`) — the sections they displaced were renumbered to `howto-17`…`22` / `theory-p10`…`13` in all ten languages by script; do the same for the next insertion (rule 5 above), never append. **v3.6 additions that must also survive:** the **two-layer Advanced tab** — strip `adv-subnav` with `advbtn-gasq`/`-hyd`/`-gtfuel`, sub-panes `adv-sub-gasq`/`-hyd`/`-gtfuel`, `ADV_SUBS`/`ADV_SUB_KEYS`, `switchAdvSub(sub, quiet)`, `gotoAdvSub()`, `currentAdvSub`, the `advSub` field in `collectState()`/`applyState()` (restored on every visit, unlike `tab`), the indented sub-tab rows + "Advanced › ⟨sub⟩" trigger in `buildMobileNav()`, the sub-tab `tablist` semantics in `enhanceAccessibility()`, `vaWrap('switchAdvSub', …)` reusing the `Tab View` event, and the `nav.adv.*` keys (6) in all 10 dictionaries; the top bar has **9** tabs (`btn-gtfuel` is gone — do not reintroduce it); How To Use §20 = GT Fuel, §21 = Safety, Theory Part XI = GT Fuel, Part XII = PRV (`test_theory_subheadings_are_arabic_and_match_their_part` pins 11→4 / 12→7); `lc-heel` defaults to **3000**; release entry `howto-new36` (`docs.howto.b110`/`b111`). **v3.4 additions that must also survive:** the restructured documentation tabs — How To Use anchors `howto-1`…`howto-21` (**reassigned in v3.4: they now follow tab order, so `howto-5` is Custom Modules and no longer Gas Composition**), the release-notes appendix `howto-releases` with its seven `<details>` (`howto-new33`, `-new32`, `-new31`, `-new30`, `-new28`, `-new25`, `howto-new` — the last two keep their historic ids), Theory anchors `theory-p1`…`theory-p12` (likewise reassigned: `theory-p1` is now Real-Gas Properties, `theory-p5` the JIS compositional Part), and the eight new doc blocks `docs.howto.b094`–`b101` in all 9 non-English dictionaries. `docs.theory.b011` (§5.7 LHV) sits **outside** its Part's `<section>` element in the source — any script that reassembles the Theory tab by `<section>` must fold the inter-section gap back in or that block vanishes silently.

## Documentation Tab Structure Rules (v3.4) — How To Use & Theory

These two tabs are reference manuals, not changelogs. v3.4 restructured both because five years of "append the new feature at the bottom" had left them ordered by release date: a reader landed on four stacked *★ New in Version x.x* blocks, and the Basic Eng cards were scattered across sections 4, 13, 16, 17 and 18. The rules below exist so that never happens again.

1. **Order follows the tab bar, never the release date.** How To Use sections and Theory Parts are sequenced Header/global → General → Basic Eng → Advanced (Gas Quality & LNG Cargo → Hydraulics → GT Fuel, the v3.6 sub-tab order) → Safety → Report, matching the order the tabs appear in the header. Within a tab, follow the order the cards appear on screen. **A new feature is inserted at its position in that order — never appended to the end.** Renumbering the sections it displaces is part of the change, not a follow-up.
2. **A Part or section must not straddle two tabs.** v3.4 split the old Theory Parts IV and VII for exactly this reason (Papay Z and the real-gas correlations belong to Basic Eng; Darcy-Weisbach, Crane, NORSOK and RP 14E belong to the Advanced ΔP card). If new content does not sit wholly inside one tab, it needs its own Part.
3. **"★ New in Version x.x" content lives ONLY in the How To Use `Appendix — Release Notes`**, newest first, one collapsed `<details>` per release with the latest `open`. Nothing describing a release goes above the numbered sections, and Theory Part headings carry no `(v3.0)`-style version tag. Shipping a release means: document the feature in its numbered section *and* add a `<details>` entry to the appendix — the appendix is history, the sections are the manual.
4. **Every How To Use section earns its place with four things**, in this order: a plain-language paragraph on what the block is for and what depends on it; a ①②③④ workflow strip; a **realistic wireframe mockup** reproducing the actual control layout with real values (Section 11, Gas Composition Input, is the canonical example — preset selector, tier badge, citation line, cross-check chips, all fourteen component boxes, the total row); and a worked example with numbers the reader can reproduce. A one-line description of a non-trivial feature is a defect, not brevity.
5. **Renumbering is a five-file operation.** Section/Part numbers appear in: the inline English heading in `index.html`, the same heading in all 9 `docs.*` dictionaries, the jump-link strip (inside `docs.howto.b001` / `docs.theory.b001` — the translated strips carry their own copies, so rebuild all ten), the `id="howto-N"`/`id="theory-pN"` anchors, and any cross-reference in prose (`see Section 16`, `Theory Part II`, `§5.4`). Grep for every one of them before committing; `tests/test_i18n_parity.py` will not catch a stale *number*, only a missing key.
6. **Mechanise it.** The v3.4 restructure was done with scripted, mapped, single-pass rewrites over `index.html` + the 9 dictionaries, asserting the expected hit count on every substitution, then verified in a browser across all 10 languages. Hand-editing 10 files of interleaved numbering is how a section silently disappears — the 1.7 LHV block, which sits OUTSIDE its Part's `<section>` element in the source, was very nearly dropped exactly that way.
7. **Reordering costs nothing in translation; rewording costs 9 languages.** Moving a `data-i18n-html` element carries its translation with it. Editing the English text under an existing key without updating the 9 dictionaries silently leaves every non-English reader on the old content — worse than a missing key, which at least falls back visibly. Rewrite the English and the 9 translations in the same commit, and derive the translated markup from the English block rather than retyping it.

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

### Basic Eng real-gas vectors (v2.8) — SG 0.65, 2,000 psi, 150 °F, k = 1.3

Shared by the Z-Factor Estimator and the Gas Property Estimator through `papayZ()`. Re-verify after ANY change to `papayZ()`, `toPsia()`, `toRankine()`, `calcZFactor()` or `calcGasProps()`. Full derivation in `docs/SPECIFICATION.md` §9 Vectors 5–6.

| Quantity | Expected |
|---|---|
| P_pc / T_pc | 670.1290 psia / 365.1100 °R |
| P_r / T_r | 2.984500 / 1.669826 |
| **Z** | **0.8646** (0.864584 exact) — both cards must show this |
| ρ (Papay) | 0.1066271 g/cm³ |
| **μ_g** (Lee-Gonzalez-Eakin) | **0.016663 cP** |
| **c** (sonic) | **410.0269 m/s** |
| **μ_JT** | **0.3279 K/bar** |

**Use the ORIGINAL LGE coefficients** — 9.379 / 0.01607 / 209.2 / 19.26, X = 3.448 + 986.4/T + 0.01009M, Y = 2.447 − 0.2224X. The widely-copied *rounded* set (9.4 / 0.02 / 209 / 19) shifts μ by ≈ −2.1 %, and two corrupted variants circulate on wiki sites (`X = 3.488`, and `0.001·M` for `0.01·M`). `tests/test_js_constants.py` pins all of these.

## Documentation Sync Rule

`index.html` contains embedded documentation (How To Use tab, Theory tab). Whenever a feature, constant, or calculation changes, check and update:
- Theory tab: Table 5.1 constants, §5.3–§5.7 worked examples, and the Part covering the affected tab. **(Renumbered in v3.4 — the compositional Part is now V, not I; see the Documentation Tab Structure Rules above before adding or moving anything.)**
- How To Use tab: the numbered section covering the affected card (its mockup, annotations and reference-value callout), **plus a `<details>` entry in the `Appendix — Release Notes` when the change ships as a release**.
- `docs/SPECIFICATION.md` (v3.4): the affected module/API section and, if applicable, the Known Issues register.
- `docs/DEVELOPMENT_PLAN.md` (v3.4): roadmap item status when a roadmap feature ships.
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

### Automated test suite (v2.8) — run it, don't just trust the checklist

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

183 tests. Full detail in `docs/SPECIFICATION.md` §13; the essentials:

- **What it covers:** Vector 2 (ΔP), Vector 3 (Flow Regime), five candidate PRV cases, i18n key parity across all 10 dictionaries (including `{placeholder}` drift and version-string consistency), and the architectural rules — stdlib-only endpoints, no frontend build step, `pytest` never in `requirements.txt`.
- **What it does NOT cover:** **Vector 1, the JIS K 2301 chain.** It lives in JavaScript (`calcGHV()`), so pytest cannot reach it. **After any change touching `calcGHV()`, `gasComps`, or `calcLNGDensity()`, the reference values above still have to be verified by hand** — a green CI run does not mean the JIS chain is safe.
- **`requirements-dev.txt` is separate on purpose.** Vercel installs `requirements.txt` into the production runtime; never put test tooling there. `tests/test_architecture.py` enforces this.
- **The suite locks CURRENT behavior, including known defects.** Where it pins a defect (RP 14E constant, two-phase `Pc`, the zero-viscosity 500) the test says so and names the `docs/SPECIFICATION.md` §11 entry. Closing one of those issues means updating the test and the register together — that coupling is deliberate, not an obstacle to route around.
- **If a test result looks impossible, delete `__pycache__`.** A restored source file can carry an mtime older than the `.pyc` compiled from a modified version, and Python will keep serving the stale bytecode. This bit during development of the suite itself.
- Adding user-visible strings? The i18n parity test is what stops a dictionary being silently skipped — run `pytest tests/test_i18n_parity.py` after touching any `i18n/*.json`.

## Engineering Standards References

- JIS K 2301:2011 — calorific value, density, SG, Wobbe index from composition.
- ISO 6578:1991 — LNG density (Klosek-McKinley).
- API Standard 520 Part I, 9th Ed. (2014) — PRV sizing; API 526 orifice areas D–T.
- API RP 14E (5th Ed., 1991) — erosional-velocity screening criterion V_e = C/√ρ (ΔP card, v2.4). SI form V_e = 1.2199033·C/√ρ, an exact unit conversion (0.3048·√16.0184634); corrected in v2.8 from the erroneous √1.5.
- Papay (1968) with Standing-Katz pseudo-criticals — gas Z-factor (Basic Eng); validity 0 < Pr ≤ 15, 1.05 ≤ Tr ≤ 3.0.
- CODATA 2018 — gas constant.
- Colebrook & White (1939) — friction factor.

## Communication Preferences

- Explain proposed changes as targeted diffs before applying.
- When uncertain whether something is a feature or a bug, ASK — do not assume.
- Responses about engineering values should show the verification calculation.
