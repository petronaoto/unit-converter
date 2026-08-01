# CLAUDE.md — `api/` (Vercel serverless Python endpoints)

Scoped project memory for the three Python API endpoints. The root `CLAUDE.md` holds the
project-wide rules (preservation policy, git workflow, version-bump checklist, JIS K 2301
client-side calculation rules); everything below is specific to this directory and applies
in addition to — never instead of — the root rules.

## Endpoints

- `dp_calculator.py` — pipe ΔP (Darcy-Weisbach + iterative Colebrook-White, HEM two-phase).
  v2.4: also returns Reynolds number `Re`, `re_regime`, Darcy friction factor `f`, the split
  `dpFric`/`dpStatic` terms, mixture density `rho_mix`, and an **API RP 14E erosional-velocity**
  check (`v_ero`, `ero_ratio`) computed from the payload's `cfactor` (default 100).
- `psv_calculator.py` — API 520 Part I PRV sizing (§5.6 gas, §5.7 steam, §5.8/§5.9 liquid,
  §5.10 two-phase Omega method); API 526 orifice letters D–T.
- `flowregime.py` — two-phase flow regime map (seaborn/matplotlib server-side PNG rendering).
  Vertical map (Hewitt & Roberts type, j_G vs j_L) when |θ| ≥ 30°, horizontal map (Baker type,
  G_G vs G_L) otherwise; θ = asin(Δz/L). Reads the same payload as dp_calculator. Returns
  `regime_key` alongside its English `regime` label (see `docs/SPECIFICATION.md` §5.3).

## Dependency Rules — DO NOT VIOLATE

- `dp_calculator.py` and `psv_calculator.py` use **only the Python standard library**
  (`json`, `math`, `http.server`) — do not add dependencies to them.
- `flowregime.py` additionally uses numpy/matplotlib/seaborn, declared in the repo-root
  `requirements.txt` — do not add further dependencies there either.

## Unit-Factor Convention (dp_calculator.py & flowregime.py)

Every `*_m` select value sent by the frontend is a **multiply-to-SI** factor:
flow×factor→kg/s, density×factor→kg/m³ (kg/m³ = 1, lb/ft³ = 16.0185), viscosity×factor→Pa·s.
Density was fixed in v2.3.1 (was erroneously dividing); **always multiply**.

## Reference Cases — MUST REPRODUCE EXACTLY

Re-verify after ANY change to the corresponding file, before committing.

- **dp_calculator** (v2.3 default ΔP inputs: ID=4 in, L=100 m, Δz=70.711 m, vapor 150 kg/h
  @ 10 kg/m³ / 0.012 cP, liquid 7,300 kg/h @ 500 kg/m³ / 0.12 cP):
  ΔP_total ≈ **176.9 kPa** (dpFric ≈ 2.34 kPa + dpStatic ≈ 174.6 kPa), vel ≈ 1.014 m/s,
  Re ≈ **2.20×10⁵** (turbulent), Darcy f ≈ **0.0184**, ρ_mix ≈ 251.7 kg/m³,
  V_e ≈ **7.72 m/s** at C=100 (v/V_e ≈ 0.13 → WITHIN LIMIT).
- **flowregime** (same inputs): must classify as **Churn / Slug Flow, θ = +45.0°, vertical map**
  (j_G ≈ 0.514 m/s, j_L ≈ 0.500 m/s).
- **psv_calculator** (added v2.8 — five USC cases, one per sizing mode; full inputs in
  `docs/SPECIFICATION.md` §9 Vector 4, enforced by `tests/test_psv_calculator.py`):
  §5.6 gas → **5.7047 in²** (orifice P), C = 346.9764, P_cf = 53.045 psia;
  §5.7 steam → **1.7030 in²** (K), K_N = 1.0115;
  §5.8 liquid certified → **4.1690 in²** (N);
  §5.9 liquid non-certified → **4.1001 in²** (N);
  §5.10 two-phase → **19.0114 in²** (T), ω = 1.4817, η_c = 0.6564, **P_c = 52.971 psia**,
  G = 590.891.

## Local Testing

- `vercel dev` is required to test these endpoints locally (opening index.html directly
  breaks the Advanced ΔP and Safety PSV calculators).
- Test with curl POSTs to `/api/dp_calculator` and `/api/psv_calculator` after modifying them.

## Governing Standards for This Directory

- API Standard 520 Part I, 9th Ed. (2014) — PRV sizing; API 526 orifice areas D–T (psv_calculator).
- API RP 14E (5th Ed., 1991) — erosional-velocity screening criterion V_e = C/√ρ (dp_calculator, v2.4).
- Colebrook & White (1939) — friction factor (dp_calculator).

## i18n Note (roadmap M4, not yet implemented)

Server-generated status/error text is English prose regardless of UI language. The planned
fix (i18n Milestone 4) is to return machine-readable status/error **keys** in addition to the
English text — an additive, stdlib-safe payload change. `flowregime.py` already follows this
pattern with `regime_key`; the other message/error branches across the three files remain unkeyed.

## Automated Tests (v2.8)

`pytest` from the repo root. Details in `docs/SPECIFICATION.md` §13; what matters here:

- The dp / psv / flowregime reference cases above are now **enforced on every push and PR**,
  not just by this file asking you to re-verify them. They still need re-verifying by hand
  when you change the physics, but a regression will no longer reach `main` silently.
- **`dp_calculator.py` is tested through `do_POST` with a fake request**, not by calling a
  `compute()` function — because it does not have one, and adding one would be a refactor
  of working code. Do not add a `compute()` "to make it testable"; the harness in
  `tests/conftest.py` already handles it.
- **The stdlib-only rule is now machine-enforced.** `tests/test_architecture.py` parses the
  AST of `dp_calculator.py` and `psv_calculator.py` and fails on any non-stdlib import, and
  the `stdlib-only` CI job installs nothing but pytest. Adding a dependency to either file
  breaks the build immediately.
- **The multiply-to-SI convention is machine-enforced too.** The v2.3.1 density bug
  (dividing rather than multiplying) is guarded by tests that deliberately use lb/ft³,
  because the reference case sends kg/m³ — whose factor is 1.0, making multiply and divide
  indistinguishable. Any new unit-factor code needs a test with a factor that is not 1.

## v2.8 — Fittings & machine-readable keys (dp_calculator.py)

- **`k_total` (optional, default 0)** is ΣK for the run's fittings, summed CLIENT-side from
  the Crane TP-410 table in `index.html`. The endpoint only multiplies:
  `dpFittings = k_total · ρ · v² / 2`, added into `dpPa`. **The default of 0 is
  load-bearing** — an omitted or non-positive `k_total` makes `dpFittings` exactly `0.0`,
  so every pre-v2.8 payload and share link still reproduces ΔP_total ≈ 176.9 kPa.
  Negative values are clamped to 0. Keeping the Crane table client-side is what allows
  this file to stay standard-library-only.
- **`L` still means STRAIGHT-pipe length.** The frontend divides by it to render ΔP per
  unit length. `L_eq` (= ΣK·D/f, at the *actual flowing* f) and `L_eff` (= L + L_eq) are
  separate fields. Do not fold L_eq into `L`.
- **`phase_key`** (`vapor`/`liquid`/`twophase`) and **`re_regime_key`**
  (`laminar`/`transitional`/`turbulent`) accompany the English `badge`/`re_regime`
  strings — the i18n Milestone 4 pattern `flowregime.py` already uses for `regime_key`.
  The frontend branches on these, never on the English text.
- **Reference case (Vector 7, `docs/SPECIFICATION.md` §9):** ΣK = 5.3760 on the Vector 2
  hydraulics → dpFittings ≈ **695.853 Pa**, L_eq ≈ **29.7586 m**, ΔP_total ≈ **177.625 kPa**.
  Re-verify alongside Vector 2 after touching this file.
