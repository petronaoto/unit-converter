"""v3.8 — Safety tab pressure inputs: per-field unit selects, Abs/Gauge basis, the ⇩ import
button, and the one-click defaults.

The conversion itself lives in JavaScript (`psvPressForApi()`), which pytest cannot execute; what
CAN be pinned from here is (a) the HTML contract the JS relies on, (b) that the on-screen defaults
really are the numbers the documentation quotes, and (c) that those numbers reproduce the
documented result through the real sizing module — i.e. that the "one click → orifice H" promise
in How To Use §21 is true of the API the card calls.

Reference: docs/SPECIFICATION.md §4.4 (defaults table) and §9 Vector 15.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX = REPO_ROOT / "index.html"

# The eight pressure fields, in DOM order, with the basis each one defaults to. Liquid (§5.8/§5.9)
# is gauge because API 520 writes those equations in gauge terms; everything else is absolute.
PRESSURE_FIELDS = {
    "psv-P1": "abs", "psv-P2": "abs",            # §5.6 gas / vapour
    "psv-P1-steam": "abs",                       # §5.7 steam
    "psv-P1-liq": "gau", "psv-Ps": "gau", "psv-P2-liq": "gau",   # §5.8 / §5.9 liquid
    "psv-Po": "abs", "psv-Pa": "abs",            # §5.10 two-phase
}

# Multiply-to-Pa factors, in the order the <select> lists them. psi first (USC is the card's
# default system); kPa second. psvSyncPressUnits() flips between exactly these two values.
UNIT_OPTIONS = [("6894.75729", "psi"), ("1000", "kPa"), ("100000", "bar"), ("1000000", "MPa"),
                ("1", "Pa"), ("101325", "atm"), ("98066.5", "kg/cm²")]

# Gas-mode one-click default (v3.8). Documented in How To Use §21 and SPECIFICATION §9 Vector 15.
GAS_DEFAULT = {"W": 8000, "M": 19, "k": 1.3, "T": 560, "Z": 1.0, "P1": 179.7, "P2": 0,
               "Kd": 0.975, "Kb": 1.0, "Kc": 1.0}


@pytest.fixture(scope="module")
def html():
    return INDEX.read_text(encoding="utf-8")


def _value_of(html, element_id):
    m = re.search(r'<input[^>]*\bid="%s"[^>]*>' % re.escape(element_id), html)
    assert m, f"no <input id={element_id!r}>"
    v = re.search(r'\bvalue="([^"]*)"', m.group(0))
    assert v, f"{element_id} has no value= attribute (placeholder-only fields are not one-click)"
    return v.group(1)


# ── HTML contract the JS relies on ───────────────────────────────────────────────

def test_every_pressure_field_has_a_unit_select_and_basis_toggle(html):
    for fid, basis in PRESSURE_FIELDS.items():
        assert html.count(f'id="{fid}-u"') == 1, f"{fid}: missing unit <select>"
        assert html.count(f'id="{fid}-abs"') == 1 and html.count(f'id="{fid}-gau"') == 1, f"{fid}: Abs/Gauge buttons"
        assert f'onclick="importPsvPressure(\'{fid}\')"' in html, f"{fid}: ⇩ import button"
        # the old fixed-unit chip is gone — _psvUnitLabels() must not try to relabel it
        assert f'id="{fid}-unit"' not in html, f"{fid}: stale fixed-unit <span> still present"


def test_default_basis_is_painted_in_the_markup(html):
    """The initial button classes must agree with PSV_PRESS_GAUGE_DEFAULT in the JS — a share
    link restore repaints, but a fresh load shows whatever the HTML says."""
    on = "bg-red-700 text-white"
    for fid, basis in PRESSURE_FIELDS.items():
        abs_btn = re.search(r'<button[^>]*id="%s-abs"[^>]*>' % fid, html).group(0)
        gau_btn = re.search(r'<button[^>]*id="%s-gau"[^>]*>' % fid, html).group(0)
        assert (on in abs_btn) == (basis == "abs"), f"{fid}: Abs button state"
        assert (on in gau_btn) == (basis == "gau"), f"{fid}: Gauge button state"
    js = re.search(r"const PSV_PRESS_GAUGE_DEFAULT = \[([^\]]*)\]", html).group(1)
    assert set(re.findall(r"'([^']+)'", js)) == {f for f, b in PRESSURE_FIELDS.items() if b == "gau"}


def test_unit_select_option_lists_are_static_and_identical(html):
    """Option values are multiply-to-Pa factors shared with the General tab Pressure card (the
    import button converts between the two). The list is STATIC — share-link restore sets the
    value before any event fires, the same rule as every other select in the app."""
    for fid in PRESSURE_FIELDS:
        sel = re.search(r'<select id="%s-u"[^>]*>(.*?)</select>' % fid, html, re.S).group(1)
        opts = re.findall(r'<option value="([^"]+)">([^<]+)</option>', sel)
        assert opts == UNIT_OPTIONS, f"{fid}: option list drifted: {opts}"
    general = re.search(r'<select id="press-select1"[^>]*>(.*?)</select>', html, re.S).group(1)
    general_factors = dict(re.findall(r'<option value="([^"]+)"[^>]*>([^<]+)</option>', general))
    for value, label in UNIT_OPTIONS[:6]:
        assert general_factors.get(value) == label, f"{label}: PSV factor {value} not shared with the General card"
    # the JS canonical factors must be the psi / kPa option values verbatim (string compare in psvSyncPressUnits)
    assert "const PSV_PSI_PA = 6894.75729, PSV_KPA_PA = 1000;" in html


def test_pressure_fields_route_through_the_basis_converter(html):
    """calcPSV() must never read a pressure field raw again; every pressure goes through
    psvPressForApi() with the right output basis (absolute, or gauge for liquid)."""
    body = html[html.index("async function calcPSV()"):]
    body = body[:body.index("// ════")]
    raw_read = lambda fid: re.search(r"(?<![A-Za-z])g\('%s'\)" % re.escape(fid), body)
    for fid in ("psv-P1", "psv-P2", "psv-P1-steam", "psv-Po", "psv-Pa"):
        assert f"gp('{fid}')" in body, f"{fid}: not converted to absolute"
        assert not raw_read(fid), f"{fid}: still read raw"
    for fid in ("psv-P1-liq", "psv-Ps", "psv-P2-liq"):
        assert f"gg('{fid}')" in body, f"{fid}: not converted to gauge"
        assert not raw_read(fid), f"{fid}: still read raw"
    # the steam saturation advisory reads the same converted figure
    assert "psvPressForApi('psv-P1-steam', usc ? 'USC' : 'SI', false)" in html
    # the psv-T-steam advisory-only pin from v3.0 still holds (5 references)
    assert html.count("psv-T-steam") == 5


def test_basis_map_travels_in_state_and_legacy_si_links_are_migrated(html):
    assert "psvPm: Object.assign({}, psvPressMode)" in html
    assert "if (s.psvPm) applyPsvPressModes(s.psvPm);" in html
    # a pre-v3.8 payload has no psv-*-u keys and its SI pressures were kPa
    assert "!('psv-P1-u' in s.inputs) && s.inputs['psv-units'] === 'SI') psvSyncPressUnits('SI')" in html
    assert '<select id="psv-units" onchange="onPsvUnitsChange()"' in html


def test_old_fixed_basis_hints_are_gone(html):
    """[gauge] / [absolute] label hints would contradict the per-field toggle."""
    assert "safety.psv.hintGauge" not in html and "safety.psv.hintAbsolute" not in html


# ── One-click defaults ───────────────────────────────────────────────────────────

def test_gas_default_values_are_the_documented_ones(html):
    got = {k: float(_value_of(html, f"psv-{k}")) for k in ("W", "M", "k", "T", "Z", "P1", "P2", "Kd", "Kb", "Kc")}
    assert got == GAS_DEFAULT
    # … and sit on psi / absolute, so the payload equals the raw numbers (no conversion on a stock case)
    sel = re.search(r'<select id="psv-P1-u"[^>]*>(.*?)</select>', html, re.S).group(1)
    assert sel.startswith('<option value="6894.75729">psi</option>')
    assert 'selected' not in sel


def test_gas_default_sizes_to_orifice_H_through_the_real_api(psv_module):
    """The whole point of the defaults: CALCULATE with nothing typed returns orifice H."""
    res = psv_module.size_gas(dict(GAS_DEFAULT), "USC")
    assert res["error"] is False
    assert res["flow_regime"] == "Critical Flow"
    assert res["C"] == pytest.approx(346.9764, abs=5e-5)
    assert res["Pcf"] == pytest.approx(98.067, abs=5e-4)
    assert res["area"] == pytest.approx(0.7144, abs=5e-5)
    assert res["orifice"] == "H"
    assert res["orifice_area"] == pytest.approx(0.785, abs=5e-4)


def test_gas_default_is_robustly_inside_orifice_H(psv_module):
    """H spans 0.503 < A ≤ 0.785 in². The default must not sit on an edge where a rounding
    difference in the browser could tip it to G or J."""
    res = psv_module.size_gas(dict(GAS_DEFAULT), "USC")
    assert 0.55 < res["area"] < 0.76


def test_gas_default_entered_as_gauge_gives_the_same_orifice(psv_module):
    """How To Use §21 says: switch P1 to Gauge and enter 165 → still H. 165 psig + 101,325 Pa."""
    p1_psia = 165 + 101325 / 6894.75729
    res = psv_module.size_gas(dict(GAS_DEFAULT, P1=p1_psia), "USC")
    assert res["orifice"] == "H"


def test_other_modes_default_to_their_reference_cases(html, psv_module):
    """Steam / liquid / two-phase open on the Vector 4 cases (SPECIFICATION §9), so one click in
    any mode returns the documented letter."""
    steam = {"W": float(_value_of(html, "psv-W-steam")), "P1": float(_value_of(html, "psv-P1-steam")),
             "Kd": 0.975, "Kb": 1.0, "Kc": 1.0, "KSH": 1.0}
    assert psv_module.size_steam(steam, "USC")["orifice"] == "K"
    liq = {"Q": float(_value_of(html, "psv-Q")), "Gl": float(_value_of(html, "psv-Gl")), "mu": 0,
           "P1": float(_value_of(html, "psv-P1-liq")), "P2": float(_value_of(html, "psv-P2-liq")),
           "Kd": 0.65, "Kw": 1.0, "Kc": 1.0}
    assert psv_module.size_liquid_cert(liq, "USC")["orifice"] == "N"
    nc = dict(liq, Ps=float(_value_of(html, "psv-Ps")), Kd=0.62, Kp=1.0); nc.pop("P1")
    assert psv_module.size_liquid_noncert(nc, "USC")["orifice"] == "N"
    tp = {"W": float(_value_of(html, "psv-W-tp")), "vo": float(_value_of(html, "psv-vo")),
          "v9": float(_value_of(html, "psv-v9")), "Po": float(_value_of(html, "psv-Po")),
          "Pa": float(_value_of(html, "psv-Pa")), "Kd": 0.85, "Kb": 1.0, "Kc": 1.0, "Kv": 1.0}
    assert psv_module.size_twophase(tp, "USC")["orifice"] == "T"


def test_docs_quote_the_default_case_numbers(html):
    """How To Use §21 worked example must match the calculator (Documentation Sync Rule)."""
    blk = re.search(r'data-i18n-html="docs\.howto\.b114">(.*?)data-i18n-html="docs\.howto\.b066"', html, re.S).group(1)
    for needle in ("8,000 lb/h", "19 g/mol", "560 °R", "179.7 psi", "346.98", "98.07 psia",
                   "0.7144 in²", "orifice H", "0.785 in²"):
        assert needle in blk, f"§21 worked example missing {needle!r}"
