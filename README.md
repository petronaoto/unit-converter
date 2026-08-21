# O&G Engineering Converter — v3.8

A high-precision, control-room-ready suite of engineering tools for the **Oil & Gas** and **LNG** sectors.

Built to replace fragmented, legacy Excel spreadsheets, this application gives process engineers, operators, and facility managers instantaneous, standards-compliant thermodynamic and hydraulic calculations — directly from a web browser.

🔗 **Live:** deployed on Vercel (auto-deploys from `main`)
📦 **Repository:** <https://github.com/petronaoto/unit-converter>

---

## 📌 Objective

Provide a single, trustworthy, browser-based toolkit for the everyday unit conversions and engineering calculations used across gas processing and LNG facilities — fast enough for control-room use, yet traceable to the governing standards.

---

## 🏗️ Architecture & Development Policy

The project follows a **Hybrid Edge-Server Architecture** to balance client responsiveness with backend mathematical integrity.

| Layer | Technology | Responsibility |
|---|---|---|
| **Frontend** | Vanilla JavaScript + Tailwind CSS (CDN), Three.js (CDN) | UI, standard conversions, JIS K 2301 compositional calcs, 3D flow animation — all client-side, zero build step |
| **Serverless** | Python on Vercel (`/api/`) | Iterative / heavy calculations decoupled from the UI thread |
| **Persistence** | Browser `localStorage` | Stores user-created Custom Modules — no external database |

**Guiding principles**

- **Decoupled math engines.** Standards-governed iterative calculations (Colebrook-White friction factor, API 520 critical-pressure ratios, server-side regime-map rendering) run in Python serverless functions, not the browser.
- **Graceful degradation.** Client `fetch` calls are wrapped in `try/catch`; cold-start timeouts or malformed data surface as contextual error badges rather than hard failures.
- **Self-contained documentation.** Operational manuals and theory are embedded natively in the app (How To Use / Theory tabs) — no external wikis to maintain.

---

## ⚙️ Core Features

### 1. General & Basic Engineering

- **Standard conversions** — bidirectional sync for Gas Volume (Nm³ ↔ scf), Pressure, Temperature, and Heating Value.
- **Custom Module Generator** — dynamically create conversion cards (e.g. tons ↔ barrels) that persist to local browser cache.
- **Pipe Volume** — rapid capacity calculations across mixed metric/imperial units.
- **Z-Factor Estimator** — quick natural-gas compressibility via Papay's equation (flags inputs outside the Pr/Tr validity envelope).
- **Petroleum Gravity** *(new in v2.4)* — three-way °API ↔ specific gravity ↔ density (water at 60 °F).
- **Viscosity converter** *(new in v2.4)* — dynamic (cP / Pa·s) ↔ kinematic (cSt / m²/s) via density.
- **Mass ↔ Volumetric Flow** *(new in v2.4)* — flow-rate conversion by fluid density.

### 2. Advanced Process Engineering (serverless-backed)

*(v3.6)* The Advanced tab is two-layered: a segmented strip with three sub-tabs — **Gas Quality & LNG Cargo**, **Hydraulics** and **GT Fuel** (formerly its own top-level tab). Your last sub-tab is remembered and share links open the exact one.

- **Compositional GHV & Flow Calculator**
  - Strict adherence to **JIS K 2301:2011** for cascading rounding, Wobbe Index, and Maximum Combustion Potential (MCP).
  - LNG liquid density via the **Klosek-McKinley** method (ISO 6578:1991).
- **LNG Cargo Estimator** *(new in v3.5)* — pick one of 36 representative LNG carriers (each row cites its own public source; Wikimedia Commons photos with credits) or type a capacity, set the loading limit, and read the cargo as t, kNm³ / MMscf and TBtu (HHV basis) — loaded and delivered after heel and boil-off — straight from the composition above.
- **Pipe Delta Pressure (Darcy-Weisbach)**
  - Pressure drop across vapor, liquid, and two-phase regimes.
  - Python backend solves the **Colebrook-White** equation implicitly.
  - *(new in v2.4)* Also reports Reynolds number, Darcy friction factor, and an **API RP 14E erosional-velocity** check (configurable C-factor), and cross-links the classified flow regime.
  - *(new in v3.7)* Selectable two-phase frictional correlation: **HEM** (default), **Lockhart-Martinelli** (Chisholm C), **Müller-Steinhagen-Heck** (1986) or **Friedel** (1979, with a surface-tension input). Static head, fittings and the velocity/Re/f readouts stay on the homogeneous basis.
- **Flow Regime Visualizer** *(new in v2.3)*
  - Classifies the two-phase flow pattern from the Pipe ΔP inputs on simplified **Hewitt & Roberts** (vertical) / **Baker** (horizontal) regime maps, selected by pipe inclination θ = asin(Δz / L).
  - Maps are rendered server-side with Python **seaborn** (`/api/flowregime`) and paired with a conceptual **Three.js 3D animation** of the flow pattern, speed, and inclination.
  - *(rebuilt in v3.7)* The animation scales layer depths and film thicknesses from the no-slip holdup, and adds a mode strip — View (Exterior / Cutaway / Inside the pipe), a Regime preview override (flagged PREVIEW), playback speed and pause — with drag-orbit and scroll zoom.

### 3. Safety

- **API 520 PRV Sizing** — required orifice areas for Gas, Liquid, Steam, and Two-Phase (Omega method) relief scenarios per API Standard 520 Part I, with API 526 orifice-letter selection.
  - *(new in v3.8)* Every pressure input (P1, P2, Ps, Po, Pa) has its own unit drop-down (psi · kPa · bar · MPa · Pa · atm · kg/cm²), an **Abs/Gauge** toggle and a ⇩ button that imports the value from the General tab's Pressure card; the card converts to the absolute (or, for liquid, gauge) basis API 520 expects before sizing.
  - *(new in v3.8)* The card opens pre-filled — gas/vapor with a case that sizes to **orifice H**, the other modes with their documented reference cases — so CALCULATE ORIFICE SIZE gives a result in one click.

### 4. Productivity *(new in v2.4)*

- **Export PDF report** — one-click printable summary of every active calculation (browser "Save as PDF").
- **Share links** — encode the full input set into the URL for handover/collaboration (computed entirely client-side).
- **Session auto-restore** — last inputs and UI preferences persist in browser local storage.
- **Out-of-range guards** — LNG density (ISO 6578 108–120 K), composition, and Papay Z-factor flag extrapolated inputs instead of silently clamping.
- **UX & accessibility polish** *(new in v2.5)* — Enter-to-calculate, instant input-validation hints and stale-result flags on the server-backed cards; jump links + back-to-top on the long documentation tabs; ARIA tab semantics; Export falls back to an HTML download when pop-ups are blocked.

### 5. Engineering additions *(v2.8)*

- **Gas Property Estimator** *(Basic Eng)* — gas viscosity (Lee-Gonzalez-Eakin 1966), sonic velocity and the Joule-Thomson coefficient from one gravity / pressure / temperature / k input set, all chained to the same Papay Z as the Z-Factor card.
- **Crane TP-410 fittings** *(ΔP card)* — twelve fitting types; ΣK·ρv²/2 added to the pressure drop, with the equivalent length reported alongside. Optional and off by default.
- **NORSOK P-001 line-sizing screen** — velocity and frictional ΔP/100 m against per-service criteria, with a WITHIN / NEAR / EXCEEDS verdict.
- **Mobile navigation** — the nine-tab bar becomes a dropdown below tablet width (the three Advanced sub-tabs appear as indented rows).
- **Share links carry custom modules** — state format v:2, behind a sanitizing import boundary.
- **Automated regression suite** — 242 pytest tests across 13 modules, plus GitHub Actions, guarding every documented reference vector on each change.

### 6. Internationalization *(v2.6–v2.7)*

- **10 UI languages, fully live** *(v2.7)* — English, 日本語, 中文, 한국어, ไทย, Bahasa Indonesia, Русский, Español, Français, and Deutsch, selectable from the header's quick toggle and settings menu. Every language covers the complete working tool (General, Basic Eng, Advanced, Safety, action bar, Report form, module modal, all dynamic calculator messages) **and** all four documentation tabs (How To Use, Theory, Terms of Use, Privacy Policy).
- **Default English, persistent choice** — first-time visitors always land in English; a returning visitor's language choice is remembered; a Share link can carry an explicit language so a shared case opens the way the sender configured it.
- **English is authoritative** — numbers keep en-US point-decimal formatting in every language (a deliberate anti-ambiguity decision), and the Terms/Privacy pages in every language carry a governing-language note stating the English version prevails.
- Calculation logic and reference values are unaffected and reproduce byte-identically in all 10 languages — see `docs/DEVELOPMENT_PLAN.md` for the remaining i18n roadmap item (server-side message localization, Milestone 4).

---

## 📜 Engineering Standards

| Standard | Scope |
|---|---|
| **JIS K 2301:2011** | Calorific value, density, relative density & Wobbe index from gas composition |
| **ISO 6578:1991** | Refrigerated hydrocarbon liquids — static measurement (LNG density) |
| **API 520 Part I (9th Ed., 2014)** | Sizing, selection & installation of pressure-relieving devices |
| **API RP 14E (5th Ed., 1991)** | Erosional-velocity screening criterion Vₑ = C/√ρ (ΔP card) |
| **Colebrook & White (1939)** | Implicit turbulent friction-factor equation |
| **Hewitt & Roberts (1969) · Baker (1954)** | Two-phase flow regime maps (simplified, indicative) |
| **CODATA 2018** | Universal gas constant R = 8.31446262 J/(mol·K) |

---

## 📚 Documentation

| Document | Contents |
|---|---|
| [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) | Vision, personas, architecture principles, full version history, the i18n program milestones, and the v3.4 outcome with the v3.5 candidates |
| [docs/SPECIFICATION.md](docs/SPECIFICATION.md) | Detailed engineering spec of every module, the three API contracts, state/share-link format, calculation rules, reference test vectors, and the known-issues register |
| [docs/MARKETING.md](docs/MARKETING.md) | Positioning, target segments, SEO/content plan, channels, and privacy-compatible analytics options |

The in-app **How To Use** and **Theory** tabs remain the end-user manual; the `docs/` folder is the maintainer/contributor reference.

---

## 🚀 Deployment & Local Setup

This repository is optimized for **Vercel**, which auto-detects the `api/` directory and provisions the Python scripts as serverless endpoints.

> ⚠️ Opening `index.html` directly breaks the Advanced ΔP / Flow Regime and Safety PRV calculators, because they depend on the Python serverless functions. Use the Vercel CLI.

```bash
# 1. Install the Vercel CLI
npm i -g vercel

# 2. From the project root, start the local dev server
vercel dev

# 3. Open the app
#    http://localhost:3000
```

**Python dependencies** (`requirements.txt`) are required only by `api/flowregime.py` (numpy / matplotlib / seaborn). `api/dp_calculator.py` and `api/psv_calculator.py` use the standard library only.

---

## 🔒 Privacy & Data Policy

- **Zero data harvesting** — no personal data is tracked, stored, or transmitted.
- **Local-only state** — Custom Modules live exclusively in your browser's `localStorage`.
- **Stateless APIs** — serverless endpoints process numerical engineering inputs transiently and return a result (the Flow Regime endpoint also returns a rendered map image); nothing is logged or tied to a user.

See the in-app **Privacy Policy** and **Terms of Use** tabs for full detail.

---

## ⚠️ Disclaimer

The calculations and conversions provided by this application are for **general reference and convenience only**. Under no circumstances should the outputs be used as the sole basis for critical engineering decisions, financial billing, process safety, or regulatory compliance. The Flow Regime visualization uses simplified, approximate regime-map boundaries and a conceptual 3D animation — it is for qualitative orientation only.

---

## 📄 Licence

Released under the **[MIT Licence](LICENSE)** — free to use, copy, modify and redistribute, including commercially, provided the copyright notice and licence text are retained.

That covers this project's own code, design and documentation. It grants **no rights in third-party material** the project cites or transcribes: the engineering standards behind the calculations (JIS K 2301, ISO 6578, API 520/526, NORSOK P-001, IAPWS-IF97 and others) remain the property of their issuing bodies and are not reproduced here; the LNG reference compositions come from GIIGNL Information Paper No. 1; and the gas-turbine catalogue figures come from the manufacturers' own published literature. See the `LICENSE` file for the full attribution list.

---

© 2026 Naoto Yamabe. Licensed under the MIT Licence.
