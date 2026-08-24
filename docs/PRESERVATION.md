# Preservation Register — feature-by-feature, v2.4 → v3.9

Companion to [`CLAUDE.md`](../CLAUDE.md) **CRITICAL Preservation Rule 5**. Every entry below
was added because the thing it names was once at risk of being silently dropped, renamed or
"simplified" away. Element IDs, payload keys, default values and test-pinned literals are an
API: treat this file as normative.

**Read this before committing any change to `index.html`.** Work through the sections for the
features your diff touches and confirm each named item still exists. Many of these are also
machine-enforced by `pytest` — but the suite pins current behaviour, so it will not catch a
feature you delete along with its test.

When a release adds something load-bearing, append a new section here — not to `CLAUDE.md`.
API-side invariants (payload defaults, error contract, stdlib rule) live in
[`api/CLAUDE.md`](../api/CLAUDE.md) instead.

---

## Baseline — must exist in every release

5. **Before committing, verify no feature was dropped**: tabs (General / Basic Eng / Advanced /
Safety / How To Use / Theory / Terms / Privacy / Report), custom modules, copy buttons, all
toggles (Abs/Gauge, HHV/LHV, VOL/MOL, MASS/MOL), the Flow Regime card (map image + Three.js 3D
animation), and all three serverless API integrations must all still exist.

---

## v2.4

- the three Basic Eng converter cards (Petroleum Gravity `api-*`, Viscosity `visc-*`, Mass↔Vol
  Flow `mf-*`), the ΔP card's Erosion C-factor input (`dp-cfactor`) and second output row
  (`dp-out-re/-f/-ve/-eratio/-ero-badge` + `dp-out-regime-note`), the out-of-range warnings
  (`z-warn`, `out-liq-warn`, `comp-warn`), and the floating action bar (Export PDF
  `exportReport()`, Share `copyShareLink()`, plus `STATE_KEY` persistence/restore).

## v2.5

- the How To Use / Theory jump-link strips and section anchors (`howto-new25`, `howto-new`,
  `howto-1`…`howto-12`, `theory-p1`…`theory-p6`), the back-to-top button (`back-to-top` + scroll
  listener), the runtime ARIA tablist semantics (`enhanceAccessibility()` + `aria-selected` in
  `switchTab()`), Enter-to-calculate on `dp-*`/`psv-*` inputs, the client-side validation
  pre-checks in `calcDeltaPressure()`/`calcPSV()`, the stale-input indicator
  (`dpResultFresh`/`psvResultFresh`/`markResultStale()`), the export pop-up Blob-download
  fallback, and the distinct viscosity option values (`0.0010` mPa·s / `0.0000010` mm²/s —
  string-distinct from cP/cSt, numerically identical).

## v2.6

- the i18n engine (`LANGUAGES` config, `loadLanguage()`, `tr()`, `applyTranslations()`,
  `setLanguage()`, `applyAwaitingBadgeDefaults()`) and the header switcher (EN/日本語 toggle +
  settings-menu dropdown) — do not rename `tr()` to `t()` or reuse `t` as a local variable name
  in any function that calls it (it already collides with locals in `exportReport()` and
  formerly in `calcZFactor()`, renamed to `trr`)
- every `data-i18n`/`data-i18n-title`/`data-i18n-aria`/`data-i18n-placeholder` attribute in
  `index.html` must have a matching key in `i18n/en.json` **and every other enabled language's
  dictionary**; `localStorage['og_lang']` and the `lang` field in `collectState()`/share-link
  state
- the idempotent (unconditional) aria-label setters in `enhanceAccessibility()` — do not
  reintroduce the old `if (!b.getAttribute('aria-label'))` guard, it silently freezes
  translations after the first language switch.

## v2.7

- the `data-i18n-html` doc-translation mechanism (`i18nHtmlOriginals` cache + the
  `[data-i18n-html]` loop in `applyTranslations()`) and all 155 `docs.*` block keys across the
  How To Use / Theory / Terms / Privacy tabs (125 from v2.7 + the 14 v2.8 blocks translated in
  v2.8.1 + the 16 v3.0 blocks, `docs.howto.b077`–`b086` and `docs.theory.b040`–`b045`) — every
  `data-i18n-html` attribute must have a matching `docs.*` key in all 9 non-English dictionaries
  (English lives inline in the HTML, not in `en.json`); all 10 `i18n/*.json` files and all 10
  `enabled: true` rows in `LANGUAGES`; the governing-language notes (`docs.terms.langNote`,
  `docs.privacy.langNote`).

## v2.8

- the Basic Eng **Gas Property Estimator** (`gp-sg`, `gp-p`/`-u`, `gp-t`/`-u`, `gp-k`,
  `gp-warn`, `gp-out-z`, `gp-out-mu`/`-u`, `gp-out-c`/`-u`, `gp-out-jt`/`-u`) and the shared
  real-gas helpers `papayZ()`/`toPsia()`/`toRankine()` that `calcZFactor()` and `calcGasProps()`
  BOTH route through — never let either card recompute Papay inline again, that duplication is
  exactly what v2.8 removed
- the **Crane fittings** block (`craneFT()`, `updateFittingSum()`, `dp-fit-details` + the twelve
  `dp-fit-*` count inputs + `dp-fit-ksum`/`-nominal`/`-ft`) and its `k_total` payload key, whose
  **default of 0 is load-bearing** — it is what keeps every pre-v2.8 share link reproducing
  Vector 2
- the **NORSOK line-sizing screen** (`renderLineSizing()`, `lastDpResult`, `dp-service`,
  `dp-out-dpfit`/`-leq`/`-dpfric100`/`-vmax`/`-vratio`/`-sizing-badge`) which judges `dpFric`
  only, never the displayed ΔP/length
- `phase_key`/`re_regime_key` from dp_calculator and the `RE_REGIME_I18N` map — do NOT
  reintroduce branching on the English badge text
- the **mobile navigation** (`buildMobileNav()`, `toggleMobileNav()`,
  `mobile-nav-wrap`/`-btn`/`-menu`/`-current`, and the `hidden md:flex` on the tab `<nav>`)
- **share-state v:2** (`escModText()`, `sanitizeSharedModule()`, `importSharedModules()`,
  `MOD_MAX_SHARED`/`MOD_MAX_TEXT_LEN`, `SHARE_URL_WARN_LEN`, the `report-*` exclusion in
  `collectInputs()`, the guarded `savedModules` parse, and the decodeShareState →
  importSharedModules → applyState boot order) — **every externally-supplied module MUST pass
  through `sanitizeSharedModule()`**, because `createCard()` interpolates module text into
  `innerHTML` and the id into inline `onclick` attributes; and the doc anchors `howto-new28`,
  `howto-13`…`howto-15`, `theory-p7`.

## v3.0

- the **Steam Properties card** (`sp-*`) and the IF97 engine — all 259 coefficients live in ONE
  `const IF97 = JSON.parse(\`…\`)` literal that `tests/test_steam_if97.py` extracts verbatim and
  re-verifies against the Release's own tables; never convert it to a plain object literal
- the **PSV steam advisory** (`psv-T-steam` + `psv-steam-advisory`, advisory-only — an
  occurrence-count test pins it out of the payload)
- the **NPSHa card** (`npsh-*`, `calcNPSH()`, `fillNPSHWater()` with its load-bearing
  `toPrecision(8)` field quantization — Vector 9 is defined through it — and
  `const NPSH_G = 9.80665;`); its deliberate NO-margin-verdict stance
- the **compressor card** (`cmp-*`, `calcCompressor()`) which must keep routing BOTH Z
  evaluations through the shared `papayZ()` (a `count == 2` test pins it) and never cites ASME
  PTC 10
- the **unit-aware clipboard** (`copyUnitOf()`, the capture-phase `_copyModClick` listener, the
  delegated long-press with `_lpUnit`/`_lpDone`, `data-unit-src`/`data-copy-unit` attributes) —
  plain click MUST stay the bare value, and in `createCard()` only the sanitized `m.id` may
  enter attribute context (unit text stays in element text; a template-scanning test enforces
  this)
- the **Basic Eng quick-links strip** (`basic.nav.*` keys, card anchors `basic-pipe`…`basic-cmp`
  with their `scroll-mt-64 md:scroll-mt-40` clearance); and the doc anchors `howto-new30`,
  `howto-16`…`howto-19`, `theory-p8`…`theory-p10`.

## v3.1

- the **GT Fuel** section (v3.6: the third Advanced sub-pane `adv-sub-gtfuel` + strip button
  `advbtn-gtfuel`; `switchTab('gtfuel')` MUST keep mapping onto `switchAdvSub('gtfuel', true)` —
  pre-v3.6 share links depend on it; `nav.gtfuel` in all 10 dictionaries) with its three panels
  `gt-select`/`gt-est`/`gt-cat` and every `gt-*` element id (selection
  `gt-vendor`/`gt-model`/`gt-cycle` + spec chips `gt-spec-*`; estimator `gt-power`/`-u`,
  `gt-eff`, `gt-hv`/`-u`, `gt-hv-basis`, `gt-hhv-ratio` + `gt-ratio-wrap`, `gt-rho`, `gt-avail`,
  `gt-import`, `gt-send-mf`, `gt-warn`; outputs
  `gt-out-q`/`-hr`/`-hr-btu`/`-vol`/`-u`/`-mass`/`-u`, totals `gt-tot-{h,d,m,y}-{vol,mass,e}`;
  catalogue `gt-cat-grid` + `gt-filt-*` pills)
- the **GT_MODELS dataset** — all 31 entries live in ONE `const GT_MODELS = JSON.parse(\`…\`)`
  literal that `tests/test_gt_fuel.py` extracts verbatim (never convert to a plain object
  literal, never drop an entry's `src` citation, and keep `|hrKJ − 3600/η| ≤ 30 kJ/kWh` when
  editing specs)
- the **static `<optgroup>` model option list** — options are hidden/disabled by
  `gtFilterModelOptions()`, NEVER rebuilt (share-link restore sets `gt-model` before any event
  fires)
- the named consts `GT_HV_FACTOR = 0.001055056 * 37.3258` (derived product, mirrors
  `HV_FACTOR`), `GT_H_YEAR = 8760`, `GT_H_MONTH = 730`; the `lastGHV` bridge assigned inside
  `calcGHV()` and read by `importGHVToGT()`; `sendGTToMassVol()` targeting `mf-mass`/`mf-rho` +
  `calcMassVol('mass')`; `calcGTFuel` in `recomputeAll()` AND in the no-stored-state boot branch
- the three original SVG `<symbol>` thumbnails `gt-svg-hd/ad/ind` (original art — vendor photos
  are copyrighted and must never be embedded)
- the catalogue's `tr()`-based render with the language-sentinel re-render
  (`gtRenderCatalogueIfStale()`); the totals convention (hourly row = instantaneous,
  daily/monthly/yearly × availability); the GT export-report section (`js.export.section6Title`
  + `js.export.gt*` keys ×10); the `gtfuel.*` namespace (56 keys) in all 10 dictionaries
- and the doc anchors `howto-new31`, `howto-20`, `theory-p11` with `docs.howto.b087`–`b090` and
  `docs.theory.b046`–`b047` in all 9 non-English dictionaries.

## v3.2

- the **Vercel Web Analytics** block — the two `<head>` tags (the `window.va` queue stub, which
  MUST stay ahead of `<script defer src="/_vercel/insights/script.js">`) and the instrumentation
  block at the end of the `<script>` (`VA_TOOL_BY_ID_PREFIX`, `vaArmed`, `vaSeenTools`,
  `trackEvent()`, `vaWrap()`). It is **purely additive by design** — it wraps globals and
  delegates off `e.target.id` rather than editing any calc function, precisely so it can never
  cause silent feature loss
- keep it that way, and add one map line per new card rather than instrumenting the card itself.
  Three invariants are load-bearing and are pinned by `tests/test_analytics_privacy.py`: (a)
  **`report` must never enter `VA_TOOL_BY_ID_PREFIX`** and the block must never read
  `.value`/`.innerText` — analytics records *that* a tool was used, never *what* was entered
- (b) `vaArmed` must stay `false` until the first `pointerdown`/`keydown`, or `recomputeAll()`
  at boot reports a `localStorage` restore as user activity
- (c) `Tool Used` must stay de-duplicated through `vaSeenTools` — the live converters fire on
  every keystroke. Any change to what is measured must update Privacy Policy §2/§5/§7/§9 **in
  the same commit**, in the inline English AND all 9 dictionaries (MARKETING.md §5 release
  rule).

## v3.3

- the **LNG reference-composition selector** on the Advanced GHV card — `comp-preset` and its
  STATIC `<option>` list (never rebuild it; a share-link restore sets the value before any event
  fires, the same rule as the v3.1 GT model list), `comp-preset-wrap`/`-badge`/`-check` and the
  three citation spans `comp-preset-src-prefix`/`-warn`/`-text`
- the **`LNG_PRESETS` dataset** — all 9 entries in ONE `const LNG_PRESETS = JSON.parse(\`…\`)`
  literal that `tests/test_lng_presets.py` extracts verbatim (never convert it to a plain object
  literal, never drop an entry's `src`), plus `LNG_PRESET_TOL = 0.05`
- the **three-tier honesty boundary** (`pub`/`ref` carry the source's own `gcv`/`wi`, `asm` must
  carry `null` for both — a cross-check against an invented number would dress a guess as a
  citation, and a test pins it)
- the per-entry `basis` field, which drives `ghv-mode` on load — GIIGNL Table 1 is **mole %**
  and reading it as volume % puts every row ~0.06 MJ/Nm³ above its published GCV
- `lastCompCheck` assigned from **`hhv_mix`, never `hv_mix`** (GCV is the gross value and must
  not follow the HHV/LHV display toggle — pinned by a test)
- `renderLNGPresetInfo()` called from inside `calcGHV()` (not only from `applyLNGPreset()`, or a
  restored share link shows a preset name with no citation) and kept free of `innerHTML`
- the delegated `input` listener that drops the selector to Custom on any manual `comp-*` edit
- the `data-i18n-label` mechanism in `applyTranslations()` for `<optgroup>` labels (plain
  `data-i18n` sets textContent, which would delete an optgroup's children) and its matching
  branch in `test_i18n_parity.py`'s `ATTR_PATTERN`; the `advanced.ghv.preset.*` namespace (19
  keys) in all 10 dictionaries
- and the doc anchors `howto-21`, `theory-p12` with `docs.howto.b092`–`b093` and
  `docs.theory.b048`–`b049` in all 9 non-English dictionaries.

## Share-link decode (2026-08-16)

- `decodeShareState()` reads the payload from the fragment **and** the query string, fragment
  first, through `normalizeShareB64()` (which undoes percent-encoding, `+`→space and base64url).
  **`copyShareLink()` must keep emitting `#s=` and must never emit `?s=`** — a fragment never
  reaches the server, a query string lands in access logs, and generating one would put user
  inputs into Vercel's logs against the Privacy Policy and the v3.2 analytics boundary.
  `tests/test_share_state.py` fails if this is flipped. The `?s=` read path exists because
  LinkedIn strips everything after the `#` when it auto-links a URL. The C4-split sensitivity
  figure (**≤ 0.03 MJ/Nm³**) is quoted in the on-screen citations, the Theory tab and
  `C4_SPLIT_MAX_SPREAD` — a test asserts the citation and the enforced number are the same
  number, so re-measure before tightening the claim.

## v3.4

- the restructured documentation tabs — How To Use anchors `howto-1`…`howto-21` (**reassigned in
  v3.4: they now follow tab order, so `howto-5` is Custom Modules and no longer Gas
  Composition**), the release-notes appendix `howto-releases` with its seven `<details>`
  (`howto-new33`, `-new32`, `-new31`, `-new30`, `-new28`, `-new25`, `howto-new` — the last two
  keep their historic ids), Theory anchors `theory-p1`…`theory-p12` (likewise reassigned:
  `theory-p1` is now Real-Gas Properties, `theory-p5` the JIS compositional Part), and the eight
  new doc blocks `docs.howto.b094`–`b101` in all 9 non-English dictionaries. `docs.theory.b011`
  (§5.7 LHV) sits **outside** its Part's `<section>` element in the source — any script that
  reassembles the Theory tab by `<section>` must fold the inter-section gap back in or that
  block vanishes silently.

## v3.5

- the **LNG Cargo Estimator** card (`adv-lng-cargo`, id prefix `lc-` → analytics slug
  `lng-cargo`): `lc-vessel` and its STATIC 36-option list (never rebuild — filters
  `lcFilterVesselOptions()` only hide/disable; share-restore rule),
  `lc-cap`/`-fill`/`-heel`/`-bor`/`-days`, outputs `lc-out-vliq`/`-mass`/`-gas`/`-e`/`-el` with
  unit selects `lc-out-mass-u`/`-gas-u`/`-e-u` and the delivered spans `lc-out-*-d`/`-dv`, chips
  `lc-out-dens`/`-exp`, cross-link `lc-out-gt`, filter pills `lc-filt-t-*`/`lc-filt-c-*`, the
  vessel panel ids `lc-thumb-*`/`lc-spec-*`/`lc-src`/`lc-credit`/`lc-link-mt`/`lc-link-vf`,
  catalogue `lc-cat`/`lc-cat-grid`/`lc-cat-count`, and the four original schematics
  `lc-svg-{membrane,moss,ssp,typec}`
- the **`LNG_VESSELS` dataset** — 36 entries in ONE `const LNG_VESSELS = JSON.parse(\`…\`)`
  literal that `tests/test_lng_cargo.py` extracts verbatim
- **every entry must keep its own public `src`/`srcUrl`** (an owner/builder/class-society page
  or Wikipedia — NEVER an AIS/spotter site, NEVER the IGU report: its Appendix 3 is
  all-rights-reserved Rystad data and is deliberately not reproduced; the report is cited for
  fleet context only)
- `photo`/`credit`/`creditUrl` must agree with `assets/vessels/CREDITS.json` (Wikimedia Commons
  CC BY-SA / PD thumbnails only, ≤ 130 KB, credited on screen — no
  MarineTraffic/VesselFinder/ShipSpotting imagery ever, those are linked by IMO as plain
  hyperlinks)
- the **`lastLNGProps` bridge** assigned inside `calcGHV()` (kept SEPARATE from the test-pinned
  `lastGHV`) and `calcLNGCargo()` called at the end of `calcGHV()`, in `recomputeAll()` after
  `calcGTFuel`, and at the end of `calcGTFuel()` — the card owns no physics and must never touch
  `gasComps`/ISO 6578 itself; `lcRenderVessel()` stays textContent-only; the explicit
  `LC_TYPE_KEYS`/`LC_CONT_KEYS` maps (dead-key sweep); export §7 (`js.export.section7Title` +
  `lc*` keys); the `advanced.lngCargo.*` namespace (89 keys) in all 10 dictionaries.

## v3.5 — GT Fuel unit switches

- the named constants `GJ_PER_MMBTU = 1.055056`, `MJ_PER_MWH = 3600`, `KG_PER_LB = 0.45359237`,
  `RHO_LBSCF_TO_KGNM3 = KG_PER_LB * 37.3258` (test-pinned literals)
- `gt-rho-u` (kg/Nm³ | lb/scf) — **lb/scf converts with 16.9307, never 16.0185** (standard vs
  actual volume; `gtLastResult.rho` stays kg/Nm³, `importGHVToGT()` converts back)
- `gt-out-q-u`, the extended `gt-out-vol-u`/`gt-out-mass-u` lists, the totals-header selects
  `gt-tot-vol-u`/`gt-tot-q-u`/`gt-tot-e-u` and the new `gt-tot-{h,d,m,y}-q` column (in `outIds`)
  — defaults must reproduce the Vector 11 strings byte-for-byte
- clipboard census now 26 static / 6 literal. Docs: How To Use §16 (`howto-16`,
  `docs.howto.b102`–`b106`), the GT §21 addendum (`b107`), release entry `howto-new35`
  (`b108`/`b109`), Theory Part IX (`theory-p9`, `docs.theory.b050`/`b051`) and the Part XII
  addendum (`b052`) — the sections they displaced were renumbered to `howto-17`…`22` /
  `theory-p10`…`13` in all ten languages by script; do the same for the next insertion (rule 5
  above), never append.

## v3.6

- the **two-layer Advanced tab** — strip `adv-subnav` with `advbtn-gasq`/`-hyd`/`-gtfuel`,
  sub-panes `adv-sub-gasq`/`-hyd`/`-gtfuel`, `ADV_SUBS`/`ADV_SUB_KEYS`,
  `switchAdvSub(sub, quiet)`, `gotoAdvSub()`, `currentAdvSub`, the `advSub` field in
  `collectState()`/`applyState()` (restored on every visit, unlike `tab`), the indented sub-tab
  rows + "Advanced › ⟨sub⟩" trigger in `buildMobileNav()`, the sub-tab `tablist` semantics in
  `enhanceAccessibility()`, `vaWrap('switchAdvSub', …)` reusing the `Tab View` event, and the
  `nav.adv.*` keys (6) in all 10 dictionaries
- the top bar has **9** tabs (`btn-gtfuel` is gone — do not reintroduce it)
- How To Use §20 = GT Fuel, §21 = Safety, Theory Part XI = GT Fuel, Part XII = PRV
  (`test_theory_subheadings_are_arabic_and_match_their_part` pins 11→4 / 12→7)
- `lc-heel` defaults to **3000**; release entry `howto-new36` (`docs.howto.b110`/`b111`).

## v3.7

- the ΔP **TWO-PHASE METHOD** selector `dp-tp-method` (STATIC option list
  `hem`/`lm`/`msh`/`friedel` — share-restore rule) and the Friedel-only **SURFACE TENSION**
  field `dp-sigma`/`dp-sigma-wrap` with `updateTpMethodUI()` (registered in `recomputeAll()` so
  a restored `tp_method=friedel` re-shows it)
- the `tp_method`/`sigma` payload keys whose **absent defaults are load-bearing** — an absent
  `tp_method` must stay bit-identical to HEM (same rule as `k_total`/`cfactor`; see
  `api/CLAUDE.md` "v3.7 — Selectable two-phase methods")
- `two_phase_dpdz()` and the additive response fields `tp_method`/`sigma`/`phi2`/`lm_X`/`lm_C`
- the rebuilt Three.js animation — `initFlow3D()`/`stopFlow3D()` (with geometry/material
  disposal + `forceContextLoss()`), `showFlow3DUnavailable()`,
  `rebuildFlow3D()`/`setFlow3DSpeed()`/`toggleFlow3DPause()`, and the mode strip
  `fr-3d-view`/`fr-3d-regime`/`fr-3d-speed`/`fr-3d-pause` (STATIC option lists; `fr-3d-regime`
  previews under the calculated θ and must keep the PREVIEW overlay tag)
- the 27 new working-tool i18n keys (`advanced.deltaP.tpMethod*`/`tpm*`/`sigma*`,
  `advanced.flowRegime.view*`/`regime*`/`rg*`/`speedLabel`/`pauseAria`/`previewTag`,
  `js.export.tpMethodLabel`) in all 10 dictionaries
- and the doc anchors/blocks `howto-new37` (`docs.howto.b112`/`b113`), Theory §10.6 + Part XIII
  citation cards (`docs.theory.b053`/`b054`) in all 9 non-English dictionaries.

## v3.8

- the Safety-tab **per-field pressure inputs** — for each of `psv-P1`, `psv-P2`, `psv-P1-steam`,
  `psv-P1-liq`, `psv-Ps`, `psv-P2-liq`, `psv-Po`, `psv-Pa`: the unit `<select id="<id>-u">`
  (STATIC option list — psi `6894.75729` first, kPa `1000` second, then bar/MPa/Pa/atm/kg/cm²;
  share-restore rule; the string values are compared verbatim by `psvSyncPressUnits()`), the
  Abs/Gauge pair `<id>-abs`/`<id>-gau`, and the ⇩ `importPsvPressure(id)` button
- `PSV_PRESS_IDS`, `PSV_PRESS_GAUGE_DEFAULT` (the three liquid fields — API 520 §5.8/§5.9 are
  gauge; everything else absolute, i.e. the pre-v3.8 meaning of every field),
  `PSV_PSI_PA`/`PSV_KPA_PA`, the `psvPressMode` map,
  `setPsvPressMode()`/`paintPsvPressMode()`/`applyPsvPressModes()`, `psvPressFactor()`,
  **`psvPressForApi(id, units, gaugeOut)`** — every pressure `calcPSV()` sends MUST go through
  it (`gp()` absolute / `gg()` gauge; a test forbids raw `g('psv-P…')` reads) and it must keep
  passing a field that already sits on the system's canonical unit+basis through **unchanged**,
  which is what keeps Vector 4 and old share links bit-identical
- `onPsvUnitsChange()` (the `psv-units` onchange — moves psi↔kPa selections only and, since
  v3.8.2, CONVERTS the figure with the label via `psvRescale()` — the old "numbers stay" rule
  turned the default H case into R under SI) and `updateSteamAdvisory()` reading
  `psvPressForApi('psv-P1-steam', …)`
- `psvPm` in `collectState()`/`applyState()` plus the legacy shim
  (`!('psv-P1-u' in s.inputs) && psv-units === SI → psvSyncPressUnits('SI')`)
- the **one-click defaults** (`value=` attributes: gas W 8000 · M 19 · k 1.3 · T 560 · Z 1.0 ·
  P1 179.7 · P2 0 → orifice H = **Vector 15**; steam/liquid/two-phase on Vector 4 — `psv-W-tp`
  is **238715**, not the old 477,430 placeholder)
- the `safety.psv.importPressTitle`/`importPressEmpty`/`importPressDone` keys in all 10
  dictionaries (`hintGauge`/`hintAbsolute` are retired — do not reintroduce)
- Theory **§12.8** (Part XII now has 8 sub-headings —
  `test_theory_subheadings_are_arabic_and_match_their_part` pins 12→8) and the doc blocks
  `docs.howto.b114` (§21 anatomy + worked example), `howto-new38` (`b115`/`b116`),
  `docs.theory.b055` in all 9 non-English dictionaries. API `psv_calculator.py` was deliberately
  NOT changed — the conversion is a client responsibility.

## v3.8.1

- the unit `<select id="<id>-u">` on `psv-W`/`-W-steam`/`-W-tp`, `psv-T`, `psv-T-steam`,
  `psv-Q`, `psv-mu`, `psv-vo`/`-v9` (STATIC lists; first option = USC canonical, second = SI
  canonical; `psv-mu` keeps cP `1` / mPa·s `1.0` string-distinct), the **`PSV_QTY`** table +
  `psvQty()`/`psvTempToK()`/`psvTempFromK()`/`psvSyncQtyUnits()` — `calcPSV()` reads
  W/T/Q/µ/vo/v9 through `gq()` (a test forbids raw `g(…)` reads) and `updateSteamAdvisory()`
  reads `psvQty('psv-T-steam', …)` (the five-reference pin on `psv-T-steam` still holds — input
  id, select id, PSV_QTY key, comment, advisory read)
- **`psvEnsureDefaults()`/`psvResetPanel()`/`PSV_PANEL_REQUIRED`** called in `applyState()`
  between `applyInputs()` and `recomputeAll()` — this is what makes the one-click defaults
  visible to RETURNING visitors (a saved session restores over the HTML `value=` attributes),
  the liquid rule is **P1 *or* Ps** (never both required, or a certified case is wiped), and a
  complete saved case must never be touched
- `_psvUnitLabels()` is an intentional no-op shell — do not delete it and do not put relabelling
  back into `updatePSVMode()`.

## v3.8.2 / v3.8.3

- `psvRescale()` + the converting branch in `psvSyncQtyUnits()` (temperatures through
  `psvTempToK`/`psvTempFromK`, `from === to` short-circuit for cP), the **`↺ Load example`**
  button `psv-load-example` → `psvLoadExample()` (resets all four panels via `psvResetPanel()`,
  leaves mode/units alone, then — v3.8.3 — `psvExpressPanelInSystem()` re-expresses each reset
  panel in the ACTIVE unit system through the `scope`-limited
  `psvSyncPressUnits(units, box)`/`psvSyncQtyUnits(units, box)`; the restore fallback in
  `psvEnsureDefaults()` does the same — never reset a panel without it, or an SI user gets USC
  labels back) and its keys `safety.psv.loadExample`/`loadExampleTitle` in all 10 dictionaries.

## v3.9

**The full active LNG fleet (IGU Appendix 3, licensed).** Must survive:

- The **`LNG_FLEET` dataset** — ONE `JSON.parse` literal of **768** compact rows
  `[imo, name, owner, builder, cap_m3, cont, type, prop, year]` (`tests/test_lng_cargo.py`
  extracts it verbatim; never convert to a plain literal), expanded at boot with `igu: true`;
  `LNG_FLEET_BY_ID` (Map) and `LNG_FLEET_SRC_URL`
  (`https://www.igu.org/igu-reports/2026-world-lng-report/`).
- **The licence and its rendered conditions.** The rows reproduce Appendix 3 of the IGU World
  LNG Report 2026 (data: Rystad Energy) under the **IGU's written permission of 2026-08-24**
  (E. Minty, Director Communication; Gmail thread 1a0155dd0d9f2ec8). Conditions — full
  attribution and a link to the original source — are load-bearing UI: `lcRenderVessel()`
  routes `v.igu` rows to `advanced.lngCargo.iguSrc` + `LNG_FLEET_SRC_URL`; the on-card
  `advanced.lngCargo.fleetContext` note states the permission and the no-re-extraction
  undertaking; Terms §6 (`docs.terms.b008`, EN + 9) carries the licence statement; the LICENSE
  third-party section records it. Removing any of these breaks the grant's terms, not just a
  feature. Do NOT add rows from any other rights-reserved compilation without an equivalent
  grant, and never swap a featured row's primary-source citation for the IGU's.
- **Dedup rule:** the 36 featured `LNG_VESSELS` IMOs never appear in `LNG_FLEET`; where the
  report and a featured row disagree on capacity, the featured row keeps its primary source's
  figure (15 such rows as of v3.9).
- The **`grpFleet` static optgroup** — 768 options, labels `Name — cap m³ · Owner` derived
  from the dataset; the whole `lc-vessel` list is 805 options and is still NEVER rebuilt
  (filters hide/disable only; share-restore rule).
- Vessel type **`bunk`** (`advanced.lngCargo.type.bunk`, 1 ship, Hai Yang Shi You 301) in
  `LC_TYPE_KEYS` and in the small-scale filter bucket
  (`v.type === 'small' || v.type === 'mid' || v.type === 'bunk'`).
- The catalogue's two-tier render: featured photo cards + compact fleet cells, count line
  totalling both (`rows.length + fleetRows.length`).
- New i18n keys ×10: `advanced.lngCargo.{fleetContext (rewritten), grpFleet, iguSrc, type.bunk}`,
  `docs.howto.{b117, b118}`; rewritten doc blocks: `docs.howto.b104/b105`, `docs.theory.b051`,
  `docs.terms.b008` (all ten languages).
