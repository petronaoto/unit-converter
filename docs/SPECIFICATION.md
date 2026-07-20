# Detailed Specification — O&G Engineering Converter

**Document version:** 1.1 (describes app v2.6)
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
- **Floating action bar** (bottom-right, hidden in print): Share, Export PDF, and Back-to-Top (v2.5, appears after ~600 px scroll); `state-toast` gives feedback.
- **Copy buttons:** inline SVG buttons on inputs/outputs → clipboard, with a 1.5 s green check; `aria-label`s are backfilled at runtime.

## 4. Feature Specifications by Tab

### 4.1 General

| Card | Inputs (IDs) | Behavior |
|---|---|---|
| **Gas Volume** | `nm3-input`/`nm3-select`, `scf-input`/`scf-select` | Bidirectional live conversion; base factor **1 Nm³ = 37.3258 scf** with unit multipliers (kNm³, MMscf, …). |
| **Pressure** | `press-input1`/`press-select1` + mode buttons `press-mode1-abs`/`-gau`; mirrored `…2` set | Dual-sided converter; each side independently Abs or Gauge (`setPressMode`). Conversion goes through absolute Pa (`pressToAbsPa`/`pressFromAbsPa`, atmosphere = 101.325 kPa). |
| **Temperature** | `temp-input1`/`temp-select1`, `temp-input2`/`temp-select2` | °C/°F/K bidirectional (`convertTemp`). |
| **Heating Value** | `hv-input1`, `hv-input2` | Fixed-unit MJ/Nm³ ↔ Btu/scf pair (`HV_FACTOR`). |
| **Custom Modules** | Builder modal (`openModal()`), presets (flow rate, density, viscosity, …) | User-defined linear-factor converter cards; persist in `localStorage['og_custom_modules']`; created via `createCard`. Not included in Share links (known limitation). |

### 4.2 Basic Eng

| Card | Inputs → Outputs (IDs) | Method |
|---|---|---|
| **Pipe Volume** | `pipe-id`, `pipe-length`, `pipe-out-u` → `pipe-vol-out` | V = π/4 · D² · L with mixed metric/imperial units (`calcPipeVolume`). Canonical card layout. |
| **Z-Factor Estimator** | `z-sg`, `z-p`/`z-p-u`, `z-t`/`z-t-u` → `z-result`, warning `z-warn` | **Papay (1968)**: Z = 1 − 3.52·Pr/10^(0.9813·Tr) + 0.274·Pr²/10^(0.8157·Tr), with **Standing-Katz pseudo-criticals** Ppc = 756.8 − 131·SG − 3.6·SG², Tpc = 169.2 + 349.5·SG − 74·SG² (psia/°R). Validity envelope 0 < Pr ≤ 15, 1.05 ≤ Tr ≤ 3.0; out-of-envelope inputs show an extrapolation warning in `z-warn`. |
| **Petroleum Gravity** | `api-grav`, `api-sg`, `api-den`/`api-den-u` | Three-way °API ↔ SG(60/60°F) ↔ density; °API = 141.5/SG − 131.5; water at 60 °F = 999.016 kg/m³ (`RHO_WATER_60F`). |
| **Viscosity** | `visc-dyn`(+unit), `visc-kin`(+unit), `visc-rho` | ν = μ/ρ; dynamic (cP, mPa·s, Pa·s) ↔ kinematic (cSt, mm²/s, m²/s) via density. Since v2.5, mPa·s and mm²/s use the distinct option values `0.0010`/`0.0000010` so restored state keeps the selected label (numerically identical to cP/cSt). |
| **Mass↔Vol Flow** | `mf-mass`(+unit), `mf-vol`(+unit), `mf-rho` | Q_m = Q_v · ρ bidirectional (`calcMassVol`). |

### 4.3 Advanced

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

#### 4.3.2 Pipe Delta Pressure (Darcy-Weisbach) — server-backed

- **Inputs** (`dp-*`): `dp-scale`, `dp-id`/`dp-id-unit`, `dp-len`/`dp-len-unit`, `dp-rough`/`dp-rough-unit`, `dp-elev`/`dp-elev-unit`; vapor `dp-v-flow`/`-u`, `dp-v-den`/`-u`, `dp-v-visc`/`-u`; liquid `dp-l-flow`/`-u`, `dp-l-den`/`-u`, `dp-l-visc`/`-u`; erosion C-factor `dp-cfactor` (default 100).
- **Outputs:** `dp-out-total`(+unit), `dp-out-len` (ΔP per 100 m / 100 ft), `dp-out-vel`(+unit), second row `dp-out-re`/`dp-out-re-regime`, `dp-out-f`, `dp-out-ve`, `dp-out-eratio`, `dp-out-ero-badge` (WITHIN LIMIT < 0.8 ≤ NEAR LIMIT < 1.0 ≤ EXCEEDS Ve), regime cross-link note `dp-out-regime-note`, status badge `dp-regime-badge`.
- **Method (server, §5.1):** phase detection → single vapor / single liquid / two-phase HEM; Darcy-Weisbach friction term + hydrostatic term; Colebrook-White friction factor (iterative); API RP 14E erosional velocity V_e = 1.2247·C/√ρ_mix (SI form of V_e = C/√ρ in lb/ft³ units).

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
| Steam | §5.7 | `psv-W-steam`, `psv-P1-steam`, `psv-Kd-steam`, `psv-Kb-steam`, `psv-Kc-steam`, `psv-KSH` | Kd 0.975, Kb 1.0, Kc 1.0, KSH 1.0 |
| Liquid (certified) | §5.8 | `psv-Q`, `psv-Gl`, `psv-P1-liq`, `psv-P2-liq`, `psv-mu`, `psv-Kd-liq`, `psv-Kw`, `psv-Kc-liq` | Gl 1.0, Kd 0.65, Kw 1.0, Kc 1.0 |
| Liquid (non-certified) | §5.9 | as above + `psv-Ps`, `psv-Kp` | Kd 0.62, Kp 1.0 |
| Two-phase | §5.10 / Annex C | `psv-W-tp`, `psv-vo`, `psv-v9`, `psv-Po`, `psv-Pa`, `psv-Kd-tp`, `psv-Kb-tp`, `psv-Kc-tp`, `psv-Kv-tp` | Kd 0.85, Kb/Kc/Kv 1.0 |

- **Outputs:** `psv-out-area` (+`psv-out-area-unit`), `psv-out-orifice` (API 526 letter D–T, or `T+` if larger than T), `psv-out-orifice-area`, `psv-out-details` (mode-specific intermediates: C, Pcf, Pcf/P1, KN, KSH, Kv, Re, ω, η_c, Pc, G), badge `psv-badge`.
- **Methods (server, §5.2):** gas — critical vs subcritical via (2/(k+1))^(k/(k−1)) with C coefficient and F₂ subcritical factor; steam — Napier equation with KN high-pressure correction and KSH superheat factor; liquid — §5.8 two-pass with viscosity correction Kv(Re), §5.9 adds 1.25·Ps effective ΔP and Kp; two-phase — Omega method (ω = 9(v₉/v₀ − 1), η_c from Eq. C.15, critical/subcritical mass flux G, area per C.20/C.21).

### 4.5 Documentation & Support Tabs

- **How To Use** — Operations manual: "What's New" + 12 illustrated sections (header/nav, General, custom modules, Basic Eng, Advanced §1–4, ΔP, Flow Regime, PRV, Report) using CSS wireframe diagrams. Since v2.5: jump-link strip at the top and section anchors.
- **Theory** — Constants and formulas: Part I gas compositional (JIS K 2301 with worked examples), Part II density/flow, Part III LNG Klosek-McKinley (Tables B.2/C), Part IV hydraulics (Papay Z-factor §4.1, Darcy-Weisbach + Colebrook §4.2, flow-regime maps §4.3, erosional velocity §4.4), Part VI PRV sizing (§6.1–§6.7 incl. API 526 orifice table), Part V data sources. Worked-example numbers must match actual calculator output exactly.
- **Terms of Use** — 8 clauses (reference-only nature, warranty disclaimer, liability, user responsibility, IP, updates, governing law).
- **Privacy Policy** — 10 clauses (zero collection, localStorage-only state, stateless APIs, hosting, report feature, no cookies/tracking, children, rights, contact).
- **Report** — `mailto:` composer for bug reports / feature requests (no server round-trip); includes app-version environment string.

## 5. Serverless API Contracts

All endpoints: `POST` JSON body, JSON response, `Access-Control-Allow-Origin: *`, OPTIONS preflight supported. Malformed JSON → HTTP 400. Domain errors are returned as HTTP 200 with an error object (schemas below differ per endpoint — see Known Issues #6).

### 5.1 `POST /api/dp_calculator`

**Request** (all numeric; `*_mult`/`*_m` are multiply-to-SI factors):

```json
{ "scale": 1, "id": 4, "id_mult": 0.0254, "len": 100, "len_mult": 1,
  "rough": 0.045, "rough_mult": 0.001, "elev": 70.711, "elev_mult": 1,
  "v_flow": 150, "v_flow_m": 0.000277778, "v_den": 10, "v_den_m": 1, "v_visc": 0.012, "v_visc_m": 0.001,
  "l_flow": 7300, "l_flow_m": 0.000277778, "l_den": 500, "l_den_m": 1, "l_visc": 0.12, "l_visc_m": 0.001,
  "cfactor": 100 }
```

**Success response:**

```json
{ "error": false,
  "dpPa": 176919.0, "dpFric": 2340.0, "dpStatic": 174580.0,
  "vel": 1.014, "Re": 220000.0, "re_regime": "Turbulent", "f": 0.0184,
  "rho_mix": 251.7, "v_ero": 7.72, "ero_ratio": 0.13, "cfactor": 100.0,
  "L": 100.0, "badge": "Two-Phase (HEM)", "badgeClass": "…tailwind classes…" }
```

(Values shown are the reference case, approximate; `re_regime` ∈ Laminar < 2300 ≤ Transitional < 4000 ≤ Turbulent.)

**Error response:** `{ "error": true, "badge": "…", "badgeClass": "…" }` — note: no `message` field (Known Issue #6).

**Method:** HEM two-phase mixing (x = W_v/W_t; 1/ρ = x/ρ_v + (1−x)/ρ_l; μ = x·μ_v + (1−x)·μ_l), Darcy-Weisbach ΔP_fric = f·(L/D)·ρ·v²/2 with iterative Colebrook-White f (laminar 64/Re below Re 2300), ΔP_static = ρ·g·Δz (g = 9.81), API RP 14E V_e = 1.2247·C/√ρ.

### 5.2 `POST /api/psv_calculator`

**Request:** `{ "mode": "gas|steam|liquid_cert|liquid_noncert|twophase", "units": "USC|SI", …mode fields… }` (field lists and defaults in §4.4; USC: lb/h, psia, °R, gpm; SI: kg/h, kPaa, K, L/min).

**Success response (common):**

```json
{ "error": false, "area": 1234.5678, "area_unit": "mm²",
  "orifice": "J", "orifice_area": 830.0, "orifice_unit": "mm²",
  "flow_regime": "…", "badge": "…", "badgeClass": "…" }
```

plus mode-specific intermediates — gas: `C`, `Pcf`, `critical_ratio`; steam: `KN`, `KSH`; liquid: `Kv`, `Re`; two-phase: `omega`, `eta_c`, `Pc`, `G`. Orifice selection: smallest API 526 letter (D–T) whose area ≥ required; `T+` if none.

**Error response:** `{ "error": true, "message": "…" }` — note: no badge fields (Known Issue #6).

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
- **State shape** (v1): `{ "v": 1, "inputs": { "<element-id>": "<value>", … }, "hv": "hhv|lhv", "fa": "vol|mol", "fb": "mass|mol", "p1": "abs|gau", "p2": "abs|gau", "tab": "<tab-name>", "lang": "<language-code>" }` — `inputs` covers every `input`/`select`/`textarea` with an id inside `<main>`. `lang` was added in v2.6 (purely additive; older encoded links with no `lang` key still decode fine and default to English).
- **Share link:** `copyShareLink()` base64-encodes the same state object into `<origin><path>#s=<base64>`; entirely client-side.
- **Restore precedence on load:** share-link hash → localStorage → defaults. Restore reapplies inputs, the five toggle modes, and recomputes client-side cards. **Only share links** additionally open on their saved tab (so a shared PSV case lands on Safety); normal visits always land on the General tab (v2.5.1 — localStorage tab restore was removed as a landing-page annoyance, though `tab` is still recorded in the state object for share links). **Language follows a different policy** (v2.6): a returning visitor's saved `og_lang` auto-restores on a normal visit (unlike `tab`), and a share link's `lang` field takes priority over even that saved preference — see §12.
- **Custom modules** persist separately in `localStorage['og_custom_modules']` and are **not** part of the share-link payload (documented limitation; roadmap v2.6).

## 7. Export Report

`exportReport()` builds a standalone printable HTML document (report header with version + timestamp, sections for GHV & composition, ΔP, Flow Regime, PRV, Basic Eng values, plus the reference-only disclaimer) and opens it in a new window for the browser's Save-as-PDF. Since v2.5, if the pop-up is blocked the same HTML is downloaded as `og-converter-report.html` instead, with a toast explaining the fallback.

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

**Vector 2 — Pipe ΔP default case** (ID = 4 in, L = 100 m, Δz = 70.711 m, vapor 150 kg/h @ 10 kg/m³ / 0.012 cP, liquid 7,300 kg/h @ 500 kg/m³ / 0.12 cP, C = 100): ΔP_total ≈ **176.9 kPa** (friction ≈ 2.34 kPa + static ≈ 174.6 kPa), vel ≈ 1.014 m/s, Re ≈ **2.20×10⁵** (Turbulent), f ≈ **0.0184**, ρ_mix ≈ 251.7 kg/m³, V_e ≈ **7.72 m/s**, v/V_e ≈ 0.13 → WITHIN LIMIT.

**Vector 3 — Flow Regime default case** (same inputs): **Churn / Slug Flow**, θ = **+45.0°**, vertical map, j_G ≈ 0.514 m/s, j_L ≈ 0.500 m/s.

## 10. Deployment

- **Production:** Vercel, auto-deploy on push to `main`. Zero-config: static `index.html` + auto-provisioned `api/` Python functions.
- **Dependencies:** `requirements.txt` applies to `flowregime.py` only (numpy ≥ 1.26, matplotlib ≥ 3.8, seaborn ≥ 0.13). The other two endpoints must remain standard-library-only.
- **Local:** `vercel dev` → <http://localhost:3000>.

## 11. Known Issues Register

| # | Issue | Location | Status |
|---|---|---|---|
| 1 | Two-phase PRV result line displays Pc computed from back-pressure `Pa` instead of relieving pressure `Po` (sizing itself is correct — the internal critical/subcritical decision uses η_c·Po) | `api/psv_calculator.py:329` | Fix proposed, awaiting maintainer approval |
| 2 | ΔP API: zero viscosity/density inputs can raise an uncaught exception → HTTP 500 without CORS/JSON, surfacing as a generic "API Connection Failed" badge | `api/dp_calculator.py` | Fix proposed, awaiting approval |
| 3 | ΔP API accepts a negative erosion C-factor (produces a negative V_e with a green WITHIN LIMIT badge); `cfactor: 0` silently becomes 100 | `api/dp_calculator.py:107` | Fix proposed, awaiting approval |
| 4 | PRV gas mode: k ≤ 1 raises a division error that surfaces as a raw Python message; generic `str(e)` leaks internals | `api/psv_calculator.py` | Fix proposed, awaiting approval |
| 5 | PRV two-phase: omitted back-pressure defaults to 0, silently forcing the critical branch | `api/psv_calculator.py` | Behavior decision needed (default to atmospheric vs. require input) |
| 6 | Error-response schemas differ across the three endpoints (dp: badge without message; psv: message without badge; flowregime: both) | all three endpoints | Harmonization to the superset `{error, message, badge, badgeClass}` proposed |
| 7 | Custom modules are not encoded in Share links | `index.html` state system | Roadmap v2.7 (state format v:2) |
| 8 | No dedicated mobile navigation; tab bar relies on horizontal scroll | `index.html` header | Roadmap v2.7 |

## 12. Internationalization (i18n)

Added in v2.6 as **Milestone 1** of a multi-milestone program (roadmap and decision points in DEVELOPMENT_PLAN.md §6 "Internationalization Program"). Default language is English; the app is fully usable in Japanese today; 8 more languages are scaffolded but not yet translated.

### 12.1 Dictionaries

- `i18n/en.json` — canonical dictionary and the runtime fallback for any key missing in another language.
- `i18n/ja.json` — Japanese, Milestone-1 scope (below).
- One flat/nested, dot-path-keyed JSON file per language (e.g. `advanced.deltaP.pipeIdLabel`, `safety.psv.gasHeading`, `js.export.section1Title`), namespaced roughly by tab/card. Fetched lazily at runtime via `fetch('i18n/<code>.json')` — not bundled into `index.html` — so the no-build-step principle holds and a visitor never downloads a language they don't select. English is always fetched too, as the fallback source.

### 12.2 Engine (inline in `index.html`'s existing `<script>` block — no second script file)

| Function | Role |
|---|---|
| `LANGUAGES` | Config array of all 10 target languages, `{code, native, enabled}`. Only `en`/`ja` are `enabled: true`; the other 8 render in the settings menu as disabled "coming soon" rows — enabling one is a one-line flag flip plus its dictionary file. |
| `loadLanguage(code)` | Fetches and caches a dictionary in `translationsCache`. |
| `tr(key, params)` | Dynamic-string helper for JS-generated text (calc warnings/badges, toasts, the `exportReport()` document, mailto body). Does `{param}` template substitution and falls back to English, then to the raw key, if a key is missing. **Named `tr()`, not `t()`** — `t` already shadows a local variable in several existing functions (`exportReport()`'s id-lookup helper, `calcZFactor()`'s temperature local; the latter's *reduced-temperature-ratio* local was also renamed `pr`/`trr` to avoid colliding with `tr()` itself — a pure rename, zero calculation change). |
| `applyTranslations()` | Walks `[data-i18n]` (textContent), `[data-i18n-title]`, `[data-i18n-aria]`, `[data-i18n-placeholder]` and sets the matching text/attribute. No `data-i18n-html` variant exists by design — translation files stay plain text with no injection surface; labels mixing a translatable word with a literal symbol (e.g. "MASS FLOW W", "DYNAMIC VISCOSITY (μ)") split the literal symbol into its own sibling `<span>` instead. |
| `setLanguage(code)` | Persists `localStorage['og_lang']`, syncs `<html lang>`, re-runs `applyTranslations()` + `enhanceAccessibility()` (see 12.4), refreshes client-side calculator output via the existing `recomputeAll()`, and marks server-backed results (ΔP/PSV/Flow Regime badges) stale via the existing `markResultStale()` convention rather than re-firing an API call. |
| `applyAwaitingBadgeDefaults()` | Re-translates the idle-state badge text ("Awaiting Calc...", "Run calculation to see intermediate values…", etc.) without stomping a live result already showing in a different language. |

### 12.3 Switcher UI

Two-part control in the header (`.flex.items-center.justify-between.mb-4` row), not in the horizontally-scrolling tab `<nav>`:
- **Quick toggle** — `EN` / `日本語` segmented buttons, visually matching the app's existing Abs/Gauge-style toggle-button pattern.
- **Settings menu** — a gear-icon button opens a dropdown listing all 10 `LANGUAGES` entries; enabled ones are clickable, pending ones show a muted "coming soon" tag.

### 12.4 Bundled fixes (each was necessary for correct language switching, not scope creep)

- `enhanceAccessibility()`'s three `aria-label` setters were guarded ("if not already set") and would have silently frozen after the first language switch; they are now unconditional (idempotent) and are re-run from `setLanguage()`.
- `setHVMode()`'s direct DOM-text overwrite of `out-ghv-label` is now routed through `tr()`, and `applyTranslations()` re-syncs that label from the live `hvMode` state (not a static key) so it survives a language switch mid-session.
- `calcPSV()`'s "Enter required input(s)" message previously baked in English pluralization (`'input' + (n > 1 ? 's' : '')`); replaced with distinct singular/plural translation keys, since Japanese (and several of the pending 8 languages) has no plural marking.
- `markResultStale()`'s appended suffix (previously the hardcoded literal `' · inputs changed — recalculate'`) is now translated via `tr()`.

### 12.5 Translation scope — Milestone 1

**Translated (EN ⇄ JA):** General, Basic Eng, Advanced, Safety tabs (§4.1–4.4); the floating action bar; the Report form; the module-config modal; every JS-generated dynamic string across `calcGHV()`, `calcDeltaPressure()`, `calcFlowRegime()`, `calcPSV()`, `showToast()`, and `exportReport()`'s full standalone document (which also now sets its own `<html lang>`).

**Out of scope for Milestone 1** (§4.5 tabs; ~4,300 words, deferred to Milestone 3): How To Use, Theory, Terms of Use, Privacy Policy.

**Never translated, by design, in any language:** chemical formulas, SI/imperial unit symbols, standard/code citations (JIS K 2301, API 520/526, ISO 6578, ASTM D1250, CODATA, API RP 14E), engineering variable symbols (W, P1, Kd, θ, ω, Re, …), version strings, the §9 reference test-vector values (byte-identical across languages by requirement), proper nouns, the developer's email.

**Not yet localized (server side):** the three Python endpoints (§5) still return English prose for status/error text. `flowregime.py` already returns a machine-readable `regime_key` alongside its English `regime` label (§5.3) — the ~10+ other message/error branches across the three files are unkeyed. See DEVELOPMENT_PLAN.md §6 Milestone 4 (optional).

**Number formatting is unchanged and language-independent:** `toLocaleString('en-US', …)` applies regardless of UI language — a deliberate decision (avoids decimal-comma ambiguity on values that get copy/pasted or shared cross-language), not a gap.
