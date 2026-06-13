# O&G Engineering Converter — v2.3.1

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
- **Z-Factor Estimator** — quick natural-gas compressibility via Papay's equation.

### 2. Advanced Process Engineering (serverless-backed)

- **Compositional GHV & Flow Calculator**
  - Strict adherence to **JIS K 2301:2011** for cascading rounding, Wobbe Index, and Maximum Combustion Potential (MCP).
  - LNG liquid density via the **Klosek-McKinley** method (ISO 6578:1991).
- **Pipe Delta Pressure (Fanning)**
  - Pressure drop across vapor, liquid, and two-phase (Homogeneous Equilibrium Model) regimes.
  - Python backend solves the **Colebrook-White** equation implicitly.
- **Flow Regime Visualizer** *(new in v2.3)*
  - Classifies the two-phase flow pattern from the Pipe ΔP inputs on simplified **Hewitt & Roberts** (vertical) / **Baker** (horizontal) regime maps, selected by pipe inclination θ = asin(Δz / L).
  - Maps are rendered server-side with Python **seaborn** (`/api/flowregime`) and paired with a conceptual **Three.js 3D animation** of the flow pattern, speed, and inclination.

### 3. Safety

- **API 520 PRV Sizing** — required orifice areas for Gas, Liquid, Steam, and Two-Phase (Omega method) relief scenarios per API Standard 520 Part I, with API 526 orifice-letter selection.

---

## 📜 Engineering Standards

| Standard | Scope |
|---|---|
| **JIS K 2301:2011** | Calorific value, density, relative density & Wobbe index from gas composition |
| **ISO 6578:1991** | Refrigerated hydrocarbon liquids — static measurement (LNG density) |
| **API 520 Part I (9th Ed., 2014)** | Sizing, selection & installation of pressure-relieving devices |
| **Colebrook & White (1939)** | Implicit turbulent friction-factor equation |
| **Hewitt & Roberts (1969) · Baker (1954)** | Two-phase flow regime maps (simplified, indicative) |
| **CODATA 2018** | Universal gas constant R = 8.31446262 J/(mol·K) |

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

© 2026 Naoto Yamabe. All rights reserved.
