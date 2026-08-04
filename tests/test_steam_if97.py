"""IAPWS-IF97 client-side engine — coefficient extraction and re-verification.

The steam card (v3.0) evaluates IF97 Regions 1, 2 and 4 in the browser. pytest cannot
execute that JavaScript, but the coefficients live in index.html as a single JSON
literal inside `const IF97 = JSON.parse(...)` precisely so this file can extract THE
EXACT LITERAL the browser parses, re-implement the equations independently in Python,
and reproduce the Release's own computer-program verification tables:

    Table 5   — Region 1 (v, h, u, s, cp, w at three T/p points)
    Table 15  — Region 2 (same six properties at three T/p points)
    Tables 35/36 — Region 4 saturation, both directions
    B23 check point — T = 623.15 K <-> p = 16.5291643 MPa

Source: Revised Release on IAPWS-IF97 (August 2007), iapws.org. Every expected value
below is transcribed from those tables; tolerance 5e-9 relative, the rounding
granularity of the tables' 9 significant figures. A single mistyped digit in any of
the 259 coefficients fails these tests.

The browser-side arithmetic itself is verified by hand in a real browser engine
against the same tables and Vector 8 (docs/SPECIFICATION.md §9), same as Vector 1.
"""

import json
import math
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

REL_TOL = 5e-9  # tables print 9 significant figures


@pytest.fixture(scope="module")
def html():
    return (REPO_ROOT / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def if97(html):
    """The exact JSON literal the browser executes — not a copy."""
    matches = re.findall(r"const IF97 = JSON\.parse\(`(.*?)`\);", html, re.DOTALL)
    assert len(matches) == 1, "IF97 coefficient literal must appear exactly once"
    return json.loads(matches[0])  # strict JSON — a JS-only construct would raise


# ── Structure: the constant set is complete and the documented count is honest ────

def test_gas_constant_and_array_shapes(if97):
    assert if97["R"] == 0.461526                       # Eq. (1), kJ/(kg K)
    assert len(if97["B23"]["n"]) == 5                  # Table 1
    assert len(if97["R4"]["n"]) == 10                  # Table 34
    assert len(if97["R1"]["I"]) == len(if97["R1"]["J"]) == len(if97["R1"]["n"]) == 34
    assert len(if97["R2"]["J0"]) == len(if97["R2"]["n0"]) == 9
    assert len(if97["R2"]["I"]) == len(if97["R2"]["J"]) == len(if97["R2"]["n"]) == 43


def test_the_259_coefficient_claim_is_arithmetically_true(if97):
    """The card footnote and Theory §8.4 both say '259 coefficients'. Keep the claim
    honest: 34x3 (R1) + 9x2 (R2 ideal) + 43x3 (R2 residual) + 10 (R4) = 259."""
    n = (3 * len(if97["R1"]["n"]) + 2 * len(if97["R2"]["n0"])
         + 3 * len(if97["R2"]["n"]) + len(if97["R4"]["n"]))
    assert n == 259


# ── Independent Python implementation, driven by the EXTRACTED coefficients ───────

def region1(c, p, T):
    R = c["R"]
    pi, tau = p / 16.53, 1386.0 / T
    A, B = 7.1 - pi, tau - 1.222
    g = gp = gpp = gt = gtt = gpt = 0.0
    for I, J, n in zip(c["R1"]["I"], c["R1"]["J"], c["R1"]["n"]):
        g += n * A**I * B**J
        gp -= n * I * A**(I - 1) * B**J
        gpp += n * I * (I - 1) * A**(I - 2) * B**J
        gt += n * A**I * J * B**(J - 1)
        gtt += n * A**I * J * (J - 1) * B**(J - 2)
        gpt -= n * I * A**(I - 1) * J * B**(J - 1)
    RT = R * T
    return {
        "v": pi * gp * RT / (p * 1000.0),
        "h": RT * tau * gt,
        "u": RT * (tau * gt - pi * gp),
        "s": R * (tau * gt - g),
        "cp": -R * tau * tau * gtt,
        "w": math.sqrt(RT * 1000.0 * gp * gp
                       / ((gp - tau * gpt) ** 2 / (tau * tau * gtt) - gpp)),
    }


def region2(c, p, T):
    R = c["R"]
    pi, tau = p, 540.0 / T
    g0, g0t, g0tt = math.log(pi), 0.0, 0.0
    for J, n in zip(c["R2"]["J0"], c["R2"]["n0"]):
        g0 += n * tau**J
        g0t += n * J * tau**(J - 1)
        g0tt += n * J * (J - 1) * tau**(J - 2)
    B0 = tau - 0.5
    gr = grp = grpp = grt = grtt = grpt = 0.0
    for I, J, n in zip(c["R2"]["I"], c["R2"]["J"], c["R2"]["n"]):
        gr += n * pi**I * B0**J
        grp += n * I * pi**(I - 1) * B0**J
        grpp += n * I * (I - 1) * pi**(I - 2) * B0**J
        grt += n * pi**I * J * B0**(J - 1)
        grtt += n * pi**I * J * (J - 1) * B0**(J - 2)
        grpt += n * I * pi**(I - 1) * J * B0**(J - 1)
    RT = R * T
    num = 1.0 + 2.0 * pi * grp + pi * pi * grp * grp
    den = ((1.0 - pi * pi * grpp)
           + (1.0 + pi * grp - tau * pi * grpt) ** 2 / (tau * tau * (g0tt + grtt)))
    return {
        "v": pi * (1.0 / pi + grp) * RT / (p * 1000.0),
        "h": RT * tau * (g0t + grt),
        "u": RT * (tau * (g0t + grt) - pi * (1.0 / pi + grp)),
        "s": R * (tau * (g0t + grt) - (g0 + gr)),
        "cp": -R * tau * tau * (g0tt + grtt),
        "w": math.sqrt(RT * 1000.0 * num / den),
    }


def psat(c, T):
    n = c["R4"]["n"]
    th = T + n[8] / (T - n[9])
    A = th * th + n[0] * th + n[1]
    B = n[2] * th * th + n[3] * th + n[4]
    C = n[5] * th * th + n[6] * th + n[7]
    return (2.0 * C / (-B + math.sqrt(B * B - 4.0 * A * C))) ** 4


def tsat(c, p):
    n = c["R4"]["n"]
    beta = p ** 0.25
    E = beta * beta + n[2] * beta + n[5]
    F = n[0] * beta * beta + n[3] * beta + n[6]
    G = n[1] * beta * beta + n[4] * beta + n[7]
    D = 2.0 * G / (-F - math.sqrt(F * F - 4.0 * E * G))
    return (n[9] + D - math.sqrt((n[9] + D) ** 2 - 4.0 * (n[8] + n[9] * D))) / 2.0


# ── Table 5 — Region 1 verification (18 values) ──────────────────────────────────

TABLE5 = {
    (300, 3):  {"v": 0.100215168e-2, "h": 0.115331273e3, "u": 0.112324818e3,
                "s": 0.392294792,    "cp": 0.417301218e1, "w": 0.150773921e4},
    (300, 80): {"v": 0.971180894e-3, "h": 0.184142828e3, "u": 0.106448356e3,
                "s": 0.368563852,    "cp": 0.401008987e1, "w": 0.163469054e4},
    (500, 3):  {"v": 0.120241800e-2, "h": 0.975542239e3, "u": 0.971934985e3,
                "s": 0.258041912e1,  "cp": 0.465580682e1, "w": 0.124071337e4},
}


@pytest.mark.parametrize("point", sorted(TABLE5))
def test_region1_reproduces_release_table_5(if97, point):
    T, p = point
    got = region1(if97, p, T)
    for q, expected in TABLE5[point].items():
        assert got[q] == pytest.approx(expected, rel=REL_TOL), f"{q} at T={T} p={p}"


# ── Table 15 — Region 2 verification (18 values) ─────────────────────────────────

TABLE15 = {
    (300, 0.0035): {"v": 0.394913866e2,  "h": 0.254991145e4, "u": 0.241169160e4,
                    "s": 0.852238967e1,  "cp": 0.191300162e1, "w": 0.427920172e3},
    (700, 0.0035): {"v": 0.923015898e2,  "h": 0.333568375e4, "u": 0.301262819e4,
                    "s": 0.101749996e2,  "cp": 0.208141274e1, "w": 0.644289068e3},
    (700, 30):     {"v": 0.542946619e-2, "h": 0.263149474e4, "u": 0.246861076e4,
                    "s": 0.517540298e1,  "cp": 0.103505092e2, "w": 0.480386523e3},
}


@pytest.mark.parametrize("point", sorted(TABLE15))
def test_region2_reproduces_release_table_15(if97, point):
    T, p = point
    got = region2(if97, p, T)
    for q, expected in TABLE15[point].items():
        assert got[q] == pytest.approx(expected, rel=REL_TOL), f"{q} at T={T} p={p}"


# ── Tables 35/36 — Region 4, both directions ─────────────────────────────────────

@pytest.mark.parametrize("T,expected", [
    (300, 0.353658941e-2), (500, 0.263889776e1), (600, 0.123443146e2)])
def test_region4_psat_reproduces_table_35(if97, T, expected):
    assert psat(if97, T) == pytest.approx(expected, rel=REL_TOL)


@pytest.mark.parametrize("p,expected", [
    (0.1, 0.372755919e3), (1.0, 0.453035632e3), (10.0, 0.584149488e3)])
def test_region4_tsat_reproduces_table_36(if97, p, expected):
    assert tsat(if97, p) == pytest.approx(expected, rel=REL_TOL)


def test_region4_is_self_inverse(if97):
    """Eq. 31 is Eq. 30 solved in closed form; a coefficient error that happened to
    cancel in one direction would still break the round trip."""
    for p in (0.001, 0.101325, 1.0, 4.0, 10.0, 16.529, 22.0):
        assert psat(if97, tsat(if97, p)) == pytest.approx(p, rel=1e-8)


# ── B23 boundary ─────────────────────────────────────────────────────────────────

def test_b23_verification_point(if97):
    n = if97["B23"]["n"]
    T, p = 623.15, 16.5291643
    assert n[0] + n[1] * T + n[2] * T * T == pytest.approx(p, rel=REL_TOL)
    assert n[3] + math.sqrt((p - n[4]) / n[2]) == pytest.approx(T, rel=REL_TOL)


# ── Vector 8 — the documented worked example (docs/SPECIFICATION.md §9) ──────────
#
# These pin the numbers printed in the How To Use / Theory tabs (formatValue shows
# 5 decimals). If an equation edit shifts any displayed digit, this fails before a
# stale worked example reaches production.

def test_vector8_superheated_point(if97):
    r = region2(if97, 4.0, 573.15)   # 4 MPa, 300 °C
    assert 1.0 / r["v"] == pytest.approx(16.98717, abs=5e-6)
    assert r["h"] == pytest.approx(2961.65148, abs=5e-6)
    assert r["s"] == pytest.approx(6.36383, abs=5e-6)
    assert r["cp"] == pytest.approx(2.81995, abs=5e-6)
    assert r["w"] == pytest.approx(550.23169, abs=5e-6)


def test_vector8_saturation_row(if97):
    Ts = tsat(if97, 4.0)
    assert Ts - 273.15 == pytest.approx(250.35752, abs=5e-6)
    hf = region1(if97, 4.0, Ts)["h"]
    hg = region2(if97, 4.0, Ts)["h"]
    assert hf == pytest.approx(1087.42602, abs=5e-6)
    assert hg == pytest.approx(2800.89732, abs=5e-6)
    assert hg - hf == pytest.approx(1713.4713, abs=5e-5)


def test_vector8_subcooled_point(if97):
    r = region1(if97, 4.0, 423.15)   # 4 MPa, 150 °C
    assert 1.0 / r["v"] == pytest.approx(918.99612, abs=5e-6)
    assert r["h"] == pytest.approx(634.43339, abs=5e-6)
    assert r["s"] == pytest.approx(1.83804, abs=5e-6)


def test_psv_advisory_example(if97):
    """SPECIFICATION §9 Vector 8: 1,774.7 psia -> Tsat displays 619.11105 °F.

    Uses the app's own psia->MPa factor (0.006894757, matching the 6894.757 Pa
    literal elsewhere in index.html) and pins the value at the 5-decimal display
    rounding — the browser shows exactly this string, verified by hand."""
    TsK = tsat(if97, 1774.7 * 0.006894757)
    assert round(TsK * 1.8 - 459.67, 5) == 619.11105


# ── Source-level guards (same doctrine as test_js_constants.py) ──────────────────

def test_steam_functions_exist_and_are_wired(html):
    for fn in ("function if97PsatMPa(", "function if97TsatK(", "function if97B23pMPa(",
               "function if97Region1(", "function if97Region2(", "function if97Classify(",
               "function calcSteamProps(", "function updateSteamAdvisory("):
        assert fn in html, f"{fn} missing"
    # restored state / share links must recompute the card
    m = re.search(r"\[calcGHV,.*?\]\.forEach", html)
    assert m and "calcSteamProps" in m.group(0), "calcSteamProps missing from recomputeAll()"


def test_exact_unit_factors_survive(html):
    """Conversion factors are exact by definition; 'tidying' any of them breaks
    reproducibility. psi->MPa matches the 6894.757 Pa literal used elsewhere in
    the app; Btu factors are the International Table definitions."""
    for factor in ('value="0.006894757"',   # psia -> MPa
                   'value="0.42992261"',    # kJ/kg -> Btu/lb  (1/2.326 exactly)
                   'value="0.23884590"',    # kJ/(kg·K) -> Btu/(lb·°R)  (1/4.1868)
                   'value="0.062427960"',   # kg/m³ -> lb/ft³  (1/16.0184634)
                   'value="3.280840"'):     # m/s -> ft/s
        assert factor in html, f"{factor} missing from steam card unit selects"


def test_advisory_temperature_never_enters_the_sizing_payload(html):
    """psv-T-steam is advisory-only. Exactly five references may exist: the input id,
    its unit-span id, the comment above updateSteamAdvisory(), the read inside it,
    and the unit relabel in _psvUnitLabels(). A sixth means someone wired it into
    calcPSV() — that is a payload change and must be a deliberate, reviewed
    decision, not a drive-by."""
    assert html.count("psv-T-steam") == 5
