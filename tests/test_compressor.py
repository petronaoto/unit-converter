"""Compressor head/power card (v3.0) — Vector 10 pins and source-level guards.

Same doctrine as test_npsh.py: the card is client-side JavaScript, so the
constants it computes with are EXTRACTED from index.html (not re-typed here),
the algorithm is re-run in Python through the exact path calcCompressor() takes
(toPsia -> papayZ at suction -> one-pass perfect-gas T2 -> papayZ at discharge
-> Z_avg heads), and the display strings are pinned against both the page's
documentation tabs and docs/SPECIFICATION.md §9 Vector 10. The browser side is
verified by hand, same as Vectors 1, 8 and 9.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Vector 10 duty: SG 0.65, 40 -> 80 bar a, 30 degC, k = 1.3, eta_p = 75 %, 100 t/h
SG, K_CPCV, ETA_P = 0.65, 1.3, 0.75


@pytest.fixture(scope="module")
def html():
    return (REPO_ROOT / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def spec():
    return (REPO_ROOT / "docs" / "SPECIFICATION.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def consts(html):
    """Pull the exact literals calcCompressor() runs on out of the page source."""
    def grab(pattern):
        m = re.search(pattern, html)
        assert m, pattern
        return float(m.group(1))
    return {
        "bar_to_psia": grab(r"PRESS_TO_PSIA = \{[^}]*bar: ([0-9.]+),"),
        "mw_air": grab(r"const MW_AIR_GP\s*=\s*([0-9.]+);"),
        "r_kmol": grab(r"const R_KMOL_GP\s*=\s*([0-9.]+);"),
    }


def papay(sg, p_psia, t_rankine):
    """Papay (1968) exactly as papayZ() writes it; the literals themselves are
    pinned source-side by tests/test_js_constants.py."""
    ppc = 756.8 - 131 * sg - 3.6 * sg * sg
    tpc = 169.2 + 349.5 * sg - 74 * sg * sg
    pr, trr = p_psia / ppc, t_rankine / tpc
    z = 1 - 3.52 * pr / 10 ** (0.9813 * trr) + 0.274 * pr * pr / 10 ** (0.8157 * trr)
    return pr, trr, z


def vector10(consts):
    p1 = 40 * consts["bar_to_psia"]
    p2 = 80 * consts["bar_to_psia"]
    t1R = 30 * 1.8 + 491.67
    r = p2 / p1
    pr1, tr1, z1 = papay(SG, p1, t1R)
    mP = (K_CPCV - 1) / (K_CPCV * ETA_P)
    t2R = t1R * r ** mP
    pr2, tr2, z2 = papay(SG, p2, t2R)
    z_avg = (z1 + z2) / 2
    rtm = consts["r_kmol"] * (t1R / 1.8) / (SG * consts["mw_air"])
    mS = (K_CPCV - 1) / K_CPCV
    h_poly = z_avg * rtm * (r ** mP - 1) / mP
    h_isen = z_avg * rtm * (r ** mS - 1) / mS
    return dict(r=r, z1=z1, z2=z2, z_avg=z_avg, mP=mP, t2R=t2R,
                pr1=pr1, tr1=tr1, pr2=pr2, tr2=tr2,
                h_poly=h_poly, h_isen=h_isen,
                eta_is=ETA_P * h_isen / h_poly,
                w_kw=(100 * 1000 / 3600.0) * h_poly / ETA_P / 1000.0)


# ── Vector 10 — docs/SPECIFICATION.md §9 ─────────────────────────────────────────

def test_vector10_z_line(consts):
    v = vector10(consts)
    assert round(v["r"], 10) == 2.0
    assert round(v["z1"], 4) == 0.9083 and round(v["z1"], 8) == 0.9083271
    assert round(v["z2"], 4) == 0.9322 and round(v["z2"], 8) == 0.9321836
    assert round(v["z_avg"], 4) == 0.9203 and round(v["z_avg"], 8) == 0.92025535
    # both states must sit INSIDE Papay validity — Vector 10 exercises no warning
    for pr, tr in ((v["pr1"], v["tr1"]), (v["pr2"], v["tr2"])):
        assert 0 < pr <= 15 and 1.05 <= tr <= 3.0


def test_vector10_heads_and_temperature(consts):
    v = vector10(consts)
    assert round(v["h_poly"] / 1000.0, 5) == 95.18714
    assert round(v["h_isen"] / 1000.0, 5) == 92.60625
    assert round(v["t2R"] / 1.8 - 273.15, 5) == 102.06672
    assert round(1 / (1 - v["mP"]), 4) == 1.4444          # polytropic exponent n
    assert round(v["eta_is"] * 100, 2) == 72.97
    assert v["eta_is"] < ETA_P                             # always true in compression


def test_vector10_power_and_display_units(consts):
    v = vector10(consts)
    assert round(v["w_kw"], 5) == 3525.44967
    assert round(v["w_kw"] * 1.3410221, 5) == 4727.70592           # hp display
    assert round(v["h_poly"] / 1000.0 * 334.55256, 5) == 31845.10172  # ft·lbf/lbm


def test_display_unit_factors_derive_from_exact_definitions():
    """The two new output factors are 8-s.f. roundings of exact products:
    ft·lbf/lbm = 9.80665 × 0.3048 J/kg and hp = 550 ft·lbf/s."""
    assert abs(1000.0 / (9.80665 * 0.3048) - 334.55256) < 5e-6
    hp_w = 550 * 0.3048 * 0.45359237 * 9.80665
    assert abs(1000.0 / hp_w - 1.3410221) < 5e-8


def test_vector10_numbers_agree_between_page_and_spec(html, spec):
    """Worked example digits must be identical in the How To Use tab, the Theory
    tab and SPECIFICATION §9 — same doctrine as Vectors 5–9."""
    for token in ("95.18714", "92.60625", "102.06672", "3,525.44967",
                  "0.9083", "0.9322", "0.9203", "1.4444", "72.97"):
        assert html.count(token) >= 2, f"{token} missing from a documentation tab"
        assert token in spec, f"{token} missing from SPECIFICATION.md"
    # the Z line renders as one string in the card; How To Use and the spec quote it verbatim
    assert "0.9083 / 0.9322 / 0.9203" in html and "0.9083 / 0.9322 / 0.9203" in spec


# ── Source-level guards ──────────────────────────────────────────────────────────

def test_compressor_function_exists_and_is_wired(html):
    assert "function calcCompressor(" in html
    m = re.search(r"\[calcGHV,.*?\]\.forEach", html)
    assert m and "calcCompressor" in m.group(0), "calcCompressor missing from recomputeAll()"
    body = html[html.index("function calcCompressor"):]
    body = body[:body.index("\n    }")]
    # must route through the SHARED real-gas helpers, never a private copy —
    # exactly the duplication v2.8 removed from the Z-Factor/Gas Property pair
    assert body.count("papayZ(") == 2, "Z1 and Z2 must both come from papayZ()"
    for shared in ("toPsia(", "toRankine(", "steamKtoUnit(", "MW_AIR_GP", "R_KMOL_GP"):
        assert shared in body, f"{shared} missing from calcCompressor()"
    # NaN-safe positive-assertion polarity (PR-1 heritage), incl. the eta<=1 rejection
    assert "!(etaP > 0) || !(etaP <= 1)" in body
    assert "!(p2 > p1)" in body


def test_compressor_exact_unit_factors_survive(html):
    for factor in ('value="334.55256"',    # kJ/kg -> ft·lbf/lbm (from exact 2.98906692)
                   'value="1.3410221"',    # kW -> hp (from exact 745.69987... W)
                   'value="0.45359237"',   # lb -> kg, exact by definition
                   'value="3600"'):        # kg/s -> kg/h, exact
        assert factor in html, f"{factor} missing from compressor unit selects"
