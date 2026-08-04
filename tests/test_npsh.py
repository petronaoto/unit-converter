"""NPSHa card (v3.0) — Vector 9 pins and source-level guards.

The card is client-side JavaScript, so pytest verifies it the same way the other
JS surfaces are verified: the water-helper values come from the SAME extracted
IF97 literal test_steam_if97.py already validates against the Release's own
tables, the NPSHa arithmetic is re-run here in Python through the exact path the
UI takes (helper quantizes Pv and rho to 8 significant figures into the input
fields, then the calculation reads those), and the resulting display strings are
pinned against both the page and docs/SPECIFICATION.md §9 Vector 9. The browser
side is verified by hand, same as Vectors 1 and 8.
"""

import re
from pathlib import Path

import pytest

import test_steam_if97 as steam

REPO_ROOT = Path(__file__).resolve().parent.parent

G = 9.80665  # m/s², standard gravity — exact by definition


@pytest.fixture(scope="module")
def html():
    return (REPO_ROOT / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def spec():
    return (REPO_ROOT / "docs" / "SPECIFICATION.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def if97(html):
    matches = re.findall(r"const IF97 = JSON\.parse\(`(.*?)`\);", html, re.DOTALL)
    assert len(matches) == 1
    import json
    return json.loads(matches[0])


def prec8(x):
    """The helper writes toPrecision(8) into the input fields; mirror that."""
    return float(f"{x:.8g}")


def water_fill(if97, T_K):
    pv_kpa = prec8(steam.psat(if97, T_K) * 1000.0)
    rho = prec8(1.0 / steam.region1(if97, steam.psat(if97, T_K), T_K)["v"])
    return pv_kpa, rho


# ── Vector 9 — docs/SPECIFICATION.md §9 ──────────────────────────────────────────

def test_vector9_water_fill_values(if97):
    """80 °C: the two field values the helper writes, exactly as displayed."""
    pv, rho = water_fill(if97, 353.15)
    assert pv == 47.41472
    assert rho == 971.77879


def test_vector9_npsha(if97):
    """Open tank, z = +3 m, h_f = 1.2 m -> 7.45697 m = 24.46511 ft (5-dec display)."""
    pv, rho = water_fill(if97, 353.15)
    hp = (101.325 - pv) * 1000.0 / (rho * G)
    npsha = hp + 3.0 - 1.2
    assert round(hp, 5) == 5.65697
    assert round(npsha, 5) == 7.45697
    assert round(npsha * 3.280840, 5) == 24.46511


def test_vector9_flashing_case(if97):
    """95 °C on a 2 m suction lift with 0.8 m friction -> negative NPSHa."""
    pv, rho = water_fill(if97, 368.15)
    assert pv == 84.608938
    assert rho == 961.88733
    hp = (101.325 - pv) * 1000.0 / (rho * G)
    npsha = hp - 2.0 - 0.8
    assert round(hp, 4) == 1.7721
    assert round(npsha, 4) == -1.0279
    assert npsha <= 0  # the card must show the flashing warning here


def test_vector9_numbers_agree_between_page_and_spec(html, spec):
    """The same doctrine as test_js_constants.py: the worked example must print the
    same digits in the How To Use tab, the Theory tab and SPECIFICATION §9."""
    for token in ("7.45697", "24.46511", "47.41472", "971.77879", "5.65697"):
        assert html.count(token) >= 2, f"{token} missing from a documentation tab"
        assert token in spec, f"{token} missing from SPECIFICATION.md"


# ── Source-level guards ──────────────────────────────────────────────────────────

def test_npsh_functions_exist_and_are_wired(html):
    for fn in ("function calcNPSH(", "function fillNPSHWater("):
        assert fn in html, f"{fn} missing"
    m = re.search(r"\[calcGHV,.*?\]\.forEach", html)
    assert m and "calcNPSH" in m.group(0), "calcNPSH missing from recomputeAll()"
    # the helper must go through the shared IF97 surfaces, not a private copy
    body = html[html.index("function fillNPSHWater"):]
    body = body[:body.index("\n    }")]
    assert "if97PsatMPa(" in body and "if97Region1(" in body
    assert "toPrecision(8)" in body, "field quantization is part of Vector 9's definition"


def test_standard_gravity_is_exact(html):
    assert "const NPSH_G = 9.80665;" in html, (
        "g must be the exact standard-gravity literal, not a rounded 9.81")


def test_npsh_exact_unit_factors_survive(html):
    """kPa-family factors on the two pressure selects; exact length/density factors."""
    for factor in ('value="6.894757"',    # psia -> kPa (matches 6894.757 Pa elsewhere)
                   'value="98.0665"',     # kg/cm² -> kPa (exact)
                   'value="0.3048"',      # ft -> m (exact)
                   'value="16.0184634"'): # lb/ft³ -> kg/m³ (same as RP 14E constant)
        assert factor in html, f"{factor} missing from NPSHa unit selects"
