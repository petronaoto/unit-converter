# CLAUDE.md — O&G Engineering Converter

Project memory for Claude Code. Read and follow all rules below in every session.

## Project Overview

- **App**: O&G Engineering Converter v2.3.1 — a control-room-ready unit conversion and engineering calculation suite for the Oil & Gas / LNG sector.
- **Developer**: Naoto Yamabe (petro.naoto@gmail.com)
- **Live deployment**: Vercel (auto-deploys from `main` branch on GitHub)
- **Architecture**: Hybrid Edge-Server
  - `index.html` — single-file frontend: vanilla JavaScript + Tailwind CSS via CDN. No build step. All standard conversions and JIS K 2301 compositional calculations run client-side.
  - `api/dp_calculator.py` — Vercel serverless Python: pipe ΔP (Darcy-Weisbach + iterative Colebrook-White, HEM two-phase).
  - `api/psv_calculator.py` — Vercel serverless Python: API 520 Part I PRV sizing (§5.6 gas, §5.7 steam, §5.8/§5.9 liquid, §5.10 two-phase Omega method).
  - `api/flowregime.py` — Vercel serverless Python: two-phase flow regime map (seaborn/matplotlib server-side PNG rendering). Vertical map (Hewitt & Roberts type, j_G vs j_L) when |θ| ≥ 30°, horizontal map (Baker type, G_G vs G_L) otherwise; θ = asin(Δz/L). Reads the same payload as dp_calculator.
  - `requirements.txt` — Python deps for flowregime.py only (numpy/matplotlib/seaborn).
  - `README.md` — project documentation.

## CRITICAL Preservation Rules

1. **NEVER simplify, refactor, remove, or rename any existing feature, function, element ID, or constant unless explicitly instructed.** Silent feature loss is the most serious failure mode in this project.
2. **Make surgical, minimal diffs.** Do not regenerate whole files or whole sections to apply a small change.
3. **Do not "improve" working code** (formatting, style, modernization) unless asked.
4. **Element IDs are an API.** JavaScript references HTML IDs extensively (`out-ghv`, `flow-mass-in-u`, `psv-*`, `dp-*`, etc.). Never change an ID without updating every reference, and only when instructed.
5. **Before committing, verify no feature was dropped**: tabs (General / Basic Eng / Advanced / Safety / How To Use / Theory / Terms / Privacy / Report), custom modules, copy buttons, all toggles (Abs/Gauge, HHV/LHV, VOL/MOL, MASS/MOL), the Flow Regime card (map image + Three.js 3D animation), and all three serverless API integrations must all still exist.

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
- Tag releases: `git tag -a vX.Y -m "..."` then `git push origin vX.Y`. Hotfixes use vX.Y.Z.
- Never force-push to `main`. Never commit without showing the diff first.
- Pushing to `main` triggers a live Vercel deployment — confirm with Naoto before pushing anything non-trivial.

## Local Development & Testing

- `vercel dev` is required to test the two Python API endpoints locally (opening index.html directly breaks the Advanced ΔP and Safety PSV calculators).
- Test API endpoints with curl POSTs to `/api/dp_calculator` and `/api/psv_calculator` after modifying them.
- `api/dp_calculator.py` and `api/psv_calculator.py` use only the standard library (`json`, `math`, `http.server`) — do not add dependencies to them. `api/flowregime.py` additionally uses numpy/matplotlib/seaborn, declared in `requirements.txt` — do not add further dependencies.
- Flow Regime reference case: the v2.3 default ΔP inputs (ID=4 in, L=100 m, Δz=70.711 m, vapor 150 kg/h @ 10 kg/m³ / 0.012 cP, liquid 7,300 kg/h @ 500 kg/m³ / 0.12 cP) must classify as **Churn / Slug Flow, θ = +45.0°, vertical map** (j_G ≈ 0.514 m/s, j_L ≈ 0.500 m/s).
- Unit-factor convention (dp_calculator.py & flowregime.py): every `*_m` select value is a **multiply-to-SI** factor — flow×factor→kg/s, density×factor→kg/m³ (kg/m³=1, lb/ft³=16.0185), viscosity×factor→Pa·s. Density was fixed in v2.3.1 (was erroneously dividing); always multiply.

## Engineering Standards References

- JIS K 2301:2011 — calorific value, density, SG, Wobbe index from composition.
- ISO 6578:1991 — LNG density (Klosek-McKinley).
- API Standard 520 Part I, 9th Ed. (2014) — PRV sizing; API 526 orifice areas D–T.
- CODATA 2018 — gas constant.
- Colebrook & White (1939) — friction factor.

## Communication Preferences

- Explain proposed changes as targeted diffs before applying.
- When uncertain whether something is a feature or a bug, ASK — do not assume.
- Responses about engineering values should show the verification calculation.
