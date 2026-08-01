"""Reference-value regression for api/psv_calculator.py (API 520 Part I, 9th Ed.).

NOTE ON PROVENANCE — read before trusting these numbers.

Unlike the ΔP and Flow Regime cases, no PSV reference vector has ever been documented in
CLAUDE.md, api/CLAUDE.md or docs/SPECIFICATION.md §9. The five cases below were generated
by running the CURRENT implementation against the placeholder values already shown in the
Safety card's own input fields (index.html `psv-*` placeholders), then hand-checked where
the arithmetic is short enough to check.

They are therefore *behavior locks*, not independently blessed engineering references:
they prove the endpoint has not changed, not that it was right to begin with. They are
proposed for the maintainer's review and, once blessed, for promotion into
docs/SPECIFICATION.md §9 as Vector 4.

Hand-check performed on the gas case (§5.6, USC, k = 1.3):
    C   = 520 * sqrt(1.3 * (2/2.3)^(2.3/0.3)) = 346.98
    pcr = (2/2.3)^(1.3/0.3)                   = 0.5457
    Pcf = 0.5457 * 97.2                       = 53.04 psia
    A   = 53500 / (346.98*0.975*97.2) * sqrt(627/51) = 5.704 in²  -> orifice P (6.38 in²)
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

def test_twophase_critical_omega(psv_module):
    data = {"W": 477430, "vo": 0.3116, "v9": 0.3629, "Po": 80.7, "Pa": 0,
            "Kd": 0.85, "Kb": 1.0, "Kc": 1.0, "Kv": 1.0}
    res = psv_module.size_twophase(data, "USC")

    assert res["error"] is False
    assert res["area"] == pytest.approx(38.0227, abs=5e-4)
    assert res["flow_regime"] == "Two-Phase Critical (Omega)"
    assert res["badge"] == "Two-Phase (Omega Method)"
    assert res["omega"] == pytest.approx(1.4817, abs=5e-5)
    assert res["eta_c"] == pytest.approx(0.6564, abs=5e-5)
    assert res["G"] == pytest.approx(590.891, abs=5e-4)


def test_twophase_reported_pc_encodes_known_issue_1(psv_module):
    """KNOWN ISSUE (docs/SPECIFICATION.md §11 #1): the reported Pc is computed from the
    back-pressure Pa instead of the relieving pressure Po. The sizing itself is correct —
    the internal critical/subcritical decision uses eta_c * Po — but the DISPLAYED Pc is
    wrong. With the default Pa = 0 it degrades to exactly 0.0.

    Locked here so that fixing the issue is a deliberate act that updates this test and
    the register entry together, rather than a silent change to a displayed value.
    """
    data = {"W": 477430, "vo": 0.3116, "v9": 0.3629, "Po": 80.7, "Pa": 0,
            "Kd": 0.85, "Kb": 1.0, "Kc": 1.0, "Kv": 1.0}
    res = psv_module.size_twophase(data, "USC")
    assert res["Pc"] == pytest.approx(0.0)
    # What it SHOULD be, once #1 is fixed:
    assert res["eta_c"] * data["Po"] == pytest.approx(52.97, abs=0.05)


def test_twophase_rejects_v9_below_vo(psv_module):
    """omega < 0 is physically impossible — the two-phase specific volume must expand."""
    data = {"W": 477430, "vo": 0.3629, "v9": 0.3116, "Po": 80.7, "Pa": 0,
            "Kd": 0.85, "Kb": 1.0, "Kc": 1.0, "Kv": 1.0}
    res = psv_module.size_twophase(data, "USC")
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
