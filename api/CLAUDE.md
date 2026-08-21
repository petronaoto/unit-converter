# CLAUDE.md — `api/` (Vercel serverless Python endpoints)

Scoped project memory for the three Python API endpoints. The root `CLAUDE.md` holds the
project-wide rules (preservation policy, git workflow, version-bump checklist, JIS K 2301
client-side calculation rules); everything below is specific to this directory and applies
in addition to — never instead of — the root rules.

## Endpoints

- `dp_calculator.py` — pipe ΔP (Darcy-Weisbach + iterative Colebrook-White, two-phase).
  v2.4: also returns Reynolds number `Re`, `re_regime`, Darcy friction factor `f`, the split
  `dpFric`/`dpStatic` terms, mixture density `rho_mix`, and an **API RP 14E erosional-velocity**
  check (`v_ero`, `ero_ratio`) computed from the payload's `cfactor` (default 100).
  v3.7: the two-phase FRICTIONAL term is computed by the correlation named in `tp_method`
  (`hem` default / `lm` Lockhart-Martinelli + Chisholm C / `msh` Müller-Steinhagen-Heck /
  `friedel` Friedel 1979, which consumes `sigma` [N/m], default 0.010) via `two_phase_dpdz()`.
  See "v3.7 — Selectable two-phase methods" below.
- `psv_calculator.py` — API 520 Part I PRV sizing (§5.6 gas, §5.7 steam, §5.8/§5.9 liquid,
  §5.10 two-phase Omega method); API 526 orifice letters D–T.
- `flowregime.py` — two-phase flow regime map (seaborn/matplotlib server-side PNG rendering).
  Vertical map (Hewitt & Roberts type, j_G vs j_L) when θ ≥ **+**30°, horizontal map (Baker type,
  G_G vs G_L) otherwise; θ = asin(Δz/L). **The gate is DIRECTIONAL (v3.8.4)** — it was `abs(θ) ≥ 30°`
  until then, which sent downhill lines to Hewitt & Roberts' *upflow* map. That map has no
  stratified region at all, and downward inclination is what most favours stratified flow, so the
  likeliest answer was unreachable. Steep downflow (θ ≤ −30°) now uses Baker and sets
  `downflow_advisory: true` + an `advisory` string; Baker is a horizontal correlation, so it is the
  nearest available basis, not a correct one. Reads the same payload as dp_calculator. Returns
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
  V_e ≈ **7.69 m/s** at C=100 (v/V_e ≈ 0.13 → WITHIN LIMIT). *(v2.8: was 7.72 with the
  old √1.5 constant; the SI constant is now the exact 1.2199033 — see the note below.)*
- **dp_calculator v3.7 methods** (same inputs, `tp_method` set; static head 174.590 kPa in
  every case — SPECIFICATION.md §9 Vector 14): `lm` → dpFric ≈ **4.843 kPa**, total ≈
  **179.433 kPa** (C = 20, X = 6.1663, φ_L² = 4.2697); `msh` → **3.243 kPa** / **177.833 kPa**;
  `friedel` (σ = 0.010) → **4.044 kPa** / **178.634 kPa** (φ_LO² = 3.4294). An ABSENT
  `tp_method` must stay bit-identical to `hem`.
- **flowregime** (same inputs): must classify as **Churn / Slug Flow, θ = +45.0°, vertical map**
  (j_G ≈ 0.514 m/s, j_L ≈ 0.500 m/s). *(Uphill, so v3.8.4's directional gate leaves it
  bit-identical.)*
- **flowregime downflow (v3.8.4)**: the same inputs with `elev` **negated** (θ = −45.0°) must now
  classify on the **horizontal** map with `downflow_advisory: true`, NOT on the vertical map.
  A low-gas downhill case — `v_flow` 5, `l_flow` 2000 kg/h at θ = −45° — must read
  **Stratified** (G_G ≈ 0.171, G_L ≈ 68.5 kg/s·m²); it read **Bubbly** before the fix, which is
  the regression this pins.
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

## v3.0 PR-1 — Error contract hardening (all three endpoints)

- **Every error response carries the superset `{error, message, badge, badgeClass}`**
  (closed §11 #6). dp's error branches each include all four fields inline;
  psv adds the badge fields at `do_POST`'s single exit point — do NOT remove that
  patch-in or add new psv error returns that bypass `_respond` via the handler.
  New error branches in any endpoint must carry the full superset from birth.
- **dp_calculator validation (closed §11 #2, #3):** zero/negative density or viscosity
  on a *flowing* phase → structured `Invalid Input` (a vapor-only payload must NOT
  require liquid properties); a **present** `cfactor` ≤ 0 or non-finite → structured
  error, while an **absent** `cfactor` defaults to 100 — that default is load-bearing
  for pre-v2.4 payloads, like `k_total`'s 0 below.
- **psv_calculator (closed §11 #4, #5):** gas mode rejects `k ≤ 1` before `calc_C`;
  the generic `except` returns a fixed message — never reintroduce `str(e)`.
  Two-phase `Pa ≤ 0` becomes atmospheric (101.325 kPa SI / 14.696 psia USC —
  maintainer decision 2026-08-04). Vector 4 stays on the critical branch
  (P_c = 52.971 psia > atmospheric); do not "simplify" the default back to 0.
- **psv two-phase subcritical mass flux (closed §11 #12):** the Leung bracket is
  `−2·(ω·ln η + (ω−1)(1−η))` — the −2 multiplies the WHOLE bracket. The pre-fix form
  (−2 on the log term only) gave subcritical flux above choked flux and under-sized
  valves ~20–30 % on that branch. The continuity test
  (`test_subcritical_flux_is_continuous_with_the_critical_branch`) pins it: at
  η_a = η_c the subcritical G must reproduce the critical-branch G, because that is
  how η_c is defined. Any future edit that breaks continuity there is wrong.
- **NaN discipline:** validation guards use `not (x > 0)` polarity, never `x <= 0` —
  NaN fails every ordered comparison, so the `<=` form silently admits it and emits
  RFC-8259-invalid `NaN` tokens the browser cannot parse. dp additionally runs an
  `isfinite` sweep over every extracted field. Keep both patterns in new code.
- Error `message` strings are deliberately English prose until i18n Milestone 4
  assigns them keys.

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
  hydraulics → dpFittings ≈ **695.854 Pa**, L_eq ≈ **29.7586 m**, ΔP_total ≈ **177.625 kPa**.
  Re-verify alongside Vector 2 after touching this file.

## v3.7 — Selectable two-phase methods (dp_calculator.py)

- **`tp_method` (optional, default "hem") is load-bearing** exactly like `k_total` and
  `cfactor`: absent/empty/null means HEM, which must reproduce every pre-v3.7 payload
  and share link bit-for-bit (`test_absent_tp_method_reproduces_the_hem_result_exactly`).
  A PRESENT unknown value is a structured `Invalid Input` error, never a silent fallback.
- **The method replaces `dpFric` ONLY.** `dpStatic`, `dpFittings`, `vel`, `Re`, `f`,
  `rho_mix`, `v_ero`, `ero_ratio`, `L_eq` stay on the homogeneous no-slip basis so the
  RP 14E and NORSOK screens are method-independent — machine-enforced by
  `test_method_changes_only_the_frictional_term`. Do not "fix" this by feeding a
  slip-corrected density into the other terms.
- **`sigma` (optional, default 0.010 N/m)** follows the cfactor contract: absent → default;
  present non-positive/non-finite/non-numeric → structured error, regardless of method.
  The UI enters mN/m and sends N/m, mapping blank/zero to 10 mN/m client-side.
- **Friedel requires mu_v < mu_l** (its (1 − mu_v/mu_l)^0.7 term) and returns a structured
  error otherwise. The other methods accept equal viscosities.
- All phase-alone (`lm`) and whole-flow (`msh`/`friedel`) friction factors reuse
  `get_darcy_friction_factor()` at the actual pipe relative roughness — a deliberate
  engineering adaptation (the originals used smooth-pipe Blasius-type factors); keep it
  consistent rather than introducing a second friction model.
- Chisholm C selection threshold is Re < 2300 ("viscous"), matching the friction
  function's laminar switch — pinned across all four regime combinations by
  `test_lm_chisholm_c_follows_the_phase_alone_regimes`.
- New response fields are additive: `tp_method`, `sigma` (always), `phi2` (lm/friedel),
  `lm_X`/`lm_C` (lm). The two-phase badge is "Two-Phase (%s)" % TP_METHOD_LABELS[m];
  the default badge stays exactly "Two-Phase (HEM)".
