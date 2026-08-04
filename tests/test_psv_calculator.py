"""Reference-value regression for api/psv_calculator.py (API 520 Part I, 9th Ed.).

These are **Vector 4** in docs/SPECIFICATION.md §9 — five USC cases, one per sizing mode,
reviewed and approved by the maintainer in v2.8. Before v2.8 no PSV reference vector
existed anywhere in the repo, although the roadmap item named "dp/psv cases".

Provenance: the inputs are the placeholder values already shown in the Safety card's own
fields (index.html `psv-*` placeholders), so they are auditable from the UI. Two
adjustments were made during review:

  * §5.10 two-phase W was halved to 238,715 lb/h so the required area (19.01 in²) lands
    inside the API 526 range on orifice T, rather than over-ranging to `T+`. The
    over-range path is still covered — see test_oversized_requirement_is_flagged.
  * The reported Pc was fixed (see test_twophase_reports_pc_from_relieving_pressure).

Hand-check performed on the gas case (§5.6, USC, k = 1.3):
    C   = 520 * sqrt(1.3 * (2/2.3)^(2.3/0.3)) = 346.98
    pcr = (2/2.3)^(1.3/0.3)                   = 0.5457
    Pcf = 0.5457 * 97.2                       = 53.04 psia
    A   = 53500 / (346.98*0.975*97.2) * sqrt(627/51) = 5.704 in²  -> orifice P (6.38 in²)

Hand-check performed on the two-phase case (§5.10, USC):
    omega = 9 * (0.3629/0.3116 - 1)                    = 1.4817
    eta_c                                              = 0.6564
    G     = 68.09 * 0.6564 * sqrt(80.7/(0.3116*1.4817)) = 590.891
    A     = 0.04 * 238715 / (0.85 * 590.891)            = 19.0114 in² -> orifice T
    Pc    = 0.6564 * 80.7                               = 52.971 psia
"""

import math

import pytest


# ── §5.6 Gas / vapour ────────────────────────────────────────────────────────────

def test_gas_critical_flow(psv_module):
    data = {"W": 53500, "M": 51, "k": 1.3, "T": 627, "Z": 1.0,
            "P1": 97.2, "P2": 0, "Kd": 0.975, "Kb": 1.0, "Kc": 1.0}
    res = psv_module.size_gas(data, "USC")

    assert res["error"] is False
    assert res["area"] == pytest.approx(5.7047, abs=5e-4)
    assert res["area_unit"] == "in²"
    assert res["orifice"] == "P"
    assert res["orifice_area"] == pytest.approx(6.38, abs=5e-3)
    assert res["flow_regime"] == "Critical Flow"
    assert res["C"] == pytest.approx(346.9764, abs=5e-4)
    assert res["Pcf"] == pytest.approx(53.045, abs=5e-3)
    assert res["critical_ratio"] == pytest.approx(0.5457, abs=5e-5)


def test_gas_subcritical_branch(psv_module):
    """Back-pressure above P_cf must switch to the §5.6 subcritical equation."""
    base = {"W": 53500, "M": 51, "k": 1.3, "T": 627, "Z": 1.0,
            "P1": 97.2, "Kd": 0.975, "Kb": 1.0, "Kc": 1.0}
    res = psv_module.size_gas(dict(base, P2=80.0), "USC")

    assert res["error"] is False
    assert res["flow_regime"].startswith("Subcritical Flow")
    # r = 80 / 97.2 = 0.8230
    assert "0.823" in res["flow_regime"]
    # Subcritical relief needs a larger orifice than the same case run critical.
    crit = psv_module.size_gas(dict(base, P2=0), "USC")
    assert res["area"] > crit["area"]


def test_gas_rejects_non_positive_inputs(psv_module):
    for bad in ({"W": 0}, {"M": 0}, {"P1": 0}):
        data = dict({"W": 53500, "M": 51, "k": 1.3, "T": 627, "Z": 1.0,
                     "P1": 97.2, "P2": 0}, **bad)
        res = psv_module.size_gas(data, "USC")
        assert res["error"] is True
        assert "must be > 0" in res["message"]


# ── §5.7 Steam ───────────────────────────────────────────────────────────────────

def test_steam_critical_flow(psv_module):
    data = {"W": 153500, "P1": 1774.7, "Kd": 0.975, "Kb": 1.0, "Kc": 1.0, "KSH": 1.0}
    res = psv_module.size_steam(data, "USC")

    assert res["error"] is False
    assert res["area"] == pytest.approx(1.703, abs=5e-4)
    assert res["orifice"] == "K"
    assert res["orifice_area"] == pytest.approx(1.838, abs=5e-3)
    assert res["flow_regime"] == "Steam — Critical Flow"
    assert res["badge"] == "Steam Critical Flow"
    assert res["KN"] == pytest.approx(1.0115, abs=5e-4)
    assert res["KSH"] == pytest.approx(1.0)


# ── §5.8 / §5.9 Liquid ───────────────────────────────────────────────────────────

def test_liquid_certified(psv_module):
    data = {"Q": 1800, "Gl": 0.9, "mu": 0, "P1": 275, "P2": 0,
            "Kd": 0.65, "Kw": 1.0, "Kc": 1.0}
    res = psv_module.size_liquid_cert(data, "USC")

    assert res["error"] is False
    assert res["area"] == pytest.approx(4.169, abs=5e-4)
    assert res["orifice"] == "N"
    assert res["flow_regime"] == "Liquid — Certified PRV"
    assert res["badge"] == "Liquid (§5.8 Certified)"
    # No viscosity given -> Kv correction skipped entirely.
    assert res["Kv"] == pytest.approx(1.0)
    assert res["Re"] is None


def test_liquid_non_certified(psv_module):
    data = {"Q": 1800, "Gl": 0.9, "mu": 0, "Ps": 250, "P2": 0,
            "Kd": 0.62, "Kw": 1.0, "Kc": 1.0, "Kp": 1.0}
    res = psv_module.size_liquid_noncert(data, "USC")

    assert res["error"] is False
    assert res["area"] == pytest.approx(4.1001, abs=5e-4)
    assert res["orifice"] == "N"
    assert res["flow_regime"] == "Liquid — Non-Certified PRV"
    assert res["badge"] == "Liquid (§5.9 Non-Certified)"


def test_liquid_viscosity_correction_reduces_capacity(psv_module):
    """A viscous liquid must give Kv < 1, hence a LARGER required area."""
    base = {"Q": 1800, "Gl": 0.9, "P1": 275, "P2": 0,
            "Kd": 0.65, "Kw": 1.0, "Kc": 1.0}
    inviscid = psv_module.size_liquid_cert(dict(base, mu=0), "USC")
    viscous = psv_module.size_liquid_cert(dict(base, mu=1000), "USC")

    assert viscous["Kv"] < 1.0
    assert viscous["Re"] is not None
    assert viscous["area"] > inviscid["area"]


# ── §5.10 Two-phase (Omega method) ───────────────────────────────────────────────

TWOPHASE_CASE = {"W": 238715, "vo": 0.3116, "v9": 0.3629, "Po": 80.7, "Pa": 0,
                 "Kd": 0.85, "Kb": 1.0, "Kc": 1.0, "Kv": 1.0}


def test_twophase_critical_omega(psv_module):
    res = psv_module.size_twophase(dict(TWOPHASE_CASE), "USC")

    assert res["error"] is False
    assert res["area"] == pytest.approx(19.0114, abs=5e-4)
    assert res["orifice"] == "T"
    assert res["orifice_area"] == pytest.approx(26.00, abs=5e-3)
    assert res["flow_regime"] == "Two-Phase Critical (Omega)"
    assert res["badge"] == "Two-Phase (Omega Method)"
    assert res["omega"] == pytest.approx(1.4817, abs=5e-5)
    assert res["eta_c"] == pytest.approx(0.6564, abs=5e-5)
    assert res["G"] == pytest.approx(590.891, abs=5e-4)


def test_twophase_reports_pc_from_relieving_pressure(psv_module):
    """FIXED IN v2.8 (closes docs/SPECIFICATION.md §11 issue #1).

    The reported Pc was computed from the back-pressure Pa instead of the relieving
    pressure Po, so it read exactly 0.0 whenever Pa was left at its default — which is
    the default. Sizing was never affected: the internal critical/subcritical decision
    on psv_calculator.py:299 always used eta_c * Po. Only the displayed value was wrong,
    and it is displayed (index.html:3257 pushes it into psv-out-details).

    Pc = eta_c * Po = 0.6564 * 80.7 = 52.971 psia.
    """
    res = psv_module.size_twophase(dict(TWOPHASE_CASE), "USC")
    assert res["Pc"] == pytest.approx(52.971, abs=5e-4)
    assert res["Pc"] == pytest.approx(res["eta_c"] * TWOPHASE_CASE["Po"], abs=1e-3)


def test_twophase_pc_is_independent_of_back_pressure(psv_module):
    """The regression guard for #1: Pc must not move when only Pa changes.

    Pa still (correctly) decides the critical/subcritical branch, so this compares the
    two runs while both remain critical (Pa < Pc = 52.97).
    """
    at_zero = psv_module.size_twophase(dict(TWOPHASE_CASE, Pa=0), "USC")
    at_forty = psv_module.size_twophase(dict(TWOPHASE_CASE, Pa=40), "USC")

    assert at_zero["flow_regime"] == at_forty["flow_regime"] == "Two-Phase Critical (Omega)"
    assert at_forty["Pc"] == pytest.approx(at_zero["Pc"], abs=1e-9)
    assert at_forty["Pc"] == pytest.approx(52.971, abs=5e-4)


def test_twophase_subcritical_branch(psv_module):
    """Back-pressure above Pc must switch to the subcritical mass-flux equation."""
    res = psv_module.size_twophase(dict(TWOPHASE_CASE, Pa=70), "USC")
    assert res["error"] is False
    assert res["flow_regime"] == "Two-Phase Subcritical (Omega)"
    # Pc is a property of Po and omega, so it is unchanged by the branch taken.
    assert res["Pc"] == pytest.approx(52.971, abs=5e-4)


def test_twophase_rejects_v9_below_vo(psv_module):
    """omega < 0 is physically impossible — the two-phase specific volume must expand."""
    res = psv_module.size_twophase(dict(TWOPHASE_CASE, vo=0.3629, v9=0.3116), "USC")
    assert res["error"] is True


# ── Shared helpers ───────────────────────────────────────────────────────────────

def test_critical_pressure_ratio_matches_the_closed_form(psv_module):
    for k in (1.1, 1.2, 1.3, 1.4, 1.667):
        expected = (2.0 / (k + 1.0)) ** (k / (k - 1.0))
        assert psv_module.critical_pressure_ratio(k) == pytest.approx(expected, rel=1e-12)


def test_coefficient_C_matches_the_closed_form(psv_module):
    """C = 520 sqrt(k (2/(k+1))^((k+1)/(k-1))) in USC; the SI constant is 0.03948 x that."""
    for k in (1.1, 1.3, 1.4):
        term = k * (2.0 / (k + 1.0)) ** ((k + 1.0) / (k - 1.0))
        assert psv_module.calc_C(k, "USC") == pytest.approx(520.0 * math.sqrt(term), rel=1e-9)


def test_orifice_selection_picks_the_next_size_up(psv_module):
    """API 526 letters D-T. A required area must never select a smaller orifice."""
    for required in (0.05, 0.110, 0.111, 1.5, 6.0, 25.0):
        letter, area_in2, area_mm2 = psv_module.select_orifice(required)
        assert area_in2 >= required or letter.endswith("+")
        # The mm² column holds API 526's own PUBLISHED figures, which are rounded
        # rather than exact conversions of the in² column (e.g. D is listed as
        # 71.0 mm², where 0.110 in² x 645.16 = 70.9676). Tolerance accommodates the
        # published rounding; a transcription error would be far larger than 0.1 %.
        assert area_mm2 == pytest.approx(area_in2 * 645.16, rel=1e-3)


def test_orifice_exact_boundary_selects_that_letter(psv_module):
    """0.110 in² is exactly API 526 'D' — it must not round up to 'E'."""
    letter, area_in2, _ = psv_module.select_orifice(0.110)
    assert letter == "D"
    assert area_in2 == pytest.approx(0.110)


def test_oversized_requirement_is_flagged_not_silently_capped(psv_module):
    """Above the largest API 526 orifice (T = 26.0 in²) the result must be marked."""
    letter, _, _ = psv_module.select_orifice(100.0)
    assert letter.endswith("+"), f"expected an over-range marker, got {letter!r}"


# ── v3.0 PR-1 hardening (closes docs/SPECIFICATION.md §11 #4, #5, #6) ──────────


def test_gas_k_of_exactly_one_is_a_structured_error(psv_module):
    """FIXED (closes §11 #4): k = 1 raised ZeroDivisionError inside calc_C's
    (k+1)/(k-1) exponent and reached the UI as the literal Python message
    "float division by zero"."""
    res = psv_module.size_gas({"W": 53500, "M": 51, "k": 1.0, "T": 627,
                               "P1": 97.2}, "USC")
    assert res["error"] is True
    assert "k must be > 1" in res["message"]
    assert "division" not in res["message"].lower()


def test_gas_k_below_one_is_rejected_not_silently_computed(psv_module):
    """Same §11 #4 family: k < 1 raised nothing and silently produced a physically
    meaningless area (ideal-gas k = Cp/Cv is > 1 by definition)."""
    res = psv_module.size_gas({"W": 53500, "M": 51, "k": 0.9, "T": 627,
                               "P1": 97.2}, "USC")
    assert res["error"] is True
    assert "k must be > 1" in res["message"]


def test_unexpected_exceptions_no_longer_leak_python_internals(psv_module,
                                                               post_to_handler):
    """FIXED (closes §11 #4): the handler's generic except returned str(e), leaking
    interpreter internals into the UI. A negative absolute temperature still raises
    (math domain error in sqrt) — the response must be the fixed generic message."""
    status, data = post_to_handler(psv_module, {"mode": "gas", "units": "USC",
                                                "W": 53500, "M": 51, "k": 1.3,
                                                "T": -100, "P1": 97.2})
    assert status == 200
    assert data["error"] is True
    assert data["message"] == "Internal calculation error — check the input values."
    assert "domain" not in data["message"] and "division" not in data["message"]


def test_psv_error_responses_carry_the_harmonized_superset(psv_module,
                                                           post_to_handler):
    """§11 #6: psv errors used to carry message but no badge fields. Every error
    shape must now include the full {error, message, badge, badgeClass} superset,
    matching flowregime.py's established schema."""
    cases = [
        {"mode": "gas", "units": "USC", "W": 0, "M": 51, "k": 1.3, "T": 627,
         "P1": 97.2},                                       # validation message
        {"mode": "gas", "units": "USC", "W": 53500, "M": 51, "k": 1.0, "T": 627,
         "P1": 97.2},                                       # k guard
        {"mode": "does-not-exist", "units": "USC"},         # unknown mode
    ]
    for payload in cases:
        status, data = post_to_handler(psv_module, payload)
        assert status == 200
        assert data["error"] is True
        for field in ("message", "badge", "badgeClass"):
            assert field in data, f"missing {field} for {payload.get('mode')}"


def test_twophase_omitted_pa_defaults_to_atmospheric_reference_case_unchanged(psv_module):
    """FIXED (closes §11 #5, maintainer decision 2026-08-04): omitted/zero Pa now
    defaults to atmospheric instead of a perfect vacuum. Vector 4's case has
    Pc = 52.971 psia > 14.696, so it stays on the critical branch bit-for-bit."""
    res = psv_module.size_twophase(dict(TWOPHASE_CASE), "USC")
    assert res["error"] is False
    assert res["flow_regime"] == "Two-Phase Critical (Omega)"
    assert res["area"] == pytest.approx(19.0114, abs=5e-4)


def test_twophase_low_po_with_omitted_pa_is_now_subcritical(psv_module):
    """The behavioral point of §11 #5: with Pa = 0 treated as vacuum, the critical
    branch was unconditional and UNDER-sized whenever the real operating point was
    subcritical. At Po = 20 psia the critical pressure is 0.6564 x 20 = 13.13 psia,
    BELOW atmospheric — a vented system physically cannot be choked there, and the
    subcritical equation must now be used."""
    res = psv_module.size_twophase(dict(TWOPHASE_CASE, Po=20), "USC")
    assert res["error"] is False
    assert res["flow_regime"] == "Two-Phase Subcritical (Omega)"
    assert res["Pc"] == pytest.approx(0.6564 * 20, abs=5e-3)
    # Pinned under the CORRECTED Leung bracket (§11 #12): the pre-fix formula gave
    # G = 362.6 / area = 30.978 in² — a ~21 % under-size on this branch.
    assert res["G"] == pytest.approx(288.25, abs=5e-2)
    assert res["area"] == pytest.approx(38.9718, abs=5e-3)


def test_twophase_si_omitted_pa_uses_atmospheric_in_kpa(psv_module):
    """The SI branch must default to 101.325 kPa, not 14.696 (unit mix-up guard).
    Po = 130 kPa (above atmospheric, so flow is possible) gives Pc = eta_c * 130
    ~ 91 kPa, below the 101.325 kPa default back-pressure -> subcritical."""
    res = psv_module.size_twophase({"W": 10000, "vo": 0.019, "v9": 0.023,
                                    "Po": 130, "Pa": 0, "Kd": 0.85}, "SI")
    assert res["error"] is False
    assert res["flow_regime"] == "Two-Phase Subcritical (Omega)"
    assert res["Pc"] < 101.325 < 130
    # Corrected Leung bracket (§11 #12); the pre-fix formula selected orifice L here.
    assert res["area"] == pytest.approx(2589.0238, abs=5e-2)
    assert res["orifice"] == "N"


def test_twophase_explicit_pa_is_still_honored(psv_module):
    """An explicit positive Pa must be used as given — the atmospheric default only
    replaces omitted/zero values. Pa = 60 psia > Pc = 52.97 forces subcritical."""
    res = psv_module.size_twophase(dict(TWOPHASE_CASE, Pa=60), "USC")
    assert res["error"] is False
    assert res["flow_regime"] == "Two-Phase Subcritical (Omega)"


def test_subcritical_flux_is_continuous_with_the_critical_branch(psv_module):
    """FIXED (closes §11 #12): the subcritical mass-flux bracket was coded as
    -2·ω·ln(η) + (ω-1)(1-η) instead of Leung's -2·[ω·ln(η) + (ω-1)(1-η)] — the -2
    multiplied only the log term. That form produced subcritical flux ABOVE choked
    flux (impossible — choked flow is maximal) and was discontinuous at η_c.

    η_c is DEFINED as the point where the flux expression peaks, so the subcritical
    G evaluated just below η_c must reproduce the critical-branch G. The residual
    tolerance reflects omega_eta_c's quadratic approximation of the transcendental
    η_c equation, not the flux formula itself. Before the §11 #5 atmospheric default
    this branch was unreachable at the UI's Pa default of 0; the two ship together."""
    import math as _math
    for vo, v9 in ((0.3116, 0.3629), (0.019, 0.023), (0.05, 0.10)):
        omega = 9.0 * (v9 / vo - 1.0)
        eta_c = psv_module.omega_eta_c(omega)
        Po = 100.0
        G_crit = eta_c * _math.sqrt(Po / (vo * omega))
        eta = eta_c * 0.999999
        inner = -2.0 * (omega * _math.log(eta) + (omega - 1.0) * (1.0 - eta))
        denom = omega * (1.0 / eta - 1.0) + 1.0
        G_sub = _math.sqrt(inner) * _math.sqrt(Po / vo) / denom
        assert G_sub == pytest.approx(G_crit, rel=2e-3), f"discontinuous at omega={omega}"
        # And further below eta_c the flux must FALL — never exceed choked flow.
        eta_low = eta_c * 0.7
        inner_l = -2.0 * (omega * _math.log(eta_low) + (omega - 1.0) * (1.0 - eta_low))
        denom_l = omega * (1.0 / eta_low - 1.0) + 1.0
        G_low = _math.sqrt(inner_l) * _math.sqrt(Po / vo) / denom_l
        assert G_low < G_crit, f"subcritical flux exceeds choked flux at omega={omega}"


def test_twophase_po_at_or_below_default_backpressure_is_a_specific_error(psv_module):
    """With the atmospheric Pa default, Po ≤ 14.696 psia and an omitted Pa cannot
    relieve — the error must say exactly that (and name the vacuum-discharge escape
    hatch), not fall through to the generic subcritical-flux message."""
    res = psv_module.size_twophase(dict(TWOPHASE_CASE, Po=10), "USC")
    assert res["error"] is True
    assert "must exceed the back-pressure" in res["message"]
    assert "vacuum" in res["message"]


def test_gas_nan_mass_flow_is_rejected(psv_module):
    """NaN fails every ordered comparison, so the old `W <= 0` guard admitted it and
    returned error:false with area NaN — a body a browser cannot even parse. The
    guards now use not-(x > 0) polarity."""
    res = psv_module.size_gas({"W": float("nan"), "M": 51, "k": 1.3, "T": 627,
                               "P1": 97.2}, "USC")
    assert res["error"] is True


def test_psv_non_object_json_body_is_a_structured_400(psv_module, post_to_handler):
    """A valid-JSON body that is not an object ([1,2,3]) used to crash at data.get()
    -> bare 500. Now the 400 branch with the full superset."""
    status, data = post_to_handler(psv_module, [1, 2, 3])
    assert status == 400
    assert data["error"] is True
    for field in ("message", "badge", "badgeClass"):
        assert field in data
