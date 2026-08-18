# Detailed Specification — O&G Engineering Converter

**Document version:** 2.0 (describes app v3.6)
**Maintainer:** Naoto Yamabe (petro.naoto@gmail.com)
**Companion documents:** [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) · [MARKETING.md](MARKETING.md)

This is the engineering specification of every feature in the application. It is kept in sync with the code under the Documentation Sync Rule (see CLAUDE.md): any change to a feature, constant, ID, or calculation must update the affected section here in the same commit.

---

## 1. Scope & Conventions

- **Element IDs are an API.** JavaScript addresses the DOM exclusively by ID. IDs listed in this document are load-bearing contract elements; they are never renamed or removed without a coordinated change.
- **Multiply-to-SI unit factors.** Every unit `<select>` whose id ends in a unit suffix (`*-u`, `*-unit`, `*_m`) stores a factor that **multiplies** the entered value to reach SI: flow × factor → kg/s, density × factor → kg/m³ (kg/m³ = 1, lb/ft³ = 16.0185), viscosity × factor → Pa·s, length × factor → m. (Density conversion was fixed to multiply in v2.3.1 — never divide.)
- **Interaction models.** Two patterns exist by design:
  - *Live converters* (General tab, Basic Eng, compositional GHV): recompute on `input`/`onchange`.
  - *Button-triggered calculators* (Pipe ΔP, Flow Regime, PRV sizing): compute on button press because they call serverless APIs. Since v2.5 these support Enter-to-calculate and show a stale-input indicator when inputs change after a result.

## 2. Runtime & Architecture

| Layer | Technology | Notes |
|---|---|---|
| Frontend | `index.html` — vanilla JS + Tailwind CSS (CDN) | Single file, no build step. One `<script>` block, global scope, ~40 functions. |
| 3D | Three.js r128, lazy-loaded from cdnjs via `loadThree()` only when the Flow Regime card is used | Promise-cached; graceful "3D unavailable" fallback if the CDN is blocked. |
| Serverless | Python on Vercel, `api/` auto-detected | `dp_calculator.py` and `psv_calculator.py`: standard library only. `flowregime.py`: numpy/matplotlib/seaborn (`requirements.txt`). |
| Persistence | Browser `localStorage` only | Keys: `og_ui_state_v24` (session state), `og_custom_modules` (user-built cards), `og_lang` (selected UI language, v2.6). No server-side storage. |
| Assets | `lng-plant-bg.jpg` (background), `favicon.ico`, `assets/flow-regime-map.png`, `assets/flow-regime-3d.gif` (doc images) | |
| Analytics (v3.2) | Vercel Web Analytics, script-tag install (`/_vercel/insights/script.js` + a `window.va` queue stub) | Cookieless. Edge-injected at request time — the path looks local but no such file exists in the repo, so the no-build-step rule is intact. 404s off Vercel; the app is unaffected. See §14. |

Local development requires `vercel dev` (opening `index.html` directly breaks the three API-backed cards).

## 3. UI Design System

- **Theme:** dark only. Base `bg-slate-950`, glassmorphism cards (`bg-slate-900/70`, `backdrop-blur-xl`), amber-500 primary accent, per-card accent dots (cyan/purple/fuchsia/red/orange), grayscale LNG-plant photo background under a gradient overlay.
- **Canonical converter card = Pipe Volume Calculator (Basic Eng).** Every converter card follows its philosophy:
  1. Figure and unit are **separate adjacent boxes** (`rounded-l-lg` figure box holding input + copy button; `rounded-r-lg` unit box) in one flex row.
  2. They highlight **independently**: figure box `focus-within:ring-2 focus-within:ring-amber-500`; unit `<select>` `focus:ring-2 focus:ring-amber-500`.
  3. Selectable units are native `<select>`s styled `bg-slate-800 border-y border-r border-slate-700 rounded-r-lg text-amber-500`, keeping the **native dropdown arrow** (no `appearance-none`).
  4. Fixed units use a matching static chip with no arrow.
- **Calculator cards** (Pipe ΔP, PRV) intentionally use denser input grids (`grid-cols-2 md:grid-cols-4`) — they are calculators, not converters, and are exempt from the converter-card layout rule.
- **Navigation:** sticky header with 9 tab buttons (`btn-general` … `btn-report`) in a horizontally scrollable bar; `switchTab(name)` toggles `tab-*` panel visibility, updates button styling and `aria-selected`, scrolls the active button into view (v2.5), and scrolls the page to top. Tab buttons carry `role="tab"` inside a `role="tablist"` nav; panels are `role="tabpanel"` (applied at runtime by `enhanceAccessibility()`).
- **Mobile navigation (v2.8):** below the `md` breakpoint the tab bar is `display:none` and a dropdown replaces it — trigger `#mobile-nav-btn` (shows the active tab's translated label), panel `#mobile-nav-menu`, wrapper `#mobile-nav-wrap`. `buildMobileNav()` generates the nine items **at runtime from the tab buttons themselves**, reusing each button's `data-i18n` key, so there is no second tab list to drift and translations are picked up automatically; it is re-run from `updateLangSwitcherUI()` on every language change and from `switchTab()` on every selection. `toggleMobileNav(force)` mirrors `toggleLangMenu()` exactly — same wrap/relative + absolute/hidden structure, same click-outside listener, plus Escape-to-close — so the file has one dropdown idiom, not two. All nine `btn-*` buttons remain in the DOM at every viewport.
  - **Accessibility:** because `display:none` removes the desktop bar from the accessibility tree, exactly **one** `role="tablist"` is exposed at any viewport (verified in a browser at 375 px and 1280 px). The generated menu items therefore carry their own `role="tab"` / `aria-controls` / `aria-selected`, set inside `buildMobileNav()` so they are correct by construction on every rebuild.
- **Floating action bar** (bottom-right, hidden in print): Share, Export PDF, and Back-to-Top (v2.5, appears after ~600 px scroll); `state-toast` gives feedback.
- **Copy buttons:** inline SVG buttons on inputs/outputs → clipboard, with a 1.5 s green check; `aria-label`s are backfilled at runtime.
- **Basic Eng quick links (v3.0):** the tab holds nine cards, so a jump-link strip (`<nav aria-label>`, key `basic.nav.aria`) sits above the grid — one pill per card in that card's accent color, translated via `basic.nav.*` keys, targeting new card anchors `basic-pipe`/`-z`/`-api`/`-visc`/`-mf`/`-gp`/`-steam`/`-npsh`/`-cmp`. The card divs carry `scroll-mt-64 md:scroll-mt-40` so anchors clear the sticky header — sized from live measurements (header 226 px tall at 375 px width, 134 px at 1280 px; the doc-tab anchors predate this and are unchanged). Same pill idiom as the How To Use / Theory strips.
- **Unit-aware clipboard (v3.0):** a plain click copies the **bare value** — unchanged since v1, deliberately, so pasted values stay numbers in spreadsheets. Ctrl/⌘/Shift+click, or a ~500 ms long-press on touch/pen pointers, appends the unit and confirms via toast (`common.copiedWithUnit`). Unit resolution (`copyUnitOf(btn)`): `data-copy-unit="literal"` for fixed chips (MJ/Nm³, Btu/scf, °API, g/mol) else `data-unit-src="id [id2 …]"` — space-separated element ids, first non-`hidden` wins (this is how the VOL/MOL flow outputs follow the visible selector), `<select>` → selected option's **label text**, anything else → `innerText`. Buttons with neither attribute (Z, SG, WI, MCP, orifice letter — and the PSV orifice area, whose displayed text already embeds its unit) behave identically on every path. Mechanism is fully delegated: a capture-phase click listener records modifier state (the 30+ inline `onclick` attributes are untouched) and document-level pointer listeners implement the long-press (mouse pointers excluded — they have modifier keys; a drag cancels; Android's ~500 ms `contextmenu` is suppressed on copy buttons only, mid-press only). The long-press fires `btn.click()` with `_lpUnit` set and swallows the follow-up native click via `_lpDone` (auto-cleared at 700 ms in case none arrives). **Security invariant:** only element IDs may appear in `data-unit-src`; in `createCard()` the (sanitized) module id goes into the attribute while the user-supplied unit text stays in element text content, preserving the v2.8 `sanitizeSharedModule()` contract.

## 4. Feature Specifications by Tab

### 4.1 General

| Card | Inputs (IDs) | Behavior |
|---|---|---|
| **Gas Volume** | `nm3-input`/`nm3-select`, `scf-input`/`scf-select` | Bidirectional live conversion; base factor **1 Nm³ = 37.3258 scf** with unit multipliers (kNm³, MMscf, …). |
| **Pressure** | `press-input1`/`press-select1` + mode buttons `press-mode1-abs`/`-gau`; mirrored `…2` set | Dual-sided converter; each side independently Abs or Gauge (`setPressMode`). Conversion goes through absolute Pa (`pressToAbsPa`/`pressFromAbsPa`, atmosphere = 101.325 kPa). |
| **Temperature** | `temp-input1`/`temp-select1`, `temp-input2`/`temp-select2` | °C/°F/K bidirectional (`convertTemp`). |
| **Heating Value** | `hv-input1`, `hv-input2` | Fixed-unit MJ/Nm³ ↔ Btu/scf pair (`HV_FACTOR`). |
| **Custom Modules** | Builder modal (`openModal()`), presets (flow rate, density, viscosity, …) | User-defined linear-factor converter cards; persist in `localStorage['og_custom_modules']`; created via `createCard`. **Since v2.8 they travel in Share links** (state v:2, behind the sanitizing import boundary — see §6.1 and §11 #7); max 20 modules per link, 40 characters per label. |

### 4.2 Basic Eng

| Card | Inputs → Outputs (IDs) | Method |
|---|---|---|
| **Pipe Volume** | `pipe-id`, `pipe-length`, `pipe-out-u` → `pipe-vol-out` | V = π/4 · D² · L with mixed metric/imperial units (`calcPipeVolume`). Canonical card layout. |
| **Z-Factor Estimator** | `z-sg`, `z-p`/`z-p-u`, `z-t`/`z-t-u` → `z-result`, warning `z-warn` | **Papay (1968)**: Z = 1 − 3.52·Pr/10^(0.9813·Tr) + 0.274·Pr²/10^(0.8157·Tr), with **Standing-Katz pseudo-criticals** Ppc = 756.8 − 131·SG − 3.6·SG², Tpc = 169.2 + 349.5·SG − 74·SG² (psia/°R). Validity envelope 0 < Pr ≤ 15, 1.05 ≤ Tr ≤ 3.0; out-of-envelope inputs show an extrapolation warning in `z-warn`. |
| **Petroleum Gravity** | `api-grav`, `api-sg`, `api-den`/`api-den-u` | Three-way °API ↔ SG(60/60°F) ↔ density; °API = 141.5/SG − 131.5; water at 60 °F = 999.016 kg/m³ (`RHO_WATER_60F`). |
| **Viscosity** | `visc-dyn`(+unit), `visc-kin`(+unit), `visc-rho` | ν = μ/ρ; dynamic (cP, mPa·s, Pa·s) ↔ kinematic (cSt, mm²/s, m²/s) via density. Since v2.5, mPa·s and mm²/s use the distinct option values `0.0010`/`0.0000010` so restored state keeps the selected label (numerically identical to cP/cSt). |
| **Mass↔Vol Flow** | `mf-mass`(+unit), `mf-vol`(+unit), `mf-rho` | Q_m = Q_v · ρ bidirectional (`calcMassVol`). |
| **Gas Property Estimator** (v2.8) | `gp-sg`, `gp-p`/`gp-p-u`, `gp-t`/`gp-t-u`, `gp-k` → `gp-out-z`, `gp-out-mu`/`-u`, `gp-out-c`/`-u`, `gp-out-jt`/`-u`, warning `gp-warn` (`calcGasProps`) | Four screening outputs from one (SG, P, T, k) set, all chained to the **shared `papayZ()` helper** — see below. **μ:** Lee, Gonzalez & Eakin (1966), SPE 1340, **original unrounded coefficients** (K = (9.379 + 0.01607M)T^1.5/(209.2 + 19.26M + T), X = 3.448 + 986.4/T + 0.01009M, Y = 2.447 − 0.2224X, μ[cP] = 10⁻⁴·K·exp(X·ρ^Y); T in °R, M in lb/lbmol, ρ in g/cm³). ρ = PM/(ZRT) with R = 10.731577. **c:** √(k·Z·R_u·T/M), R_u = 8314.462618 J/(kmol·K). **μ_JT:** (R·T²/(P·C_p))·(∂Z/∂T)_P, with ∂Z/∂T by central difference on the same Papay expression (h = 0.5 °R, hard-coded) and C_p = kR/(k−1). MW = SG × 28.9647. Validity: warns (never clamps) outside the Papay envelope and outside LGE's 100–340 °F / 100–8,000 psia experimental basis. Labelled **SCREENING** in the UI — only Papay and LGE are published correlations; the sonic-velocity form is an engineering approximation and μ_JT has no single governing document. |

| **Steam Properties** (v3.0) | `sp-p`/`sp-p-u`, `sp-t`/`sp-t-u` → `sp-out-state`/`-statenote`, `sp-out-rho`/`-u`, `sp-out-h`/`-u`, `sp-out-s`/`-u`, `sp-out-cp`/`-u`, `sp-out-w`/`-u`, `sp-out-tsat`/`-u`, `sp-out-hfg`/`-u`, `sp-out-satnote`, warning `sp-warn` (`calcSteamProps`) | **IAPWS-IF97** (Revised Release 2007) Regions 1 (compressed liquid), 2 (steam) and 4 (saturation line) + the B23 boundary, evaluated client-side. Classification: T ≤ 623.15 K → p vs p_sat(T); 623.15–863.15 K → p vs B23; Region 3 and out-of-range → structured refusal, never extrapolation. Properties from the dimensionless Gibbs equations and their analytic derivatives (ρ, h, s, c_p, w). Saturation row: T_sat by Eq. 31 (closed form), h_f = h^R1(p, T_sat), h_g = h^R2(p, T_sat), shown up to p_sat(623.15 K) = 16.529 MPa (liquid side of the line above that is Region 3). Near-saturation (\|p/p_sat − 1\| < 0.001) shows a two-phase warning. Unit factors are exact by definition: psia→MPa 0.006894757, Btu/lb 0.42992261 (= 1/2.326), Btu/(lb·°R) 0.23884590 (= 1/4.1868), lb/ft³ 0.062427960. Range 273.15–1073.15 K, 0 < p ≤ 100 MPa. |

| **Pump Suction — NPSHa** (v3.0) | `npsh-p`/`-u`, `npsh-pv`/`-u`, `npsh-rho`/`-u`, `npsh-z`/`-u`, `npsh-hf`/`-u`, water helper `npsh-tw`/`-u` + `npsh-fill` → `npsh-out`/`-u`, `npsh-breakdown`, warning `npsh-warn` (`calcNPSH`, `fillNPSHWater`) | First-principles head balance NPSHa = (P_surf − P_v)/(ρ·g) + z − h_f with g = 9.80665 m/s² exactly; z negative = suction lift; NaN-safe positive-assertion guards (h_f ≥ 0, ρ > 0, P_surf > 0, P_v ≥ 0). Term breakdown displayed. Warnings at the physical cliffs only: P_surf ≤ P_v (vessel boiling) and NPSHa ≤ 0 (flashing before the impeller). **Water helper:** fills P_v = p_sat(T) (IF97 Region 4) and ρ = ρ_f(T) (Region 1 on the saturation line) into the fields at 8 significant figures — visible and overridable, valid 0–350 °C, routed through the SAME `if97PsatMPa()`/`if97Region1()` as the steam card. **Deliberately NO margin verdict** — NPSHr lives on the vendor curve; HI 9.6.1 / API 610 margins are licensed and not reproduced. |

| **Compressor — Head & Power** (v3.0) | `cmp-sg`, `cmp-p1`/`-u`, `cmp-t1`/`-u`, `cmp-p2`/`-u`, `cmp-k`, `cmp-eta`, optional `cmp-flow`/`-u` → `cmp-out-z`, `cmp-out-hp`/`-u`, `cmp-out-his`/`-u`, `cmp-out-t2`/`-u`, `cmp-out-power`/`-u`, `cmp-out-path`, warning `cmp-warn` (`calcCompressor`) | First-principles screening: H_poly = Z_avg·(R/M)·T₁·(r^m − 1)/m with m = (k−1)/(k·η_p) = (n−1)/n; H_is with m_s = (k−1)/k; T₂ = T₁·r^m (perfect-gas polytropic path); implied η_s = η_p·H_is/H_poly; gas power W = ṁ·H_poly/η_p (no mechanical losses). **Real-gas correction:** Z_avg = (Z₁ + Z₂)/2 through the SAME `papayZ()`/`toPsia()`/`toRankine()` as the Z-Factor and Gas Property cards; Z₂ is evaluated ONCE at the perfect-gas T₂ estimate — a deterministic single pass, deliberately not an iteration. Per-state Papay validity warnings; P₂ ≤ P₁ rejected with a compression-only message; η_p entered in percent, rejected outside (0, 100]. R_u = 8314.462618, MW = SG × 28.9647 — the Gas Property card's literals, no new physics constants. Output factors from exact definitions: ft·lbf/lbm = 9.80665 × 0.3048 = 2.98906692 J/kg (literal 334.55256), hp = 550 ft·lbf/s = 745.69987 W (literal 1.3410221); flow factors multiply-to-kg/h (1000, 1, 3600, 0.45359237). **Not an ASME PTC 10 procedure** — that test code is licensed and is neither used nor cited as a source. |

**IF97 coefficient contract (v3.0).** All 259 coefficients (R1 34×3, R2 9×2 + 43×3, R4 10) plus the 5 B23 constants live in ONE `JSON.parse` literal (`const IF97 = JSON.parse(\`…\`)`). `tests/test_steam_if97.py` extracts that exact literal, re-implements the equations independently in Python, and reproduces the Release's own computer-program verification tables — Table 5, Table 15, Tables 35/36, and the B23 check point — to 9 significant figures, so a single mistyped digit fails CI. Do not convert the literal to a plain JS object: that silently breaks the extraction. The browser-side arithmetic is verified by hand against the same tables (Vector 8, §9).

**Shared real-gas helpers (v2.8).** `papayZ(sg, pPsia, tRankine)` returns `{ppc, tpc, pr, trr, Z, oob}`; `toPsia(v, unit)` and `toRankine(v, unit)` carry the unit ladders. The Z-Factor Estimator and the Gas Property Estimator both route through them, so the two cards cannot report different Z for identical inputs. Before v2.8 the correlation was inline in `calcZFactor()`; the extraction was verified by differential-testing the new helper against a verbatim copy of the original arithmetic over **7,203 input combinations in a real browser engine — zero mismatches, bit-for-bit** (`Object.is`). `tests/test_js_constants.py` asserts the correlation appears exactly once in executable JS and that its constants agree across the code, the Theory tab and this document.

### 4.3 Advanced

**Two-layer navigation (v3.6).** The Advanced pane opens on a segmented strip (`adv-subnav`, ARIA `tablist`) with three sub-tabs, each a `<button id="advbtn-{sub}">` carrying a name (`nav.adv.gasq` / `nav.adv.hyd` / `nav.gtfuel`) and, at `lg` and above, a one-line description (`nav.adv.*Desc`). `switchAdvSub(sub, quiet)` toggles the sub-panes `adv-sub-gasq` (GHV card + LNG Cargo Estimator), `adv-sub-hyd` (Pipe ΔP + Flow Regime) and `adv-sub-gtfuel` (the three GT cards, §4.6) and the strip's active state; `ADV_SUBS = ['gasq','hyd','gtfuel']`. The chosen sub-tab is stored as `advSub` in the persisted state and in share links and is restored on every visit (unlike the top-level tab, which follows the v2.5.1 landing rule); `switchTab('gtfuel')` maps onto `switchAdvSub('gtfuel')` so legacy links still open GT Fuel; the mobile dropdown lists the three sub-tabs as indented rows under Advanced (`gotoAdvSub()`), and its trigger reads "Advanced › ⟨sub-tab⟩". Analytics: sub-tab views reuse the `Tab View` event with `tab: 'advanced/<sub>'`. Card markup inside the panes is unchanged from v3.5.


#### 4.3.1 Gas Heating Value (Compositional) & Flow — client-side, JIS K 2301:2011

- **Component inputs:** 14 fields `comp-*` — CH₄, C₂H₆, C₃H₈, iC₄H₁₀, nC₄H₁₀, iC₅H₁₂, nC₅H₁₂, nC₆H₁₄⁺, C₂H₄, C₃H₆, H₂, CO₂, N₂, O₂. Mode select `ghv-mode` = Vol% or Mol%. Sum shown in `comp-total`; `comp-warn` flags negative entries or totals off 100 %.
- **Data table:** `gasComps` — per-species MW, HHV, LHV (JIS Table 30), Σb summation factors (`sqrtbi`), specific-gravity factors, MCP factors. LHV values are anchored on CH₄ = 35.818 MJ/Nm³ and must not be recomputed.
- **Calculation chain (mandatory rounding — matches the Excel reference worksheet):**
  1. Vol→Mol: Cmᵢ = ROUND((Cvᵢ/Zᵢ)/Σ(Cv/Z), 4) — mole fractions to **4 d.p.**
  2. Per-component Cmᵢ×√bᵢ rounded to **5 d.p.** before summing.
  3. Z_exact = 1 − (ΣCm√b)² — used for HHV, LHV, SG. Z_rounded = ROUND(Z_exact, 4) — used **only** for ρ_std.
  4. HHV/LHV = ROUND(Σ(Cmᵢ×Hᵢ)/Z_exact, 2); SG = ROUND(Σ(Cmᵢ×Sᵢ)/Z_exact, 3).
  5. WI = ROUND(HHV_2dp/√(SG_3dp), 2) — from the **already-rounded** HHV and SG; always HHV-based per JIS K 2301 §7 regardless of the HHV/LHV display toggle.
  6. ρ_std = 101325·(MW/1000)/(Z_rounded·8.31446262·273.15) kg/Nm³.
  - Constants: R = 8.31446262 J/(mol·K) (CODATA 2018), T_std = 273.15 K, P_std = 101325 Pa, 1 Nm³ = 37.3258 scf.
- **Outputs:** `out-ghv` (+`out-ghv-label`, HHV/LHV toggle `ghv-hv-hhv`/`-lhv`), `out-mw`, `out-sg`, `out-wi`, `out-mcp` (Maximum Combustion Potential incl. inert correction), `out-liq-den` (+`out-liq-den-u`, `out-liq-warn`), opposite-basis fraction grid `opp-frac-grid` (desktop only).
- **LNG liquid density:** ISO 6578:1991 Klosek-McKinley — molar-volume table `ISO6578_VM` (108–120 K, linear T interpolation) and correction factors `ISO6578_K` (k₁/k₂, linear MW interpolation); input `op-liq-temp`; out-of-range temperatures flagged in `out-liq-warn`.
- **Flow conversion:** mass↔vol↔mol both directions (`flow-mass-in`/`-u`, `flow-vol-in`/`-u` → `out-vol-flow`, `out-mass-flow` with unit selects and VOL/MOL, MASS/MOL toggles `flowA-mode-*`, `flowB-mode-*`); actual-vs-standard T/P correction from `op-temp`, `op-press` with `flow-warn` and "Actual" label swap when off-standard.
- **Reference-composition selector (v3.3):** `comp-preset` prefills all 14 component fields from `LNG_PRESETS` (9 entries, one `JSON.parse` literal) and applies each entry's own `basis` to `ghv-mode`. See §4.3.1.1.
- **LNG Cargo Estimator (v3.5):** a separate card directly under this one that consumes ρ_liq / ρ_std / HHV / LHV through the `lastLNGProps` bridge (assigned inside `calcGHV()`, distinct from the test-pinned `lastGHV`) and calls `calcLNGCargo()` at the end of every `calcGHV()`. See §4.3.1.2.

##### 4.3.1.1 LNG reference compositions (v3.3)

- **Dataset:** `LNG_PRESETS` — a single `JSON.parse(\`…\`)` literal, extracted verbatim by `tests/test_lng_presets.py`. Per entry: `id`, `tier`, `basis`, `c` (component percentages, omitted species implicitly zero), `gcv`, `wi`, `src`.
- **Tiers**, which are an honesty boundary and are enforced in CI:
  - `pub` — five origins from **GIIGNL Information Paper No. 1, *Basic Properties of LNG*, Table 1 — Examples of LNG composition** (data: 2018 GIIGNL Annual Report): `au-nws`, `my-bintulu`, `ng-bonny`, `qa-raslaffan`, `tt-atlantic`. Carry the source's own published GCV and Wobbe index.
  - `ref` — `jis-ref`, the app's own JIS K 2301 reference case (Vector 1), carrying its pinned 44.59 / 56.00.
  - `asm` — `us-gulf`, `rich-assoc`, `n2-rich`. Engineering assumptions, **not project data**. `gcv` and `wi` MUST be `null`: a cross-check against an invented figure would present a guess as a citation.
- **Basis:** GIIGNL Table 1 does not state its basis. It is recoverable — on a **mole** basis the JIS chain reproduces the published GCVs to within 0.02 MJ/Nm³; on a volume basis all five rows sit a systematic 0.06 MJ/Nm³ high. The GIIGNL entries are therefore `mol`; `jis-ref` stays `vol`.
- **C4+ split:** GIIGNL lumps butanes into one column; the split to iC₄/nC₄ is taken as 50/50. Sweeping the full range moves HHV and WI by ≤ **0.03 MJ/Nm³** (worst case: Bintulu's WI), inside the ±0.05 cross-check band. The figure is quoted in the on-screen citations and enforced as `C4_SPLIT_MAX_SPREAD`; a test asserts the two agree.
- **Cross-check display:** `lastCompCheck` is assigned from **`hhv_mix`** — the gross value — never `hv_mix`, so the HHV/LHV display toggle cannot disturb a comparison against a published figure. Pass band `LNG_PRESET_TOL` = 0.05 MJ/Nm³.
- **Fidelity:** published rows are reproduced exactly as printed, including the Qatar row's 100.01 % total, which the existing normalization path handles rather than a silent rescale.
- **Attribution lifecycle:** a delegated `input` listener drops `comp-preset` to Custom on any manual `comp-*` edit; `renderLNGPresetInfo()` repaints from inside `calcGHV()` so a share-link or `localStorage` restore repaints its citation. The renderer is `textContent`-only — no `innerHTML`.
- **Elements:** `comp-preset`, `comp-preset-wrap`, `comp-preset-badge`, `comp-preset-src` (+ `-prefix`/`-warn`/`-text`), `comp-preset-check`. The `<option>` list is static and never rebuilt — a restore sets the value before any event fires. Analytics needs no change: the `comp` id prefix already maps to `gas-composition`.
- **i18n:** `advanced.ghv.preset.*` (19 keys) in all 10 dictionaries. `<optgroup>` labels use the v3.3 `data-i18n-label` mechanism, because plain `data-i18n` sets `textContent` and would delete an optgroup's `<option>` children. Preset names and `src` citations stay English, as GT_MODELS does.

##### 4.3.1.2 LNG Cargo Estimator (v3.5)

- **Purpose:** cargo quantities from vessel capacity and the composition above — loaded and delivered liquid volume, mass, standard gas volume and energy on the HHV (custody-transfer) basis with LHV alongside. Card `adv-lng-cargo`, id prefix `lc-` (analytics slug `lng-cargo`).
- **Inputs:** `lc-vessel` (static `<select>`, `""` = manual; 36 `<option>`s grouped by class via `data-i18n-label` optgroups — **never rebuilt**, filters only hide/disable, share-restore rule), `lc-cap` m³ (pre-filled by `selectLNGVessel()`, then user-editable and persisted independently), `lc-fill` % (default 98.5; warns above 98.5, IGC Code Ch. 15), `lc-heel` m³ (default 3,000 since v3.6, was 0), `lc-bor` %/day (default 0.10), `lc-days`. Filter pills `lc-filt-t-*` (class) and `lc-filt-c-*` (containment) drive `lcFilt` → `lcFilterVesselOptions()` + `renderLNGCatalogue()`.
- **Chain (all inputs from `lastLNGProps = { rhoLiq, tLiqK, rhoStd, hhv, lhv, mw }`):** `V_loaded = cap × fill/100`; `V_delivered = V_loaded − heel − V_loaded × BOR/100 × days` (linear screening model, clamped ≥ 0 with `warnNeg`); `m = V × ρ_liq / 1000` t; `V_std = m × 1000 / ρ_std` Nm³; `E = V_std × HHV` (and × LHV). Unit selects `lc-out-mass-u` (t | kt), `lc-out-gas-u` (kNm³ | MMNm³ | MMscf | Bscf — scf via the mandated 37.3258), `lc-out-e-u` (TBtu | MMBtu | GJ | TJ | MWh | GWh, using the named `GJ_PER_MMBTU = 1.055056` and `MJ_PER_MWH = 3600`); the LHV row follows the same select. Chips: energy density MMBtu/t and expansion ratio Nm³ per m³ liquid at 0 °C. Delivered values (`lc-out-*-dv`) appear only when heel or BOG is non-zero. Optional GT cross-link `lc-out-gt`: cargoes per year for the GT Fuel tab's yearly fuel energy (Q × 8760 × availability, in TBtu). `calcGTFuel()` re-runs `calcLNGCargo()` so that chip never goes stale. `lastLNGCargoResult` feeds export §7.
- **Vessel panel** (`lcRenderVessel()`, textContent-only — no innerHTML): Commons photo `assets/vessels/<imo>.jpg` with its `credit` line linked to the Commons file page, or an original schematic `<symbol id="lc-svg-{membrane|moss|ssp|typec}">`; spec chips IMO / delivered year / owner / builder / containment / propulsion / type / capacity; the row's own source link `lc-src`; MarineTraffic and VesselFinder deep-links **by IMO only** (`rel="noopener noreferrer nofollow"`, new tab — ordinary hyperlinks, nothing fetched or embedded).
- **Dataset `LNG_VESSELS`** — ONE `JSON.parse` literal, 36 entries `{id (IMO), name, owner, builder, cap, cont, type, prop, year, src, srcUrl, photo, credit, creditUrl}`; extracted verbatim by `tests/test_lng_cargo.py`. **Provenance by design:** every row cites its own public primary page (owner/operator fleet list, shipbuilder release, class-society register, or Wikipedia as last resort) — never an AIS/spotter site and never the IGU report, whose Appendix 3 (all rights reserved; Rystad Energy data; UK/EU database right) is deliberately **not** reproduced. The IGU World LNG Report 2026 is cited for fleet-level context only (804 active carriers at end-2025). Coverage: all 8 vessel types, all 4 containment systems, all 9 propulsion families, 12 shipyards.
- **Photos:** `assets/vessels/` — Commons-rendered thumbnails (≤ 130 KB) of CC BY-SA / PD photographs only, credited in `assets/vessels/CREDITS.json` and `README.md` (not MIT-licensed; SA attaches to the image, not the app). No MarineTraffic / VesselFinder / ShipSpotting imagery is used or hot-linked. `photo` flags, files and credits are cross-checked by test.
- **Catalogue:** `<details id="lc-cat">` (collapsed by default) with grid `lc-cat-grid` rendered from `LNG_VESSELS` only (escaped; language-sentinel re-render via `lcRenderCatalogueIfStale()`), "Use this vessel" → `selectLNGVessel()`.
- **i18n:** `advanced.lngCargo.*` (89 keys incl. `type.*` / `cont.*` maps `LC_TYPE_KEYS` / `LC_CONT_KEYS` so every key appears literally) in all 10 dictionaries; docs `docs.howto.b102`–`b109`, `docs.theory.b050`–`b052` in all 9 non-English dictionaries.

#### 4.3.2 Pipe Delta Pressure (Darcy-Weisbach) — server-backed

- **Inputs** (`dp-*`): `dp-scale`, `dp-id`/`dp-id-unit`, `dp-len`/`dp-len-unit`, `dp-rough`/`dp-rough-unit`, `dp-elev`/`dp-elev-unit`; vapor `dp-v-flow`/`-u`, `dp-v-den`/`-u`, `dp-v-visc`/`-u`; liquid `dp-l-flow`/`-u`, `dp-l-den`/`-u`, `dp-l-visc`/`-u`; erosion C-factor `dp-cfactor` (default 100).
- **Fittings & valves (v2.8, `dp-fit-*`):** a `<details id="dp-fit-details">` block between the Calculate button and the outputs panel, **collapsed by default with every count at 0**, so an untouched card sends `k_total = 0` and reproduces the v2.7 result exactly. Twelve Crane TP-410 types: `dp-fit-elbow90` (n = 30), `-elbow90lr` (16), `-elbow45` (16), `-return180` (50), `-teerun` (20), `-teebranch` (60), `-gate` (8), `-globe` (340), `-ball` (3), `-checkswing` (100), plus direct-K `-entrance` (K = 0.50) and `-exit` (K = 1.00). Live readouts `dp-fit-ksum`, `dp-fit-nominal`, `dp-fit-ft`. `updateFittingSum()` maps the entered ID to the **nearest nominal size** in the Crane App. A-26 f_T ladder (0.027 at ½" down to 0.012 at 18–24") — tabulated in size bands, so it snaps rather than interpolating — then returns ΣK = Σ qty·(n·f_T or K). The table lives **client-side** so `api/dp_calculator.py` stays standard-library-only; only ΣK crosses the wire.
- **Outputs:** `dp-out-total`(+unit), `dp-out-len` (ΔP per 100 m / 100 ft), `dp-out-vel`(+unit), second row `dp-out-re`/`dp-out-re-regime`, `dp-out-f`, `dp-out-ve`, `dp-out-eratio`, `dp-out-ero-badge` (WITHIN LIMIT < 0.8 ≤ NEAR LIMIT < 1.0 ≤ EXCEEDS Ve), regime cross-link note `dp-out-regime-note`, status badge `dp-regime-badge`. **Third row (v2.8):** `dp-out-dpfit`, `dp-out-leq`, service selector `dp-service`, `dp-out-dpfric100`, `dp-out-vmax`, `dp-out-sizing-badge`, `dp-out-vratio`.
- **Line sizing (v2.8, `renderLineSizing()`):** screens the result against **NORSOK P-001** §6.3.2/§6.4 and Tables 3–4. Gas v_max = min(175·ρ^−0.43, 60) m/s; two-phase v_max = min(183·ρ_mix^−0.5, 25) m/s non-corrosive / 10 m/s corrosive; liquid bands 1–6 m/s carbon steel, 1–7 SS/Ti, **1–3 Cu-Ni** (lowest, because of seawater erosion), 1–6 GRP; pump circuits use ΔP limits of 0.25 / 0.05 / 0.9 bar per 100 m (sub-cooled suction / boiling suction / discharge). Badge thresholds mirror the erosion check (< 0.8 within, < 1.0 near, ≥ 1.0 exceeds), plus a BELOW MIN VELOCITY state for the liquid bands and a PHASE MISMATCH state when the chosen service does not match `phase_key`. The `auto` service maps `phase_key` → gas / liquid-CS / two-phase-non-corrosive. Results are cached in `lastDpResult` so changing the service re-renders without another API call.

  ⚠ **The verdict judges `dpFric` only, never the displayed ΔP/length.** That figure includes static head, which on this card's own default (Δz = 70.711 m) is 98 % of the total — judging against it would flag almost every elevated line as ΔP-oversized. Static head is not a line-sizing criterion.

  ⚠ **NORSOK-only by design.** Widely-circulated GPSA-attributed velocity/ΔP tables could not be verified against primary text during v2.8 research — only secondary aggregators — so they are omitted rather than cited falsely. The API RP 14E erosional check is separate and is not duplicated here.
- **Method (server, §5.1):** phase detection → single vapor / single liquid / two-phase HEM; Darcy-Weisbach friction term + hydrostatic term + **fittings term ΣK·ρv²/2 (v2.8)**; Colebrook-White friction factor (iterative); API RP 14E erosional velocity V_e = 1.2199033·C/√ρ_mix (the exact SI form of V_e = C/√ρ in lb/ft³ units; corrected in v2.8 — §11 #9).

#### 4.3.3 Flow Regime — server-backed visualizer

- **No own inputs** — reads the ΔP card's `dp-*` fields. Button "VISUALIZE FLOW REGIME" → `calcFlowRegime()`.
- **Outputs:** `fr-badge`, `fr-error`, `fr-map-img` (server-rendered PNG data-URI), `fr-3d-wrap` (Three.js canvas), `fr-3d-caption`, `fr-3d-overlay`. The classified regime is cached (`lastFlowRegime`) and cross-linked into the ΔP card.
- **Method (server, §5.3):** inclination θ = asin(Δz/L). |θ| ≥ 30° → vertical map (Hewitt & Roberts type, j_G vs j_L); otherwise horizontal map (Baker type, G_G vs G_L). Simplified piecewise-linear region boundaries — **qualitative orientation only**.
- **3D animation:** regime-specific particle systems (annular film, slug/Taylor bubbles, bubbly, stratified/wavy, churn, mist) in an inclined translucent pipe; speeds scaled from superficial velocities; disposes cleanly on re-run; CDN failure degrades to the 2D map with a notice.

### 4.4 Safety — PRV Sizing (API 520 Part I, 9th Ed.)

- **Mode select** `psv-mode`: gas / steam / liquid_cert / liquid_noncert / twophase. Unit system `psv-units`: USC or SI. `updatePSVMode()` swaps the visible input panel (`psv-inputs-gas`/`-steam`/`-liquid`/`-twophase`) and unit labels.
- **Inputs by mode** (defaults applied client-side when a field is blank):

| Mode | API 520 § | Fields (IDs) | Defaults |
|---|---|---|---|
| Gas | §5.6 | `psv-W`, `psv-M`, `psv-k`, `psv-T`, `psv-Z`, `psv-P1`, `psv-P2`, `psv-Kd`, `psv-Kb`, `psv-Kc` | M 28, k 1.3, Z 1.0, Kd 0.975, Kb 1.0, Kc 1.0 |
| Steam | §5.7 | `psv-W-steam`, `psv-P1-steam`, `psv-Kd-steam`, `psv-Kb-steam`, `psv-Kc-steam`, `psv-KSH`; **v3.0 advisory-only:** `psv-T-steam` (+`-unit`) and the `psv-steam-advisory` strip | Kd 0.975, Kb 1.0, Kc 1.0, KSH 1.0 |

**Steam-mode saturation advisory (v3.0).** `updateSteamAdvisory()` — fired on every `psv-P1-steam`/`psv-T-steam` keystroke and by `updatePSVMode()` on a units toggle — shows T_sat(P1) from IF97 Region 4 (°F in USC, °C in SI), and, when the optional temperature is filled in, either the superheat above T_sat (→ "take KSH from API 520 Table 9") or "saturated, KSH = 1.0". Above the critical pressure it says no saturation temperature exists. **Client-side display only:** `calcPSV()` never reads `psv-T-steam` and the sizing payload is byte-identical to v2.8 (`tests/test_steam_if97.py` pins the reference count of `psv-T-steam` occurrences so wiring it into the payload cannot happen accidentally). KSH itself stays a manual input — Table 9 is API-copyrighted material this application does not reproduce.
| Liquid (certified) | §5.8 | `psv-Q`, `psv-Gl`, `psv-P1-liq`, `psv-P2-liq`, `psv-mu`, `psv-Kd-liq`, `psv-Kw`, `psv-Kc-liq` | Gl 1.0, Kd 0.65, Kw 1.0, Kc 1.0 |
| Liquid (non-certified) | §5.9 | as above + `psv-Ps`, `psv-Kp` | Kd 0.62, Kp 1.0 |
| Two-phase | §5.10 / Annex C | `psv-W-tp`, `psv-vo`, `psv-v9`, `psv-Po`, `psv-Pa`, `psv-Kd-tp`, `psv-Kb-tp`, `psv-Kc-tp`, `psv-Kv-tp` | Kd 0.85, Kb/Kc/Kv 1.0; **Pa ≤ 0 → atmospheric server-side** (14.696 psia / 101.325 kPa — v3.0 PR-1, §11 #5; the UI field's literal `value="0"` therefore now means "atmospheric", the physical minimum for a vented system, not "vacuum") |

- **Outputs:** `psv-out-area` (+`psv-out-area-unit`), `psv-out-orifice` (API 526 letter D–T, or `T+` if larger than T), `psv-out-orifice-area`, `psv-out-details` (mode-specific intermediates: C, Pcf, Pcf/P1, KN, KSH, Kv, Re, ω, η_c, Pc, G), badge `psv-badge`.
- **Methods (server, §5.2):** gas — critical vs subcritical via (2/(k+1))^(k/(k−1)) with C coefficient and F₂ subcritical factor; steam — Napier equation with KN high-pressure correction and KSH superheat factor; liquid — §5.8 two-pass with viscosity correction Kv(Re), §5.9 adds 1.25·Ps effective ΔP and Kp; two-phase — Omega method (ω = 9(v₉/v₀ − 1), η_c from Eq. C.15, critical/subcritical mass flux G, area per C.20/C.21).

### 4.5 Documentation & Support Tabs

Both manuals were **reordered in v3.4 to follow the tab bar rather than the release date** (see §4.5.1). Order is normative: new content is inserted at its position, never appended.

- **How To Use** — Operations manual, 22 illustrated sections in tab order, using CSS wireframe diagrams: global (1 header & tab navigation, 2 mobile navigation & sharing, 3 unit-aware copy) → General (4 standard converter cards, 5 custom modules) → Basic Eng (6 the nine-card overview, 7 Gas Property Estimator, 8 Steam Properties, 9 NPSHa, 10 Compressor) → Advanced › Gas Quality & LNG Cargo (11 gas composition input, 12 LNG reference compositions, 13 operating conditions, 14 physical & combustion properties, 15 mass/volumetric flow, **16 LNG Cargo Estimator (v3.5)**) → Advanced › Hydraulics (17 pipe ΔP, 18 fittings & line sizing, 19 Flow Regime) → Advanced › GT Fuel (20; **moved ahead of Safety in v3.6**, headings 11–19 now carry their sub-tab) → Safety (21 PRV sizing) → Report (22), followed by **`Appendix — Release Notes`** (anchor `howto-releases`): the "What's New" changelogs for v3.6, v3.5, v3.3, v3.2, v3.1, v3.0, v2.8, v2.5 and v2.4, one collapsed `<details>` each (latest `open`), anchors `howto-new36`, `-new35`, `-new33`, `-new32`, `-new31`, `-new30`, `-new28`, `-new25`, `howto-new`. Since v2.5: jump-link strip at the top and section anchors `howto-1`…`howto-22` — **reassigned in v3.4** to match the new order, and 16–21 shifted to 17–22 in v3.5 when Section 16 was inserted; **v3.6 swapped 20↔21** (GT Fuel before Safety) — all ten languages, scripted.
  - §11 (v3.4) is the reference standard for section depth: intro paragraph → ①②③④ workflow strip → a wireframe mockup of the real card (Reference Composition selector, tier badge, GIIGNL citation, cross-check chips, fourteen component boxes, the red 100.01 % Qatar total) → four annotated control callouts → a reproducible worked example. Blocks `docs.howto.b031`–`b033`, `b100`, `b101`.
- **Theory** — Constants and formulas, Parts I–XIII in tab order: Part I real-gas properties for Basic Eng (Papay Z §1.1, LGE viscosity §1.2, sonic velocity §1.3, Joule-Thomson §1.4, anchor `theory-p1`), Part II steam IAPWS-IF97 (§2.1–§2.5, `theory-p2`), Part III pump-suction NPSHa (§3.1–§3.3, `theory-p3`), Part IV compressor head & power (§4.1–§4.3, `theory-p4`), Part V gas compositional analysis per JIS K 2301 with worked examples (§5.1–§5.7, `theory-p5`), Part VI LNG reference compositions (§6.1–§6.5, `theory-p6`), Part VII standard gas density & flow conversions (§7.1–§7.2, `theory-p7`), Part VIII LNG liquid density, Klosek-McKinley Tables B.2/C (§8.1–§8.3, `theory-p8`), **Part IX LNG cargo quantities (v3.5: chain §9.1, units & the lb/scf factor §9.2, loading limit / heel / boil-off §9.3, dataset provenance §9.4, worked example Vector 13 §9.5, `theory-p9`)**, Part X pipe hydraulics for the Advanced › Hydraulics ΔP card (Darcy-Weisbach + Colebrook §10.1, Crane TP-410 fittings §10.2, NORSOK P-001 line sizing §10.3, API RP 14E erosional velocity §10.4, two-phase flow-regime maps §10.5, `theory-p10`), Part XI gas-turbine fuel estimation (§11.1–§11.3, plus §11.4 unit switches added v3.5, `theory-p11`), Part XII PRV sizing (§12.1–§12.7 incl. the API 526 orifice table, `theory-p12`) — **XI and XII swapped in v3.6** to follow the tab order (GT Fuel is now inside Advanced, ahead of Safety), Part XIII data sources & standards (`theory-p13`). Worked-example numbers must match actual calculator output exactly.

#### 4.5.1 Documentation ordering contract (v3.4)

Before v3.4 both tabs were ordered by release: How To Use opened with four stacked *★ New in Version x.x* blocks and scattered the nine Basic Eng cards across sections 4, 13, 16, 17 and 18; Theory printed Part VI before Part V. Three constraints now hold, and CLAUDE.md's *Documentation Tab Structure Rules* restate them for authors:

1. **Sections and Parts follow the tab bar, then the on-screen card order within a tab.** Insert, do not append; renumbering what a new section displaces is part of the change.
2. **No Part may straddle two tabs.** v3.4 split the old Part IV (Hydraulics & Gas Laws) and Part VII (Real-Gas Properties & Fittings) along exactly this line to produce the current Parts I and IX, and moved Data Sources from its mid-document position to the end.
3. **Release changelogs live only in the How To Use appendix.** Theory Part headings carry no version tag; a release adds a `<details>` entry *and* documents the feature in its numbered section.

Renumbering touches five places and only one of them is test-covered: the inline English heading, the same heading in all 9 `docs.*` dictionaries, the jump-link strip (which the translated `docs.*.b001` blocks each carry their own copy of), the `id=` anchors, and prose cross-references. `tests/test_i18n_parity.py` catches a missing *key*, never a stale *number*.
- **Terms of Use** — 8 clauses (reference-only nature, warranty disclaimer, liability, user responsibility, IP, updates, governing law).
- **Privacy Policy** — 10 clauses (zero collection, localStorage-only state, stateless APIs, hosting, report feature, no cookies/tracking, children, rights, contact).
- **Report** — `mailto:` composer for bug reports / feature requests (no server round-trip); includes app-version environment string.

### 4.6 GT Fuel (v3.1; a sub-tab of Advanced since v3.6)

Since v3.6 the third sub-pane of the Advanced tab (`adv-sub-gtfuel`, strip button `advbtn-gtfuel`, `switchAdvSub('gtfuel')`; before v3.6 a top-level tab `btn-gtfuel`/`tab-gtfuel` — `switchTab('gtfuel')` still works and maps onto the sub-tab so pre-v3.6 share links keep landing here) estimating gas-turbine fuel gas consumption from vendor specifications. Client-side only — no API involvement.

- **Gas Turbine Selection** (`gt-select`): vendor select `gt-vendor` (`mhi`/`ge`/`sie`/`manual`), model select `gt-model` (static `<optgroup>` option list — options are hidden/disabled by the vendor filter, never rebuilt, so share-link restore always finds its option; `gtFilterModelOptions()`), cycle select `gt-cycle` (`sc`/`cc`). Selecting a model (`selectGTModel(id)`) pre-fills power and efficiency from the simple-cycle rating or, in `cc` mode, the first published combined-cycle configuration, and paints spec chips `gt-spec-mw/-eff/-hr/-tit/-exh` (chips are re-derived inside `calcGTFuel()` so a state restore repaints them without a selection event).
- **Dataset**: `const GT_MODELS = JSON.parse(\`…\`)` — 31 machines (MHI 15 incl. FT-series aeroderivatives; GE Vernova 10; Siemens Energy 6), fields `{id, vendor, model, hz(0|50|60; 0 = both), cls(HD|AD|IND), scMW, scEff(%-LHV), hrKJ, exhKgS, exhC, titC, cc:[{cfg, mw, eff}], svg(hd|ad|ind), src}`. Every entry cites its source (MHI brochure METP-11GT01E1-E-0 performance tables; GE fact sheets GEA35750/GEA35768 + product pages; Siemens product pages). CI enforces `|hrKJ − 3600/η| ≤ 30 kJ/kWh` per machine and `cc.mw > scMW`, `cc.eff > scEff`.
- **Estimator** (`gt-est`): inputs `gt-power`(+`-u` MW|kW), `gt-eff` (%-LHV), `gt-hv`(+`-u` MJ/Nm³|Btu/scf), `gt-hv-basis` (lhv|hhv; hhv reveals `gt-hhv-ratio`, default 1.108 = 44.59/40.25), `gt-rho` (kg/Nm³), `gt-avail` (%). Physics: `Q = P/η`; `HR = 3600/η` (Btu/kWh ÷ 1.055056); `LHV_used = basis==hhv ? HV/ratio : HV`; `V = 3600·Q/LHV` Nm³/h; `ṁ = V·ρ_std`. Named constants `GT_HV_FACTOR = 0.001055056 * 37.3258` (derived, mirrors the General-tab `HV_FACTOR`), `GT_H_YEAR = 8760`, `GT_H_MONTH = 730`. Outputs `gt-out-q`, `gt-out-hr`, `gt-out-hr-btu`, `gt-out-vol`(+`-u` kNm³/h|Nm³/h|scf/h|MMSCFD), `gt-out-mass`(+`-u` t/h|kg/h|kg/s) with unit-aware copy buttons; totals table `gt-tot-{h,d,m,y}-{vol,mass,q,e}` — hourly row is the instantaneous rate, daily/monthly/yearly rows apply the availability factor. **v3.5 unit switches:** `gt-rho-u` (kg/Nm³ | lb/scf — the lb/scf factor is `RHO_LBSCF_TO_KGNM3 = KG_PER_LB * 37.3258` = 16.9307, because ρ_std is mass per *standard* volume; NOT the 16.0185 actual-density factor used by `mf-rho-u`/`dp-*-den-u`; `gtLastResult.rho` stays kg/Nm³ so `sendGTToMassVol()` is unaffected, and `importGHVToGT()` converts when lb/scf is selected); `gt-out-q-u` (MW-th | MMBtu/h | GJ/h, copy button now `data-unit-src`); `gt-out-vol-u` gains kNm³/d and MMscf/h, `gt-out-mass-u` gains t/d and lb/h; totals-table header selects `gt-tot-vol-u` (Nm³ auto kNm³/MMNm³ | scf auto MMscf/Bscf), `gt-tot-q-u` (new **Fuel energy in** column, Q × h; GJ auto TJ/PJ | MMBtu auto TBtu | MWh auto GWh) and `gt-tot-e-u` (Power sent out; MWh | GJ | MMBtu, same auto-scaling). Defaults reproduce the pre-v3.5 strings byte-for-byte (Vector 11 pins them). Named constants `GJ_PER_MMBTU = 1.055056`, `MJ_PER_MWH = 3600`, `KG_PER_LB = 0.45359237` (all test-pinned). Soft warnings in `gt-warn` (η outside 15–72 %, LHV outside 20–60 MJ/Nm³, CC mode without published CC data).
- **Cross-links**: `importGHVToGT()` reads the module-level `lastGHV = {hhv, lhv, rho}` cached by `calcGHV()` (precedent: `lastFlowRegime`) and warns if the Advanced-tab calculation has not run; `sendGTToMassVol()` writes t/h + kg/m³ into `mf-mass`/`mf-rho`, runs `calcMassVol('mass')` and jumps to `basic-mf`.
- **Catalogue** (`gt-cat`): filter pills (vendor exclusive-select + attribute exclusive-select: all/50 Hz/60 Hz/HD/AD/IND; `hz 0` machines match both frequency filters), grid `gt-cat-grid` rendered by `renderGTCatalogue()` from `GT_MODELS` via `tr('gtfuel.cat.*')` (re-rendered when a translation-sentinel changes — language switches run `recomputeAll()` → `calcGTFuel()` → `gtRenderCatalogueIfStale()`). Thumbnails are three original inline `<symbol>` schematics (`gt-svg-hd/ad/ind`) referenced per card — no vendor imagery (copyright). All figures labelled indicative, ISO conditions, natural gas.
- `calcGTFuel` is in `recomputeAll()` and in the no-stored-state boot branch; all `gt-*` inputs/selects persist via `collectInputs()` and share links automatically.

## 5. Serverless API Contracts

All endpoints: `POST` JSON body, JSON response, `Access-Control-Allow-Origin: *`, OPTIONS preflight supported. Malformed JSON → HTTP 400. Domain errors are returned as HTTP 200 with an error object carrying the **harmonized superset `{error, message, badge, badgeClass}`** on all three endpoints (v3.0 PR-1 — the schemas were divergent before; former Known Issue #6). Error `message` strings remain English prose pending i18n Milestone 4.

### 5.1 `POST /api/dp_calculator`

**Request** (all numeric; `*_mult`/`*_m` are multiply-to-SI factors):

```json
{ "scale": 1, "id": 4, "id_mult": 0.0254, "len": 100, "len_mult": 1,
  "rough": 0.045, "rough_mult": 0.001, "elev": 70.711, "elev_mult": 1,
  "v_flow": 150, "v_flow_m": 0.000277778, "v_den": 10, "v_den_m": 1, "v_visc": 0.012, "v_visc_m": 0.001,
  "l_flow": 7300, "l_flow_m": 0.000277778, "l_den": 500, "l_den_m": 1, "l_visc": 0.12, "l_visc_m": 0.001,
  "cfactor": 100, "k_total": 0 }
```

`k_total` (v2.8, **optional, default 0**) is ΣK for the fittings on the run, summed client-side from the Crane TP-410 table. Omitting it — as every pre-v2.8 payload and share link does — makes `dpFittings` exactly `0.0` and leaves `dpPa` bit-identical to v2.7. Negative values are clamped to 0. The Crane table stays client-side so this endpoint remains standard-library-only.

**Success response:**

```json
{ "error": false,
  "dpPa": 176929.0, "dpFric": 2338.3, "dpStatic": 174590.0, "dpFittings": 0.0,
  "vel": 1.014, "Re": 220110.0, "re_regime": "Turbulent", "re_regime_key": "turbulent",
  "f": 0.01835, "rho_mix": 251.69, "v_ero": 7.689, "ero_ratio": 0.132, "cfactor": 100.0,
  "k_total": 0.0, "L_eq": 0.0, "L": 100.0, "L_eff": 100.0,
  "badge": "Two-Phase (HEM)", "phase_key": "twophase", "badgeClass": "…tailwind classes…" }
```

(Values shown are the reference case; `re_regime` ∈ Laminar < 2300 ≤ Transitional < 4000 ≤ Turbulent.)

**v2.8 additions — all additive; no field was renamed or removed.**

| Field | Meaning |
|---|---|
| `dpFittings` | ΔP across the fittings, ΣK·ρv²/2 [Pa]. Included in `dpPa`; `0.0` when `k_total` is absent or ≤ 0 |
| `k_total` | ΣK as received (clamped to ≥ 0), echoed for traceability |
| `L_eq` | Equivalent straight length ΣK·D/f at the **actual flowing** friction factor [m]. Reported for information only — `dpFittings` is computed directly from ΣK and never round-trips through `L_eq` |
| `L_eff` | `L + L_eq` |
| `phase_key` | `vapor` | `liquid` | `twophase` — machine-readable companion to `badge` |
| `re_regime_key` | `laminar` | `transitional` | `turbulent` — companion to `re_regime` |

⚠ **`L` deliberately remains the STRAIGHT-pipe length.** The client divides by it to render ΔP per unit length; returning `L + L_eq` there would silently turn that display into "per effective metre", which is not what a piping engineer expects. `L_eff` carries the fittings-inclusive figure.

`phase_key` and `re_regime_key` follow the i18n Milestone 4 pattern that `flowregime.py` already established with `regime_key` (§5.3). They exist because the frontend previously branched on the English string `badge.indexOf('Two-Phase')`, which would silently stop firing in all 10 languages the moment the badge is localized.

**Error response:** `{ "error": true, "message": "…", "badge": "…", "badgeClass": "…" }` — the full superset since v3.0 PR-1 (`message` was missing before — former Known Issue #6). Validation guards (v3.0 PR-1): zero/negative density or viscosity on a *flowing* phase → structured `Invalid Input` error instead of an uncaught 500 (former #2); a **present** `cfactor` ≤ 0 or non-finite → structured error, while an **absent** `cfactor` still defaults to 100 for pre-v2.4 payload compatibility (former #3 — the old code silently mapped `cfactor: 0` to 100 and accepted negatives, which produced a green WITHIN LIMIT badge on a negative V_e). The same PR's adversarial review closed the wider uncaught-500 class: negative phase flows (could zero the HEM denominator *exactly*; UI-reachable — the inputs have no `min` attribute), negative roughness (Colebrook log of a negative), non-numeric field values (the `float()` coercions are guarded), NaN/Infinity in any extracted field (an `isfinite` sweep — NaN passes every ordered comparison and produces RFC-8259-invalid `NaN` tokens a browser cannot parse), non-object JSON bodies (`[1,2,3]` → structured 400), and a subnormal-tiny pipe ID whose area underflows to 0.

**Method:** HEM two-phase mixing (x = W_v/W_t; 1/ρ = x/ρ_v + (1−x)/ρ_l; μ = x·μ_v + (1−x)·μ_l), Darcy-Weisbach ΔP_fric = f·(L/D)·ρ·v²/2 with iterative Colebrook-White f (laminar 64/Re below Re 2300), ΔP_static = ρ·g·Δz (g = 9.81), **ΔP_fittings = ΣK·ρ·v²/2 (v2.8)**, API RP 14E V_e = 1.2199033·C/√ρ — an exact unit conversion, 0.3048·√16.0184634 (corrected in v2.8, see §11 #9). ΔP_total = ΔP_fric + ΔP_static + ΔP_fittings.

### 5.2 `POST /api/psv_calculator`

**Request:** `{ "mode": "gas|steam|liquid_cert|liquid_noncert|twophase", "units": "USC|SI", …mode fields… }` (field lists and defaults in §4.4; USC: lb/h, psia, °R, gpm; SI: kg/h, kPaa, K, L/min).

**Success response (common):**

```json
{ "error": false, "area": 1234.5678, "area_unit": "mm²",
  "orifice": "J", "orifice_area": 830.0, "orifice_unit": "mm²",
  "flow_regime": "…", "badge": "…", "badgeClass": "…" }
```

plus mode-specific intermediates — gas: `C`, `Pcf`, `critical_ratio`; steam: `KN`, `KSH`; liquid: `Kv`, `Re`; two-phase: `omega`, `eta_c`, `Pc`, `G`. Orifice selection: smallest API 526 letter (D–T) whose area ≥ required; `T+` if none.

**Error response:** `{ "error": true, "message": "…", "badge": "…", "badgeClass": "…" }` — the full superset since v3.0 PR-1 (badge fields were missing before — former Known Issue #6; they are added at the handler's single exit point, not at the 14 individual return sites). Validation guards (v3.0 PR-1): gas mode rejects `k ≤ 1` with a specific message (former #4 — `k = 1` used to surface the literal Python text "float division by zero", and `k < 1` silently computed a meaningless area; note API 520's *k-unknown* convention C = 315 corresponds to the k → 1⁺ limit — a user wanting that conservatism can enter k marginally above 1, since C(k) is monotonically increasing); unexpected exceptions return a fixed generic message instead of `str(e)`; two-phase mode replaces an omitted/zero back-pressure `Pa` with atmospheric (former #5, §4.4) and rejects `Po ≤ Pa` with a specific message naming the vacuum-discharge escape hatch (enter a small positive `Pa` explicitly); every existing `x <= 0` guard was flipped to `not (x > 0)` polarity so NaN is rejected rather than admitted (NaN fails every ordered comparison); non-object JSON bodies → structured 400. The subcritical mass-flux bracket was also corrected in this PR — see #12.

### 5.3 `POST /api/flowregime`

**Request:** same geometry/phase payload as §5.1 (cfactor ignored).

**Success response:**

```json
{ "error": false, "image": "data:image/png;base64,…",
  "regime": "Churn / Slug Flow", "regime_key": "churn_slug",
  "map_type": "vertical", "theta_deg": 45.0,
  "jG": 0.514, "jL": 0.500, "GG": 5.14, "GL": 250.0,
  "v_mix": 1.014, "lambda_l": 0.493, "clamped": false,
  "badge": "…", "badgeClass": "…" }
```

**Error response:** `{ "error": true, "message": "…", "badge": "…", "badgeClass": "…" }`; hard render failures → HTTP 500.

**Method:** θ = asin(Δz/L); |θ| ≥ 30° → vertical Hewitt & Roberts-type map in (j_G, j_L); else horizontal Baker-type map in (G_G, G_L); point-in-polygon classification against simplified log-space regions; operating point clamped to map limits when out of range (`clamped: true`). Map rendered server-side (matplotlib Agg + seaborn, dark palette matched to the app).

## 6. Client State & Share Links

- **Autosave:** every `input`/`change` inside `<main>` schedules a debounced (400 ms) save of the full state to `localStorage['og_ui_state_v24']`.
- **State shape** (v2, since v2.8): `{ "v": 2, "inputs": { "<element-id>": "<value>", … }, "mods": [{ "id", "t", "u1", "u2", "f" }, …], "hv": "hhv|lhv", "fa": "vol|mol", "fb": "mass|mol", "p1": "abs|gau", "p2": "abs|gau", "tab": "<tab-name>", "lang": "<language-code>" }` — `inputs` covers every `input`/`select`/`textarea` with an id inside `<main>`, **except `report-*`** (v2.8, see below). `lang` was added in v2.6 (purely additive). `v` was emitted as `1` from v2.4 onward but never read by anything; **v2 is the first version that carries meaning.**
- **`mods` (v2.8)** carries the custom-module *definitions*. Their *values* were always captured by `collectInputs()` — the cards live inside `<main>` and carry ids — so v1 links have always shipped orphan `mod-<ts>-in1` keys with nothing to fill on the far side. Backward compatibility runs both ways: a v1 payload has no `mods`, and the guard is `Array.isArray(shared.mods)` rather than a truthiness test, because `applyState()` has **no try/catch** and an unguarded `.forEach` would throw and silently kill the entire restore. A v2 payload opened by a stale cached v1 client degrades gracefully — unknown keys are ignored — so no coordinated rollout is needed.
- **Share link:** `copyShareLink()` base64-encodes the same state object into `<origin><path>#s=<base64>`; entirely client-side.
- **Accepted link forms (2026-08-16):** `decodeShareState()` reads the payload from **either** the
  fragment (`#s=`) or the query string (`?s=`). The fragment wins when both are present, so a stray
  `?s=` left by a redirect cannot override what the user pasted. A `normalizeShareB64()` pass undoes
  the manglings such links pick up in transit — percent-encoding, `+`→space (a query string reads
  `+` as a space), and base64url `-`/`_` — each of which otherwise makes `atob()` throw, restoring
  nothing with no error shown. **Why `?s=` exists:** LinkedIn strips everything after the `#` when
  it auto-links a URL in a post or comment, so a fragment link renders correctly, looks clickable
  and restores nothing; Teams/Outlook/Slack rewriting mangles long fragments the same way.
- **PRIVACY INVARIANT — read `?s=`, never generate it.** `copyShareLink()` emits `#s=` and must
  continue to. A fragment is never transmitted to the server; a query string travels in the request
  line and lands in access logs. Generating `?s=` would put every user's engineering inputs into
  Vercel's logs, contradicting the Privacy Policy and the "records *that* a tool was used, never
  *what* was entered" boundary that §14 holds analytics to. Anyone hand-authoring a `?s=` link (the
  LinkedIn campaign does) is making that trade knowingly for a link that must survive posting.
  `tests/test_share_state.py` pins the asymmetry and the pin is mutation-tested.
- **Restore precedence on load:** share-link payload (hash, then query) → localStorage → defaults. Restore reapplies inputs, the five toggle modes, and recomputes client-side cards. **Only share links** additionally open on their saved tab (so a shared PSV case lands on Safety); normal visits always land on the General tab (v2.5.1 — localStorage tab restore was removed as a landing-page annoyance, though `tab` is still recorded in the state object for share links). **Language follows a different policy** (v2.6): a returning visitor's saved `og_lang` auto-restores on a normal visit (unlike `tab`), and a share link's `lang` field takes priority over even that saved preference — see §12.
- **Custom modules** persist in `localStorage['og_custom_modules']` and, **since v2.8, travel in share links** (§6.1). The top-level parse of that key is wrapped in `try`/`catch` as of v2.8 — it sits at script top level, so an unparseable value previously threw and left *every function declared after it* undefined, including `collectState`, `copyShareLink`, `exportReport` and `calcPSV`.
- **`report-*` fields are excluded from state (v2.8).** The bug-report form lives inside `<main>`, so the reporter's name and free-text description were being base64-encoded into every share link and written to `localStorage`. None of it is engineering state. It is now used only when the user opens their mail client. Disclosed in the Privacy Policy tab.
- **Share-link length warning (v2.8).** A stock link is already ~4.6 kB (197 input keys as of the v3.0 cycle → ~3,400 JSON bytes → 4,627 URL chars, measured) and each custom module adds ~60–120 bytes. Browsers cope — the fragment never reaches the server — but QR generators, Outlook/Teams link rewriting and several chat clients truncate around 2,000 characters, producing a link that looks fine and restores nothing. Past `SHARE_URL_WARN_LEN` (2,000) the copy toast says so. It warns rather than blocks: the link is still valid and the user knows where it is going.

### 6.1 Share-link module import — security model (v2.8)

`createCard()` interpolates `m.t` / `m.u1` / `m.u2` directly into `innerHTML`, and `m.id` into **two inline `onclick` attribute strings**. While those values could only originate from the user's own modal, the worst case was self-XSS. **The moment a share link can supply them, that template becomes a stored-XSS-via-URL sink** — an attacker-crafted `#s=` payload executing in the recipient's page. Everything arriving from a link therefore passes `sanitizeSharedModule()` at a single import boundary before it can reach `createCard()`.

| Control | Rationale |
|---|---|
| Escape `&`, `<`, `>`, `"`, `'` in `t`/`u1`/`u2` | The first three for the `innerHTML` sink, the last two because the values also reach inline `onclick` attribute strings. Escaping at *import* is correct and safe: `innerHTML` decodes the entities, so a legitimate `Oil & Gas` still displays as `Oil & Gas` |
| **Regenerate the id** | Ids are `mod-<timestamp>` — unique per user but **not globally**. A shared module can collide with one the recipient already has, giving duplicate DOM ids, making `getElementById` inside `createCard` grab the wrong node, and making TERMINATE delete both cards |
| Remap `mod-<sender-id>-in1/-in2` onto the new id | Otherwise the imported card's values land nowhere |
| Reject non-finite or zero `f` | Zero divides by zero on the reverse conversion |
| `trim()` before slicing, reject empty titles | A whitespace-only title is truthy and would create a blank, unidentifiable card |
| Clamp text to `MOD_MAX_TEXT_LEN` (40) | Titles and units are chips in a card, not prose |
| Cap imports at `MOD_MAX_SHARED` (20) per link | Bounds how far one link can alter a workspace |

**Verified against hostile payloads in a real browser engine** — an `onerror` image in the title, a `<script>` breakout in a unit label, and an attribute breakout in the other: no nodes injected, no handler fired, the text rendered inert, and ten malformed entries (null, string, number, empty object, missing/zero/NaN factor, empty and whitespace-only titles) were all rejected without throwing.

**Persistence policy (maintainer's decision, v2.8):** imported modules are **kept** — written to `og_custom_modules` so they survive a reload and remain usable — and a toast names the count. Disclosed in the Privacy Policy tab, which also documents the `report-*` exclusion.

## 7. Export Report

`exportReport()` builds a standalone printable HTML document (report header with version + timestamp, sections for GHV & composition, ΔP, Flow Regime, PRV, Basic Eng values and — v3.1, only when a valid estimate exists — section 6 GT Fuel, plus the reference-only disclaimer) and opens it in a new window for the browser's Save-as-PDF. Since v2.5, if the pop-up is blocked the same HTML is downloaded as `og-converter-report.html` instead, with a toast explaining the fallback.

## 8. Calculation Rules Summary (normative)

The JIS K 2301 rounding chain in §4.3.1 is **normative** and matches CLAUDE.md exactly; any deviation breaks regulatory traceability. Governing references:

| Standard | Scope |
|---|---|
| JIS K 2301:2011 | Calorific value, density, SG, Wobbe index from composition (incl. Table 30 LHV values) |
| ISO 6578:1991 | LNG liquid density — Klosek-McKinley, Tables B.2 and C |
| API 520 Part I, 9th Ed. (2014) | PRV sizing; API 526 orifice areas D–T |
| API RP 14E, 5th Ed. (1991) | Erosional-velocity screening V_e = C/√ρ |
| Papay (1968) + Standing-Katz pseudo-criticals | Gas Z-factor; validity 0 < Pr ≤ 15, 1.05 ≤ Tr ≤ 3.0 |
| Colebrook & White (1939) | Turbulent friction factor (implicit) |
| Hewitt & Roberts (1969) · Baker (1954) | Flow-regime maps (simplified, indicative) |
| CODATA 2018 | R = 8.31446262 J/(mol·K) |

## 9. Reference Test Vectors — MUST REPRODUCE EXACTLY

**Vector 1 — JIS composition** (CH₄ 89, C₂H₆ 7, C₃H₈ 2.5, iC₄ 0.7, nC₄ 0.5, N₂ 0.3 vol%):

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

**Vector 2 — Pipe ΔP default case** (ID = 4 in, L = 100 m, Δz = 70.711 m, vapor 150 kg/h @ 10 kg/m³ / 0.012 cP, liquid 7,300 kg/h @ 500 kg/m³ / 0.12 cP, C = 100): ΔP_total ≈ **176.9 kPa** (friction ≈ 2.34 kPa + static ≈ 174.6 kPa), vel ≈ 1.014 m/s, Re ≈ **2.20×10⁵** (Turbulent), f ≈ **0.0184**, ρ_mix ≈ 251.7 kg/m³, V_e ≈ **7.69 m/s**, v/V_e ≈ 0.13 → WITHIN LIMIT. *(v2.8: V_e was 7.72 until the RP 14E SI constant was corrected — §11 #9. The verdict is unchanged.)*

**Vector 3 — Flow Regime default case** (same inputs): **Churn / Slug Flow**, θ = **+45.0°**, vertical map, j_G ≈ 0.514 m/s, j_L ≈ 0.500 m/s.

**Vector 4 — PRV sizing (added and approved in v2.8).** Five USC cases, one per API 520 Part I sizing mode. Inputs are the Safety card's own placeholder values — with one deliberate exception: the §5.10 two-phase case uses **W = 238,715 lb/h, half the card's 477,430 placeholder**, chosen during review so the required area lands on a real API 526 orifice (T) instead of over-ranging to `T+`. The over-range path is covered separately by `test_oversized_requirement_is_flagged_not_silently_capped`. Enforced by `tests/test_psv_calculator.py`.

| Mode | Inputs | Required area | Orifice | Intermediates |
|---|---|---|---|---|
| **§5.6 Gas** | W 53,500 lb/h · M 51 · k 1.3 · T 627 °R · Z 1.0 · P₁ 97.2 psia · P₂ 0 · K_d 0.975 | **5.7047 in²** | **P** (6.38 in²) | C 346.9764 · critical ratio 0.5457 · P_cf 53.045 psia · Critical Flow |
| **§5.7 Steam** | W 153,500 lb/h · P₁ 1,774.7 psia · K_d 0.975 · K_SH 1.0 | **1.7030 in²** | **K** (1.838 in²) | K_N 1.0115 (Napier correction active above 1,500 psia) |
| **§5.8 Liquid, certified** | Q 1,800 gal/min · G_l 0.9 · μ 0 · P₁ 275 psig · P₂ 0 · K_d 0.65 | **4.1690 in²** | **N** (4.34 in²) | K_v 1.0 · Re `None` (correction skipped when μ = 0) |
| **§5.9 Liquid, non-certified** | Q 1,800 gal/min · G_l 0.9 · μ 0 · P_s 250 psig · P₂ 0 · K_d 0.62 · K_p 1.0 | **4.1001 in²** | **N** (4.34 in²) | sizes on set pressure P_s rather than P₁ |
| **§5.10 Two-phase (Omega)** | W 238,715 lb/h · v_o 0.3116 · v₉ 0.3629 ft³/lb · P_o 80.7 psia · P_a 0 · K_d 0.85 | **19.0114 in²** | **T** (26.00 in²) | ω 1.4817 · η_c 0.6564 · **P_c 52.971 psia** · G 590.891 · Two-Phase Critical |

Hand-checks recorded in the test module's docstring: the gas case reproduces from C = 520·√(k(2/(k+1))^((k+1)/(k−1))) and the two-phase case from ω = 9(v₉/v_o − 1), both to 4 d.p.

**Vector 5 — Papay Z-Factor (added v2.8).** The Z-Factor Estimator had no documented vector before v2.8, which made the `papayZ()` extraction unverifiable. Inputs are the card's own placeholders: **SG 0.65, P 2,000 psi, T 150 °F**.

| Quantity | Expected |
|---|---|
| P_pc / T_pc | 670.1290 psia / 365.1100 °R |
| P_r / T_r | 2.984500 / 1.669826 |
| **Z (displayed, 4 d.p.)** | **0.8646** (0.864584 exact) |
| `z-warn` | hidden (inside the validity envelope) |

**Vector 6 — Gas Property Estimator (added v2.8).** Same state as Vector 5 plus **k = 1.3** (the card default, matching the PRV card's isentropic-exponent default). Every value below was reproduced independently in Python and in a real browser engine.

| Quantity | Expected |
|---|---|
| M = SG × 28.9647 | 18.827055 g/mol |
| T_R / T_K | 609.67 °R / 338.7056 K |
| Z | 0.864584 → displayed **0.8646** |
| ρ = PM/(ZRT) | 6.656512 lb/ft³ = **0.1066271 g/cm³** |
| LGE K / X / Y | 123.356242 / 5.255889 / 1.278090 |
| **μ_g** | **0.016663 cP** = 16.6635 µPa·s |
| **c** | **410.0269 m/s** = 1,345.23 ft/s |
| ∂Z/∂T (central difference, h = 0.5 °R) | 1.707785 × 10⁻³ K⁻¹ |
| C_p,molar = kR/(k−1) | 36.0293 J/(mol·K) |
| **μ_JT** | **0.3279 K/bar** = 0.04069 °F/psi |

Cross-check worth keeping: at Z = 1 the sonic velocity would be 441.0 m/s, **7.5 % higher** — that gap is why the card shows Z alongside c.

**Vector 7 — Crane fittings (added v2.8).** Vector 2's hydraulics with a representative fitting set on the 4-inch line: **4× 90° standard elbow, 1× gate valve (full open), 1× swing check valve, 1× sharp-edged entrance, 1× pipe exit.**

| Step | Expected |
|---|---|
| Nominal size → f_T (Crane App. A-26) | 4" → **0.017** |
| 4× 90° elbow, K = 30·f_T | 4 × 0.5100 = 2.0400 |
| Gate valve, K = 8·f_T | 0.1360 |
| Swing check, K = 100·f_T | 1.7000 |
| Entrance (direct K) / Exit (direct K) | 0.5000 / 1.0000 |
| **ΣK** | **5.3760** |
| Velocity head ρv²/2 | 129.4370 Pa |
| **ΔP_fittings = ΣK·ρv²/2** | **695.8532 Pa = 0.69585 kPa** |
| **L_eq = ΣK·D/f** (f = 0.0183544 flowing) | **29.75863 m** |
| L_eff | 129.75863 m |
| **ΔP_total** | **177.6247 kPa** |

**Self-consistency check built into the suite:** re-running the *straight* pipe at L = 129.75863 m with no fittings raises ΔP_fric from 2338.3238 Pa to 3034.1770 Pa — a difference of **695.8532 Pa**, identical to the direct ΣK·ρv²/2 result. The two methods agree by construction because L_eq = ΣK·D/f; if they ever diverge, one has been reimplemented incorrectly.

**Why the K method is primary.** A fitting's loss is a fixed number of velocity heads — a property of its geometry. The equivalent length that produces that loss depends on the pipe's *actual* friction factor. The Crane L/D shortcut (L_eq = n·D) implicitly assumes f = f_T, i.e. that the pipe is in fully-rough flow, which is false for most process lines including this one (Re = 2.20×10⁵, f = 0.01835 > f_T = 0.017). For this fitting set the shortcut gives Σn·D = 228 × 0.1016 = 23.16 m, **22 % below** the K-method's 29.76 m — and entrance and exit have no n at all, so they cannot appear in it.

⚠ **Gradual reducers are deliberately absent** from the fitting list. Crane's Formula 1–4 coefficients could not be verified against a primary source during v2.8 research (the Crane PDF and its mirrors were inaccessible). Publishing an unverified constant is the exact failure mode this project's traceability rules exist to prevent. Sudden contraction/enlargement are textbook-citable and could be added; gradual reducers wait for a verified copy of TP-410.

**Vector 8 — Steam (IAPWS-IF97, added v3.0).** Two layers. First, the **coefficient layer**: the 44 official verification values (Release Tables 5, 15, 35, 36 + the B23 point, all to 9 significant figures) are enforced by `tests/test_steam_if97.py` against the extracted `IF97` literal — they are the Release's own numbers, not this project's, and are not repeated here. Second, the **display layer**, the worked example printed in How To Use §16 and Theory §8.4, which the browser must reproduce exactly as formatted (`formatValue`, 5 decimals):

| Input 4 MPa (abs) | Expected |
|---|---|
| **T = 300 °C** | Superheated steam — Region 2, superheat **49.64248** K |
| ρ / h / s | **16.98717** kg/m³ / **2,961.65148** kJ/kg / **6.36383** kJ/(kg·K) |
| c_p / w | **2.81995** kJ/(kg·K) / **550.23169** m/s |
| T_sat / h_fg | **250.35752** °C / **1,713.4713** kJ/kg (h_f **1,087.42602** · h_g **2,800.89732**) |
| **T = 150 °C** | Compressed liquid — Region 1: ρ **918.99612** kg/m³, h **634.43339** kJ/kg, s **1.83804** kJ/(kg·K) |
| **PSV advisory** (steam mode, USC) | P1 = 1,774.7 psia → T_sat = **619.11105** °F (via the app's psia→MPa factor 0.006894757 — the 13-digit factor gives …06 in the 5th decimal; the displayed value follows the shipped factor) |

**Vector 9 — NPSHa (added v3.0).** Water at 80 °C in an open tank (101.325 kPa abs), liquid level +3 m above the impeller centerline, 1.2 m suction friction. The water helper quantizes its fills to 8 significant figures into the input fields — the vector is defined through that exact path (`tests/test_npsh.py`):

| Step | Expected |
|---|---|
| Helper fill @ 80 °C | P_v = **47.41472** kPa · ρ = **971.77879** kg/m³ (IF97 R4/R1) |
| Pressure head (101,325 − 47,414.72)/(ρ·9.80665) | **5.65697** m |
| **NPSHa** = 5.65697 + 3 − 1.2 | **7.45697 m = 24.46511 ft** |
| Flashing case: 95 °C, z = −2 m, h_f = 0.8 m | fill 84.608938 kPa / 961.88733 kg/m³ → head 1.7721 m → **NPSHa = −1.0279 m** + flashing warning |

**Vector 10 — Compressor head/power (added v3.0).** SG 0.65 gas, 40 → 80 bar a (r = 2 exactly), T₁ = 30 °C, k = 1.3, η_p = 75 %, 100 t/h. Both states sit inside Papay validity, so the vector exercises the no-warning path (`tests/test_compressor.py`):

| Step | Expected |
|---|---|
| m = (k−1)/(k·η_p) → n | 0.30769 → n = **1.4444** |
| T₂ = T₁·r^m | 675.39010 °R = **102.06672 °C** |
| Z₁ (Pr 0.86573, Tr 1.49454) / Z₂ at T₂ estimate (Pr 1.73146, Tr 1.84983) / Z_avg | **0.9083 / 0.9322 / 0.9203** (0.9083271 / 0.9321836 / 0.92025535 to 8 s.f.) |
| **H_poly** (Z_avg·R·T₁/M · (r^m−1)/m, R·T₁/M = 133,878.05 J/kg) | **95.18714 kJ/kg** (31,845.10172 ft·lbf/lbm) |
| H_is (m_s = (k−1)/k) | **92.60625** kJ/kg → implied η_s = 0.75 × 92.60625/95.18714 = **72.97 %** |
| Gas power W = ṁ·H_poly/η_p @ 27.77778 kg/s | **3,525.44967 kW** (3.52545 MW · 4,727.70592 hp) |

**Vector 11 — GT fuel estimator (added v3.1).** M701JAC (448) one-click prefill + Vector 1's reference gas: P = 448 MW, η = 44.0 %-LHV, LHV = 40.25 MJ/Nm³, ρ_std = 0.8193 kg/Nm³, availability 92 % (`tests/test_gt_fuel.py`):

| Step | Expected (display strings) |
|---|---|
| Q_fuel = P/η | **1,018.18 MW-th** |
| HR = 3600/η | **8,182 kJ/kWh** = **7,755 Btu/kWh** — reproduces MHI's published heat rate exactly |
| V = 3600·Q/LHV | 91,067 Nm³/h → **91.07 kNm³/h**, **81.58 MMSCFD** (×37.3258×24/10⁶) |
| ṁ = V·ρ_std | 74,611 kg/h → **74.61 t/h** |
| Monthly (730 h × 92 %) | **61.16 MMNm³** |
| Yearly (8,760 h × 92 %) | **733.93 MMNm³** · **601,308 t** · 3,610.5 GWh sent out |
| LHV in Btu/scf | 40.25 ÷ (0.001055056 × 37.3258) = **1,022.1** (1 MJ/Nm³ = 25.393 Btu/scf) |

**Vector 12 — LNG reference compositions (added v3.3).** The five GIIGNL Table 1 origins, run through the JIS K 2301 chain on a mole basis and compared with the *source's own* published figures. These are external reference points: they were not derived from this application, so they verify the engine as well as the dataset (`tests/test_lng_presets.py`):

| Origin (mol %) | GCV calc / published | WI calc / published |
|---|---|---|
| Australia NWS | **45.32** / 45.32 | **56.52** / 56.53 |
| Malaysia Bintulu | **43.69** / 43.67 | **55.58** / 55.59 |
| Nigeria Bonny | **43.41** / 43.41 | **55.49** / 55.50 |
| Qatar Ras Laffan | **43.43** / 43.43 | **55.38** / 55.40 |
| Trinidad Point Fortin | **41.05** / 41.05 | **54.23** / 54.23 |

Largest deviation across all ten comparisons: **0.02 MJ/Nm³**, against a pass band of ±0.05. The `jis-ref` preset reproduces Vector 1 exactly (44.59 / 56.00) on its volume basis.

**Vector 13 — LNG cargo quantities (added v3.5).** Australia — North West Shelf preset (mol %) at T_LNG = −160 °C, vessel LNG Endeavour 174,000 m³, loading limit 98.5 % (`tests/test_lng_cargo.py`). Inputs from the composition card: ρ_liq **467.32** kg/m³ (ISO 6578; the card uses the unrounded 467.3168), ρ_std **0.83108** kg/Nm³, HHV **45.32**, LHV **40.93** MJ/Nm³.

| Step | Expected (display strings) |
|---|---|
| V_loaded = 174,000 × 0.985 | **171,390 m³** |
| m = V × ρ_liq | **80,093 t** |
| V_std = m ÷ ρ_std | **96,373 kNm³** = 96.373 MMNm³ = **3,597 MMscf** = 3.597 Bscf |
| E_HHV = V_std × HHV | 4,368 TJ = **4.140 TBtu** (÷ 1.055056 GJ/MMBtu ÷ 10⁶) = 1,213.2 GWh |
| E_LHV | **3.739 TBtu** |
| Energy density / expansion | **51.69 MMBtu/t** · **562** Nm³ per m³ liquid (0 °C) |
| Delivered: heel 3,000 m³, BOR 0.10 %/day × 15 d | 165,819 m³ → 77,490 t → **4.005 TBtu** |
| GT cross-link (Vector 11 plant, 28.00 TBtu/yr) | ≈ **6.8** cargoes / year |

Also pinned from Vector 11 through the v3.5 unit switches: 733.93 MMNm³ = **27.394 Bscf**; fuel energy in **28.00 TBtu** (29.54 PJ); power sent out **12.32 TBtu** = **13.00 PJ**; fuel-energy input **3,474.2 MMBtu/h** = 3,665.5 GJ/h; ρ_std 0.8193 kg/Nm³ = **0.04839 lb/scf** (16.9307; the 16.0185 trap would read 0.05115).

All vectors are enforced automatically on every push and pull request, except Vector 1 and the display layers of Vectors 8–11 and 13 (browser-side JavaScript) — see §13.

## 10. Deployment

- **Production:** Vercel, auto-deploy on push to `main`. Zero-config: static `index.html` + auto-provisioned `api/` Python functions.
- **Dependencies:** `requirements.txt` applies to `flowregime.py` only (numpy ≥ 1.26, matplotlib ≥ 3.8, seaborn ≥ 0.13). The other two endpoints must remain standard-library-only.
- **Local:** `vercel dev` → <http://localhost:3000>.
- **Licence (2026-08-16):** **MIT**, in `LICENSE` at the repo root. The repository had been public but unlicensed while in-app Terms §6 prohibited redistribution and commercial use; the two were contradictory and were reconciled together. Three artefacts must stay in agreement — `LICENSE`, the README licence section, and Terms §6 (`docs.terms.b008`) in inline English plus all 9 dictionaries. The licence covers this project's own code, design and documentation only; the `LICENSE` file's third-party section (engineering standards, the GIIGNL LNG composition data, the vendor gas-turbine specifications) records what it does **not** grant rights in, and must not be dropped.

## 11. Known Issues Register

| # | Issue | Location | Status |
|---|---|---|---|
| 1 | ~~Two-phase PRV result line displays Pc computed from back-pressure `Pa` instead of relieving pressure `Po`~~ | `api/psv_calculator.py` | **FIXED v2.8.** `Pc_display` now uses `Po_input × η_c`, matching the internal `Pc` that drives the critical/subcritical decision. Sizing was never affected — only the displayed value, which read exactly `0.0` whenever `Pa` was left at its default (the default). On Vector 4's two-phase case it now reads **52.971 psia** instead of 0.0. Guarded by `test_twophase_reports_pc_from_relieving_pressure` and `test_twophase_pc_is_independent_of_back_pressure` |
| 2 | ~~ΔP API: zero viscosity/density inputs can raise an uncaught exception → HTTP 500 without CORS/JSON, surfacing as a generic "API Connection Failed" badge~~ | `api/dp_calculator.py` | **FIXED v3.0 (PR-1).** A guard after the No-Flow check rejects zero/negative density or viscosity on any *flowing* phase with a structured `Invalid Input` error; a vapor-only payload does not require liquid properties (and vice versa). The old defect-locking test `test_zero_viscosity_still_raises` was flipped to `test_zero_viscosity_returns_structured_error`, per its own docstring |
| 3 | ~~ΔP API accepts a negative erosion C-factor (produces a negative V_e with a green WITHIN LIMIT badge); `cfactor: 0` silently becomes 100~~ | `api/dp_calculator.py` | **FIXED v3.0 (PR-1).** The `or 100.0` was removed: a present `cfactor` ≤ 0 (or non-finite) is now a structured error; an absent `cfactor` still defaults to 100 so pre-v2.4 payloads and share links reproduce Vector 2. The UI cannot send 0 (index.html maps blank/zero to 100 client-side), so this only tightens the direct-API contract. Guarded by three new tests incl. `test_cfactor_default_when_absent` |
| 4 | ~~PRV gas mode: k ≤ 1 raises a division error that surfaces as a raw Python message; generic `str(e)` leaks internals~~ | `api/psv_calculator.py` | **FIXED v3.0 (PR-1).** `size_gas` rejects k ≤ 1 with a specific message (ideal-gas k = C_p/C_v is > 1 by definition; k < 1 previously computed a meaningless area *silently*); the handler's generic `except` now returns a fixed message instead of `str(e)` |
| 5 | ~~PRV two-phase: omitted back-pressure defaults to 0, silently forcing the critical branch~~ | `api/psv_calculator.py` | **FIXED v3.0 (PR-1), maintainer decision 2026-08-04 (option a).** An omitted/zero `Pa` now defaults to atmospheric (14.696 psia / 101.325 kPa) — the physical minimum for a vented system. Vector 4 is unchanged (P_c = 52.971 psia > atmospheric keeps the critical branch); the behavioral change appears only when P_c < atmospheric, where the old vacuum default *under-sized* the valve by choosing the critical equation for a subcritical case. The UI's `psv-Pa` field literal `value="0"` therefore now means "atmospheric" (§4.4) |
| 6 | ~~Error-response schemas differ across the three endpoints (dp: badge without message; psv: message without badge; flowregime: both)~~ | all three endpoints | **FIXED v3.0 (PR-1).** All error responses now carry the superset `{error, message, badge, badgeClass}` that flowregime already used: dp's two branches gained `message`, psv gains badge fields at the handler's single exit point. Purely additive — the frontend already tolerated both shapes. English prose pending i18n Milestone 4 |
| 7 | ~~Custom modules are not encoded in Share links~~ | `index.html` state system | **FIXED v2.8.** State format v:2 carries module definitions, with a sanitizing import boundary (§6.1). Also hardened alongside: the `og_custom_modules` parse is now guarded, `report-*` fields are excluded from state, and over-long share links warn |
| 8 | ~~No dedicated mobile navigation; tab bar relies on horizontal scroll~~ | `index.html` header | **FIXED v2.8.** Dropdown navigation below the `md` breakpoint (§3). Verified at 375 px: all 9 tabs reachable, trigger re-labels, menu auto-closes on selection, click-outside and Escape close it, no collision with the floating action bar, no horizontal overflow. Desktop unchanged — the bar still renders `display:flex` with all 9 buttons at 1280 px |
| 9 | ~~API RP 14E SI constant is `1.2247448714` (= √1.5)~~ | `api/dp_calculator.py` | **FIXED v2.8.** The constant is an exact unit conversion, not a fitted value: 0.3048·√16.0184634 = **1.2199032517**, where 16.0184634 = 0.45359237/0.3048³. √1.5 was a rounded "1.22" that had been "precisioned" into the wrong closed form; it over-predicted V_e by **+0.40 %**, making the screen marginally *non-conservative*. Vector 2's V_e moves **7.720 → 7.689 m/s** (ratio 0.1314 → 0.1319); the WITHIN LIMIT verdict is unchanged. Updated together in this document, CLAUDE.md, api/CLAUDE.md, the Theory tab and the How To Use callout. `test_erosional_velocity_constant_is_the_exact_unit_conversion` derives the constant from first principles rather than hard-coding it, and a second test round-trips V_e through field units |
| 10 | ~~`index.html` loads `/cdn-cgi/scripts/…/email-decode.min.js`, a Cloudflare email-obfuscation script baked into the file~~ | `index.html` | **FIXED v2.8.1.** The script tag (latterly at `index.html:2470`, sharing its line with the app's opening `<script>`) was removed with the maintainer's approval: the app deploys to Vercel where `/cdn-cgi/` does not exist (a dead 404 on every load), and no `__cf_email__` element remained for it to decode. The Privacy Policy clause that disclosed it (`docs.privacy.b007`) was rewritten in the inline English and in all 9 non-English dictionaries in the same commit |
| 12 | ~~PRV two-phase SUBCRITICAL mass-flux bracket mis-coded: `−2·ω·ln(η) + (ω−1)(1−η)` instead of Leung's `−2·[ω·ln(η) + (ω−1)(1−η)]` — the −2 multiplied only the log term~~ | `api/psv_calculator.py` (subcritical branch of `size_twophase`) | **FIXED v3.0 (PR-1).** Found by adversarial review of PR-1 itself. The wrong form produced subcritical flux ABOVE choked flux (impossible — choked flow is maximal) and was discontinuous at η_c, overstating G by ~20–30 % at ω ≈ 1.5 and **under-sizing** the valve on that branch. It shipped unnoticed since v2.0 because the branch was unreachable at the UI's `Pa` default of 0 (vacuum ⇒ always critical) — only an explicitly-entered `Pa > P_c` reached it. The §11 #5 atmospheric default would have made it the *default* path for low-P_o cases, so both changes ship in the same PR. Verified by construction: η_c is defined as the flux maximum, so the corrected subcritical G reproduces the critical-branch G at η_a = η_c (`test_subcritical_flux_is_continuous_with_the_critical_branch`, three ω values, plus pinned corrected areas: the P_o = 20 psia case moves 30.978 → **38.972 in²**). Vector 4 is on the critical branch and is bit-identical |
| 11 | ~~Z-Factor Estimator silently ignores a temperature of exactly **0**~~ (`0` is falsy, so `if(!sg \|\| !p \|\| !t) return;` aborted and left the *previous* result on screen with no indication it was stale — and 0 °C is an ordinary process temperature) | `index.html` `calcZFactor()` | **FIXED v2.8.** Guard is now `if(!sg \|\| !p \|\| isNaN(t)) return;`. `sg` and `p` keep the falsy check deliberately — zero gas gravity or zero absolute pressure are genuinely invalid, not merely unusual. Verified in a browser: 0 °C → Z = 0.6934 on **both** cards (they disagreed before), 0 °F → 0.6185, blank/`sg = 0`/`p = 0` still rejected, Vector 5 unchanged at 0.8646. Pinned by `test_zero_temperature_is_not_treated_as_missing_input` |
| 13 | ~~v2.4 Basic Eng converter cards (°API/SG/Density, Viscosity, Mass↔Vol) silently blank their computed field whenever the result reaches **1,000**~~ — the six `.value = formatValue(…)` writes put comma-grouped strings (e.g. `91,067.19`) into `type="number"` inputs, which browsers reject wholesale, leaving an empty field with no error | `index.html` `calcAPI()`/`calcVisc()`/`calcMassVol()` | **FIXED v3.1.** Found because the new GT Fuel "Send to Mass↔Vol" cross-link produces gas-scale flows (91,067 m³/h) that hit the threshold on every use; latent since v2.4 for any density > 999 kg/m³ or large flow. The six sites now use `formatValuePlain()` — identical digits to `formatValue()` (`toLocaleString` en-US, ≤ 5 fraction digits) with `useGrouping: false`, so sub-1,000 results render character-identically and larger results simply work. The General-tab converters keep `formatValue()` unchanged — their fields are `type="text" inputmode="decimal"` by design and display grouping correctly |

## 12. Internationalization (i18n)

Added in v2.6 as **Milestone 1** of a multi-milestone program (roadmap and decision points in DEVELOPMENT_PLAN.md §6 "Internationalization Program"); **Milestones 2 and 3 shipped in v2.7** — all 10 menu languages (en, ja, zh, ko, th, id, ru, es, fr, de) are fully live, covering the working tool and all four documentation tabs. Default language is English.

### 12.1 Dictionaries

- `i18n/en.json` — canonical working-tool dictionary and the runtime fallback for any working-tool key missing in another language. It deliberately contains **no `docs.*` keys** — English documentation content lives inline in `index.html` (see 12.6).
- `i18n/ja.json`, `zh.json`, `ko.json`, `th.json`, `id.json`, `ru.json`, `es.json`, `fr.json`, `de.json` — each carries the full 526-key working-tool set (368 through v2.8.1 + 36 steam keys, 19 NPSHa keys, 25 compressor keys, the `common.copiedWithUnit` toast and the 10 `basic.nav.*` quick-link keys in the v3.0 cycle; + 67 in v3.1: `nav.gtfuel`, the 56-key `gtfuel.*` namespace and 10 `js.export.gt*` keys) **plus** the 161 `docs.*` documentation keys (125 shipped in v2.7; 14 v2.8 blocks translated in v2.8.1; 4 steam, 4 NPSHa, 4 compressor and 2 unit-aware-copy blocks added with their translations in the same PR-2/PR-3/PR-4/PR-5 commits; 2 more for the ★ v3.0 What's New block in the release PR; 6 in v3.1: `docs.howto.b087`–`b090` and `docs.theory.b046`–`b047`).
- One flat/nested, dot-path-keyed JSON file per language (e.g. `advanced.deltaP.pipeIdLabel`, `safety.psv.gasHeading`, `docs.theory.b005`), namespaced roughly by tab/card. Fetched lazily at runtime via `fetch('i18n/<code>.json')` — not bundled into `index.html` — so the no-build-step principle holds and a visitor never downloads a language they don't select. English is always fetched too, as the fallback source.
- **Number formatting is en-US in every language** (decimal point, comma grouping) — a deliberate anti-ambiguity rule (see 12.5), enforced editorially in the dictionaries as well as in code.

### 12.2 Engine (inline in `index.html`'s existing `<script>` block — no second script file)

| Function | Role |
|---|---|
| `LANGUAGES` | Config array of all 10 target languages, `{code, native, enabled}`. As of v2.7 all 10 are `enabled: true`; a future language would be added as a new row plus its dictionary file. |
| `loadLanguage(code)` | Fetches and caches a dictionary in `translationsCache`. |
| `tr(key, params)` | Dynamic-string helper for JS-generated text (calc warnings/badges, toasts, the `exportReport()` document, mailto body). Does `{param}` template substitution and falls back to English, then to the raw key, if a key is missing. **Named `tr()`, not `t()`** — `t` already shadows a local variable in several existing functions (`exportReport()`'s id-lookup helper, `calcZFactor()`'s temperature local; the latter's *reduced-temperature-ratio* local was also renamed `pr`/`trr` to avoid colliding with `tr()` itself — a pure rename, zero calculation change). |
| `applyTranslations()` | Walks `[data-i18n]` (textContent), `[data-i18n-title]`, `[data-i18n-aria]`, `[data-i18n-placeholder]` and sets the matching text/attribute. Working-tool labels mixing a translatable word with a literal symbol (e.g. "MASS FLOW W", "DYNAMIC VISCOSITY (μ)") split the literal symbol into its own sibling `<span>`. **v2.7:** additionally walks `[data-i18n-html]` for the documentation tabs, swapping block-level `innerHTML` from `docs.*` keys (see 12.6). The v2.6 "no `data-i18n-html` by design" stance was superseded when the doc tabs were translated: block-level rich prose (tables, lists, inline emphasis, jump-link navs) cannot reasonably be expressed as plain-text keys, and the dictionaries remain first-party, version-controlled files — no user-supplied content ever enters them, so the innerHTML path introduces no practical injection surface. |
| `setLanguage(code)` | Persists `localStorage['og_lang']`, syncs `<html lang>`, re-runs `applyTranslations()` + `enhanceAccessibility()` (see 12.4), refreshes client-side calculator output via the existing `recomputeAll()`, and marks server-backed results (ΔP/PSV/Flow Regime badges) stale via the existing `markResultStale()` convention rather than re-firing an API call. |
| `applyAwaitingBadgeDefaults()` | Re-translates the idle-state badge text ("Awaiting Calc...", "Run calculation to see intermediate values…", etc.) without stomping a live result already showing in a different language. |

### 12.3 Switcher UI

Two-part control in the header (`.flex.items-center.justify-between.mb-4` row), not in the horizontally-scrolling tab `<nav>`:
- **Quick toggle** — `EN` / `日本語` segmented buttons, visually matching the app's existing Abs/Gauge-style toggle-button pattern.
- **Settings menu** — a gear-icon button opens a dropdown listing all 10 `LANGUAGES` entries; as of v2.7 every entry is clickable (the "coming soon" rendering path remains in `buildLangMenu()` for any future `enabled: false` row).

### 12.4 Bundled fixes (each was necessary for correct language switching, not scope creep)

- `enhanceAccessibility()`'s three `aria-label` setters were guarded ("if not already set") and would have silently frozen after the first language switch; they are now unconditional (idempotent) and are re-run from `setLanguage()`.
- `setHVMode()`'s direct DOM-text overwrite of `out-ghv-label` is now routed through `tr()`, and `applyTranslations()` re-syncs that label from the live `hvMode` state (not a static key) so it survives a language switch mid-session.
- `calcPSV()`'s "Enter required input(s)" message previously baked in English pluralization (`'input' + (n > 1 ? 's' : '')`); replaced with distinct singular/plural translation keys, since Japanese (and several of the pending 8 languages) has no plural marking.
- `markResultStale()`'s appended suffix (previously the hardcoded literal `' · inputs changed — recalculate'`) is now translated via `tr()`.

### 12.5 Translation scope — Milestones 1–3 (complete as of v2.7)

**Translated in all 10 languages:** General, Basic Eng, Advanced, Safety tabs (§4.1–4.4); the floating action bar; the Report form; the module-config modal; every JS-generated dynamic string across `calcGHV()`, `calcDeltaPressure()`, `calcFlowRegime()`, `calcPSV()`, `showToast()`, and `exportReport()`'s full standalone document (which also now sets its own `<html lang>`); and (v2.7, Milestones 2+3) the four documentation tabs — How To Use, Theory, Terms of Use, Privacy Policy — via the `data-i18n-html` mechanism in 12.6.

**Legal pages carry a governing-language note** (`docs.terms.langNote` / `docs.privacy.langNote`): translations are provided for convenience; the English version governs. Non-English Terms/Privacy texts are machine-assisted translations pending the maintainer's legal review.

**Never translated, by design, in any language:** chemical formulas, SI/imperial unit symbols, standard/code citations (JIS K 2301, API 520/526, ISO 6578, ASTM D1250, CODATA, API RP 14E), engineering variable symbols (W, P1, Kd, θ, ω, Re, …), version strings, the §9 reference test-vector values (byte-identical across languages by requirement), proper nouns, the developer's email.

**Not yet localized (server side):** the three Python endpoints (§5) still return English prose for status/error text. `flowregime.py` already returns a machine-readable `regime_key` alongside its English `regime` label (§5.3) — the ~10+ other message/error branches across the three files are unkeyed. See DEVELOPMENT_PLAN.md §6 Milestone 4 (optional).

**Number formatting is unchanged and language-independent:** `toLocaleString('en-US', …)` applies regardless of UI language — a deliberate decision (avoids decimal-comma ambiguity on values that get copy/pasted or shared cross-language), not a gap.

### 12.5.1 Pending translation (v2.8) — resolved in v2.8.1

The v2.8 documentation additions — How To Use "★ New in Version 2.8" plus sections 13–15, and Theory Part VII (7.1 Lee-Gonzalez-Eakin, 7.2 sonic velocity, 7.3 Joule-Thomson, 7.4 Crane TP-410, 7.5 NORSOK criteria) — shipped in English only: 14 blocks (howto `b069`–`b076`, theory `b034`–`b039`) totalling ~13,200 characters of technical prose, temporarily exempted via a frozen `PENDING_TRANSLATION` set in `tests/test_i18n_parity.py` with guard tests preventing the set from growing.

**v2.8.1 closed the exemption**: all 14 blocks were translated into the 9 non-English dictionaries, and the `PENDING_TRANSLATION` set and its guard tests were deleted together, per the original plan. Every `data-i18n-html` block now resolves in every language; the runtime English fallback via `i18nHtmlOriginals` (§12.6) remains in place as a safety net for any future missing key.

### 12.6 Documentation-tab translation mechanism (v2.7, Milestones 2+3)

- **`data-i18n-html` attributes** mark 155 block-level elements across the four documentation tabs (`docs.howto.b001`–`b086`, `docs.theory.b001`–`b045`, `docs.terms.b001`–`b010` + `langNote`, `docs.privacy.b001`–`b012` + `langNote`). v2.8 added 14 (howto `b069`–`b076`, theory `b034`–`b039`), translated in all 9 non-English dictionaries as of v2.8.1 — see §12.5.1. The v3.0 cycle added 4 in PR-2 (howto `b077`/`b078`, theory `b040`/`b041`), 4 in PR-3 (howto `b079`/`b080`, theory `b042`/`b043`), 4 in PR-4 (howto `b081`/`b082`, theory `b044`/`b045`), 2 in PR-5 (howto `b083`/`b084`) and 2 in the release PR (the ★ v3.0 What's New block, howto `b085`/`b086`), each with all 9 translations landing in the same commit — feature PRs now ship with zero translation debt as standard practice. New keys are appended numerically even when the section sits near the top of the DOM, because the number is only an identifier and renumbering would touch every dictionary. Blocks were chosen so that **no element containing an `id` (section anchors, jump-link targets) is ever inside a swapped region** — anchors, the back-to-top behaviour, and wireframe structure are untouched by language switches.
- **English lives inline, once.** On the first `applyTranslations()` pass each block's original English `innerHTML` is cached in `i18nHtmlOriginals`; switching back to English (or hitting a missing key in any language) restores from that cache. `en.json` therefore carries no `docs.*` keys and English users download no documentation text twice.
- **Translation integrity is machine-checked** (build-side, not runtime): each translated value must have a byte-identical HTML tag/attribute sequence to its English source, identical `{placeholder}` sets, and digit-for-digit identical numeric tokens (the Theory tab's worked examples and Table 1.1 constants are regulatory reference values). The checker lives with the maintainer tooling; re-run it whenever a `docs.*` key changes.
- **Sync rule:** any edit to the inline English documentation HTML must update the corresponding `docs.*` key in all 9 non-English dictionaries in the same commit (see CLAUDE.md Documentation Sync Rule).


## 13. Automated Testing & CI (v2.8)

Added in v2.8. Before this, the reference-value regression in DEVELOPMENT_PLAN.md §7.2 was
a manual checklist; it now runs on every push and pull request.

### 13.1 Layout

| Path | Purpose |
|---|---|
| `pytest.ini` | Runner config; `testpaths = tests` |
| `requirements-dev.txt` | **pytest only.** Deliberately separate from `requirements.txt`, which Vercel installs into the production serverless runtime |
| `tests/conftest.py` | Loads the three `api/*.py` endpoints by path (they are Vercel functions, not a package) and provides the `post_to_handler` fixture |
| `tests/test_dp_calculator.py` | Vector 2, unit-factor guards, friction-factor and phase-detection branches |
| `tests/test_psv_calculator.py` | Vector 4 candidates (§9), the five sizing modes, API 526 orifice selection |
| `tests/test_flowregime.py` | Vector 3, map selection by inclination, validation guards |
| `tests/test_i18n_parity.py` | Key parity across all 10 dictionaries; `index.html` ↔ dictionary agreement |
| `tests/test_steam_if97.py` | (v3.0) IF97 coefficient extraction from `index.html` + independent Python re-evaluation of the Release's verification tables (Tables 5/15/35/36, B23) to 9 s.f.; Vector 8 display pins; exact-unit-factor and advisory-isolation guards |
| `tests/test_npsh.py` | (v3.0) Vector 9 through the exact UI path (8-s.f. helper quantization), page↔spec worked-example agreement, g = 9.80665 and exact-unit-factor guards, shared-IF97-routing guard |
| `tests/test_compressor.py` | (v3.0) Vector 10 re-run on literals extracted from `index.html` (bar factor, MW_AIR_GP, R_KMOL_GP), page↔spec worked-example agreement, exact-derivation checks on the ft·lbf/lbm and hp display factors, shared-`papayZ()`-routing and guard-polarity source guards |
| `tests/test_clipboard.py` | (v3.0) every static `data-unit-src` id resolves to a real element, site counts (21 dynamic + 6 literal + 2 template as of v3.1), bare-value-preserving `copyText` structure, delegated-listener and long-press source guards, `createCard` id-only attribute invariant |
| `tests/test_basic_nav.py` | (v3.0) Basic Eng quick-links strip: all nine pills resolve to anchored cards in order, `scroll-mt-24` clearance survives, every pill carries a `basic.nav.*` key |
| `tests/test_gt_fuel.py` | (v3.1) Vector 11 display pins + page↔spec worked-example agreement; GT_MODELS extraction (JSON.parse contract) with per-entry source citations, HR ≡ 3600/η within 30 kJ/kWh, CC > SC invariants and MHI brochure spot-pins; derived `GT_HV_FACTOR` guard; static-option-list completeness (share-restore trap); `lastGHV` bridge, `recomputeAll` wiring and SVG-symbol presence |
| `tests/test_lng_presets.py` | (v3.3) Vector 12 — every published preset re-run through a Python replica of the JIS K 2301 chain and checked against the source's own GCV/WI within ±0.05 MJ/Nm³ (the replica is itself pinned to Vector 1 first, so a drifting guard cannot pass silently); LNG_PRESETS extraction (JSON.parse contract) with per-entry citations; the tier honesty boundary (`asm` entries forbidden from declaring a published value); GIIGNL entries pinned to `mol` basis and required to disclose the C4-split assumption; the C4-split sweep re-measured against `C4_SPLIT_MAX_SPREAD` and cross-checked against the figure quoted in the citations; static-option-list completeness (share-restore trap); source guards on `hhv_mix` (not `hv_mix`), the edit-clears-attribution listener, the `calcGHV()` repaint and the no-`innerHTML` renderer |
| `tests/test_lng_cargo.py` | (v3.5) Vector 13 chain pins + page↔spec worked-example agreement; the named unit constants (`GJ_PER_MMBTU`, `MJ_PER_MWH`, `KG_PER_LB`, `RHO_LBSCF_TO_KGNM3` derived not typed) and the lb/scf-not-lb/ft³ guard on `gt-rho-u` / `importGHVToGT()` / `gtLastResult.rho`; GT totals default units unchanged + the new `gt-tot-*-q` column blanked on bad input; Vector 11 through the switched units (27.394 Bscf, 28.00 / 12.32 TBtu, 13.00 PJ, 3,474.2 MMBtu/h, 3.40 MMscf); LNG_VESSELS extraction (JSON.parse contract), 36 unique IMOs, full class/containment/propulsion coverage; **provenance** — every row has a public non-AIS, non-IGU source URL; **photos** — every `photo` flag ↔ file ↔ CREDITS.json entry with a CC/PD licence and matching on-screen credit, ≤ 130 KB, no orphans, README disclaims MIT; static-option-list completeness; `lastLNGProps` bridge and untouched `lastGHV`; no JIS/ISO 6578 recomputation in the card; wiring into `recomputeAll`/`calcGHV`/`calcGTFuel`; no innerHTML in the vessel panel; escaped catalogue; IMO-only outbound links; `'lc': 'lng-cargo'` in the analytics map; export §7 |
| `tests/test_architecture.py` | The stdlib-only rule, the no-build-step rule, dev/prod dependency separation |
| `tests/test_analytics_privacy.py` | (v3.2) The analytics privacy boundary — Report tab excluded from the id-prefix map, no `.value`/`.innerText` read in the instrumentation block, closed set of five event names, fixed slugs only; plus disclosure parity: no stale "no analytics" claim in the English policy or the og:/twitter: tags, and all 9 translated policies name the product, cite Vercel's privacy doc and carry the bumped version. Includes a non-vacuity guard on its own map-extraction regex |
| `.github/workflows/ci.yml` | Two jobs — see 13.3 |

### 13.2 How `dp_calculator.py` is tested without refactoring it

`psv_calculator.py` and `flowregime.py` keep their math in module-level pure functions
(`size_gas(...)`, `compute(...)`) and are called directly. `dp_calculator.py` does not —
all of its physics is inline inside `handler.do_POST`, interleaved with the response
plumbing.

Adding a `compute()` function purely for testability would be a refactor of working,
deployed code, which CLAUDE.md preservation rules 1–3 forbid without explicit
instruction. Instead `post_to_handler` constructs the handler via
`handler.__new__(cls)` — bypassing `BaseHTTPRequestHandler.__init__`, which would attempt
socket setup — then injects `headers`/`rfile`/`wfile` and stubs the response methods. The
endpoint is exercised exactly as deployed, through its real HTTP entry point.

This couples to stdlib internals rather than a public API, so it is confined to that one
fixture; a future Python release breaking it is a one-line fix in `conftest.py`.

### 13.3 CI jobs

1. **`stdlib-only`** — installs `requirements-dev.txt` and nothing else, then runs the ΔP,
   PRV, i18n and architecture suites. The absent install is itself the test: adding a
   third-party import to `dp_calculator.py` or `psv_calculator.py` makes this job fail to
   import, enforcing the `api/CLAUDE.md` dependency rule mechanically.
2. **`flow-regime`** — installs `requirements.txt` (numpy/matplotlib/seaborn) and runs the
   Flow Regime suite. Only `compute()` is exercised; no PNG is rendered.

### 13.4 Scope and deliberate limits

- The suite **locks current behavior**, including the defects in §11. Where it does, the
  test says so and names the register entry, so closing an issue is a deliberate act that
  updates both together rather than a silent change to a shipped value.
- **The JIS K 2301 chain (Vector 1) is not yet covered.** It lives in JavaScript
  (`calcGHV()`), which pytest cannot import. The chosen route for a later release is to
  extract `index.html`'s self-contained slice and run it under `node -e` with a small DOM
  shim, keeping **one** source of truth for the regulatory math. A Python port was
  rejected as the primary mechanism: two sources of truth for regulatory-traceable
  arithmetic is precisely the divergence the preservation rules exist to prevent. (If one
  is ever written as a supplement, it must use `math.floor(x + 0.5)` — Python's `round()`
  is banker's rounding, JavaScript's `Math.round()` is half-up, and the JIS rules round at
  five separate places.)
- **Vector 4 (PRV) was authored during v2.8** and reviewed and approved by the maintainer before promotion into §9. Its two-phase case was adjusted during that review — W halved so the result lands on a real API 526 orifice rather than over-ranging — and the review is what surfaced Known Issue #1, now fixed.

---

## 14. Usage Analytics (v3.2)

### 14.1 Why custom events, not just page views

The app is a **single URL**. Page views therefore measure arrival and nothing else: they cannot distinguish a visitor who ran a PRV sizing from one who bounced off the General tab. With ~20 calculators competing for maintenance effort, "which of these earns its keep" is the only question worth instrumenting for, and it is invisible without custom events.

### 14.2 Installation

Script-tag install, not `@vercel/analytics`. The npm package targets React/Next and needs a bundler; this project has no build step (§2), and the dashboard's default "Get Started" panel shows the Next.js instructions, which do not apply here. Two tags in `<head>`:

```html
<script>window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };</script>
<script defer src="/_vercel/insights/script.js"></script>
```

The stub must precede the script: events fired before the deferred load completes are queued into `window.vaq` and replayed. Without it they would throw.

`/_vercel/insights/script.js` is injected by Vercel's edge and exists only on a Vercel deployment where Web Analytics is enabled for the project. Off Vercel it 404s and the queue simply never drains — every calculator behaves identically, which is also what happens for any visitor running a content blocker.

### 14.3 Event schema

Five event names, a closed set (Vercel caps distinct names per project; the variance belongs in `data`, not in the name).

| Event | `data` | Cardinality |
|---|---|---|
| `Tool Used` | `tool` — fixed slug: `gas-volume`, `pressure`, `temperature`, `heating-value`, `custom-module`, `pipe-volume`, `z-factor`, `petroleum-gravity`, `viscosity`, `mass-vol-flow`, `gas-properties`, `steam-if97`, `npsh`, `compressor`, `gas-composition`, `pipe-dp`, `gt-fuel`, `prv-sizing` | **≤ 1 per tool per page load** |
| `Calculation` | `tool` — `pipe-dp` \| `prv-sizing` \| `flow-regime` | Every run |
| `Tab View` | `tab` — the ten tab ids | Every user-initiated switch |
| `Language` | `lang` — the ten language codes | Every switch |
| `Action` | `action` — `export-pdf` \| `share-link` \| `report-sent` | Every click |

### 14.4 Two implementation constraints

**Live converters fire on every keystroke.** `calcGHV()` alone has 31 inline `oninput`/`onchange` bindings. One event per call would measure typing speed and exhaust the plan's event allowance. `Tool Used` is therefore de-duplicated through a `Set` for the life of the page: it measures *reach* (what share of visits touch the steam table), not intensity.

Detection is **delegated off `e.target.id`** via `VA_TOOL_BY_ID_PREFIX`, not by wrapping the calc functions. Several converters are bound by reference (`tIn1.addEventListener('input', updateTemp2)`, the `createCard()` module cards), and a wrapper installed after binding would never see those calls. Element ids are already an API (§1), so keying on them adds no new coupling — and it means a new card is instrumented by adding one line to the map, which is how GT Fuel's `gt-*` family is covered.

The three **server-backed** calculators are click-driven and each costs a serverless invocation, so `Calculation` counts every run. That figure is directly comparable to the function invocation count in the Vercel dashboard; the gap between them is the ad-blocker rate.

**Boot must be silent.** `applyState()` → `recomputeAll()` runs the live calculators on every page load, and a share link additionally calls `switchTab()`. Counting those would report a `localStorage` restore as user activity and flatten every tool to equal popularity. A module-level `vaArmed` flag stays `false` until the first `pointerdown` or `keydown` (capture phase, `once`), and `trackEvent()` is a no-op until then. The delegated listeners are independently safe — `applyInputs()` assigns `.value` directly, which fires no `input` event — so `vaArmed` is what protects the wrapped functions.

### 14.5 The privacy boundary

**Record *that* a tool was used; never *what* was entered into it.** No input value, no unit selection, no calculation result, and no character of the Report tab, which is excluded from the id-prefix map outright (it is the one place a user types prose, and v2.8 already excluded it from `localStorage` and from share links).

Nothing enforces this at runtime — it is a property of the id-prefix map and of six `trackEvent()` call sites, all wideable in one line. `tests/test_analytics_privacy.py` is what makes that line fail (§13.1).

The whole feature is additive: it modifies no existing function, and is removed by deleting the block at the end of the `<script>` plus the two `<head>` tags.

### 14.6 Disclosure

Per the release rule in MARKETING.md §5, no measurement ships before the Privacy Policy discloses it **in the same release**. v3.2 rewrote §2 (bullet list + a "Changed in v3.2" note), §5 (processor), §7 (rewritten from "No Cookies or Tracking" to "Cookieless Usage Analytics", with the exhaustive event list and the opt-out route) and §9 (a deletion request cannot be matched against anonymous records), in the inline English **and** in all nine non-English dictionaries (`docs.privacy.b002/b004/b007/b009/b011`). The `og:description` and `twitter:description` claims of "no tracking" were changed to "no ads", which remains true.

### 14.7 Dashboard enablement

The script alone is not sufficient — Web Analytics must also be enabled for the project in the Vercel dashboard. It already is: `https://engineering-converter.com/_vercel/insights/script.js` returned HTTP 200 with a 2,495-byte body before this release shipped, and that route is served only when the feature is on (a disabled project 404s). The dashboard's "Get Started" panel persists until the first event arrives, so it is not an indicator of the enablement state.
