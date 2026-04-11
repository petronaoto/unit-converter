O&G Engineering Converter (V2.2)
📌 Objective
The O&G Engineering Converter is a high-precision, control-room-ready suite of engineering tools designed specifically for the Oil & Gas and LNG sectors.

Built to replace fragmented, legacy Excel spreadsheets, this application provides process engineers, operators, and facility managers with instantaneous, standards-compliant thermodynamic and hydraulic calculations accessible directly from a web browser.

🏗️ Development Policies & Architecture
This project strictly adheres to a Hybrid Edge-Server Architecture to maximize both client responsiveness and backend mathematical integrity.

UI & Lightweight Computation (Client-Side): The frontend is built with vanilla JavaScript and Tailwind CSS (via CDN) for zero-build-step deployment. Standard unit conversions, input validation, and layout rendering are handled instantaneously in the browser to ensure a frictionless user experience.

Iterative Mathematical Engines (Serverless Python): Heavy, standards-governed calculations that require complex iterations (e.g., Colebrook-White friction factors, API 520 critical pressure ratios) are explicitly decoupled from the UI thread. These are offloaded to Python backend endpoints (/api/) deployed as Vercel Serverless Functions.

Stateful yet Stateless UX:
The application utilizes browser localStorage for the Custom Module Generator. This allows users to persist custom unit conversions across sessions without the overhead or privacy concerns of an external database.

Graceful Degradation:
Client-side asynchronous fetch requests are wrapped in robust try/catch blocks. If a serverless function experiences a cold-start timeout or receives malformed data, the UI updates with safe, contextual error badges rather than failing catastrophically.

Self-Contained Documentation:
All operational manuals and theoretical proofs are embedded natively within the application using CSS-rendered wireframes, eliminating the need to maintain or link out to external wikis.

⚙️ Core Features & Capabilities
1. General & Basic Engineering
Standard Conversions: Bidirectional synchronization for Gas Volume (Nm³ ↔ scf), Pressure, Temperature, and Heating Value.

Custom Module Generator: Users can dynamically instantiate custom conversion cards (e.g., metric tons to barrels) that serialize to local browser cache.

Pipe Volume: Rapid capacity calculations across mixed metric/imperial units.

Z-Factor Estimator: Quick natural gas compressibility estimation using Papay's equation.

2. Advanced Process Engineering (Serverless Backed)
Compositional GHV & Flow Calculator:

Strict adherence to JIS K 2301:2011 for cascading rounding logic, Wobbe Index, and Maximum Combustion Potential (MCP).

LNG Liquid Density calculation utilizing exact linear temperature intercepts (Klosek-McKinley derived models).

Pipe Delta Pressure (Fanning):

Calculates pressure drop across vapor, liquid, and two-phase (Homogeneous Equilibrium Model) regimes.

Python backend solves the Colebrook-White equation implicitly.

API 520 PRV Sizing:

Calculates required orifice areas for Gas, Liquid, Steam, and Two-Phase (HEM) relief scenarios per API Standard 520 Part 1.

📜 Engineering Standards Compliance
The algorithms within this repository are rigorously calibrated against the following standards:

API 520 Part 1: Sizing, Selection, and Installation of Pressure-Relieving Devices.

JIS K 2301: Fuel gases for natural gas - Calculation of calorific value, density, relative density, and Wobbe index from composition.

ISO 6578: Refrigerated hydrocarbon liquids - Static measurement - Calculation procedure.

🚀 Deployment & Local Setup
This repository is optimized for deployment on Vercel. Vercel's build engine automatically detects the api/ directory and provisions the Python scripts as serverless endpoints.

To run locally for development:
Because the application relies on Python serverless functions, opening index.html directly in a browser will break the Advanced Tab calculators. You must use the Vercel CLI.

Install the Vercel CLI:

Bash
npm i -g vercel
Navigate to the project root and start the local development server:

Bash
vercel dev
Open http://localhost:3000 in your browser.

🔒 Privacy & Data Policy
Zero Data Harvesting: This application does not track, store, or transmit personal user data to external servers. All "Custom Modules" created by the user are stored exclusively within the user's local browser storage (localStorage). The backend API endpoints are entirely stateless.

⚠️ Disclaimer
The calculations and conversions provided by this application are for general reference and convenience only. Under no circumstances should the outputs of this application be used as the sole basis for critical engineering decisions, financial billing, process safety, or regulatory compliance.

© 2026 Naoto Yamabe. All rights reserved.
