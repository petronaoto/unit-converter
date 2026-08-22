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


# ── v3.8.1 — every other physical input has a unit select too ────────────────────

QTY_FIELDS = {
    # id: (first option value = USC canonical, second option value = SI canonical)
    "psv-W": ("0.45359237", "1"), "psv-W-steam": ("0.45359237", "1"), "psv-W-tp": ("0.45359237", "1"),
    "psv-T": ("R", "K"), "psv-T-steam": ("F", "C"),
    "psv-Q": ("3.785411784", "1"), "psv-mu": ("1", "1"),      # cP in BOTH systems (API 520 SI form is mPa·s = cP)
    "psv-vo": ("0.062427961", "1"), "psv-v9": ("0.062427961", "1"),
}


def test_every_quantity_field_has_a_unit_select_with_canonical_units_first(html):
    """The USC canonical unit is the first option (the card's default system) and the SI
    canonical the second, so a fresh page and a pre-v3.8.1 restore both mean what they always
    meant; psvSyncQtyUnits() flips between exactly these two values."""
    for fid, (usc, si) in QTY_FIELDS.items():
        sel = re.search(r'<select id="%s-u"[^>]*>(.*?)</select>' % fid, html, re.S)
        assert sel, f"{fid}: missing unit <select>"
        opts = re.findall(r'<option value="([^"]+)">', sel.group(1))
        assert opts[0] == usc, f"{fid}: first option must be the USC canonical unit: {opts[:2]}"
        if usc != si:
            assert opts[1] == si, f"{fid}: second option must be the SI canonical unit: {opts[:2]}"
        assert f'id="{fid}-unit"' not in html, f"{fid}: stale fixed-unit <span> still present"
        # PSV_QTY must carry the same canonical pair
        entry = re.search(r"'%s':\s*\{\s*usc:\s*'([^']+)',\s*si:\s*'([^']+)'" % re.escape(fid), html)
        assert entry and entry.groups() == (usc, si), f"{fid}: PSV_QTY canonical pair differs from the <select>"


def test_viscosity_options_are_string_distinct(html):
    """cP and mPa·s are numerically identical; their option VALUES must differ as strings or a
    share-link restore could never tell them apart (same rule as the Basic Eng viscosity card)."""
    sel = re.search(r'<select id="psv-mu-u"[^>]*>(.*?)</select>', html, re.S).group(1)
    values = re.findall(r'<option value="([^"]+)">', sel)
    assert len(values) == len(set(values))
    assert "1" in values and "1.0" in values


def test_quantities_route_through_psvqty_in_calcpsv(html):
    body = html[html.index("async function calcPSV()"):]
    body = body[:body.index("// ════")]
    raw_read = lambda fid: re.search(r"(?<![A-Za-z])g\('%s'\)" % re.escape(fid), body)
    for fid in ("psv-W", "psv-T", "psv-W-steam", "psv-Q", "psv-mu", "psv-W-tp", "psv-vo", "psv-v9"):
        assert f"gq('{fid}')" in body, f"{fid}: not converted through psvQty()"
        assert not raw_read(fid), f"{fid}: still read raw"
    # dimensionless inputs stay raw
    for fid in ("psv-M", "psv-k", "psv-Z", "psv-Gl"):
        assert f"gq('{fid}')" not in body, f"{fid} is dimensionless and must not be unit-converted"
    # the advisory temperature goes through the same converter (and stays out of the payload)
    assert "psvQty('psv-T-steam', usc ? 'USC' : 'SI')" in html
    assert html.count("psv-T-steam") == 5


def test_units_toggle_follows_quantity_selects_too(html):
    fn = html[html.index("function onPsvUnitsChange()"):]
    fn = fn[:fn.index("}")]
    assert "psvSyncPressUnits(" in fn and "psvSyncQtyUnits(" in fn and "updatePSVMode()" in fn


# ── v3.8.2 — the toggle converts the figures it re-labels; ↺ Load example ────────

def test_units_toggle_converts_the_figures_it_relabels(html):
    """v3.8.1 re-labelled psi→kPa / lb/h→kg/h / °R→K but left the numbers, so selecting SI turned
    the default H case into an R case (maintainer screenshot 2026-08-22). Both sync functions must
    now rescale the value whenever they move a select; temperatures go through kelvin."""
    press = html[html.index("function psvSyncPressUnits("):html.index("function psvRescale(")]
    assert "psvRescale(id, parseFloat(from) / parseFloat(to))" in press
    qty = html[html.index("function psvSyncQtyUnits("):html.index("function psvLoadExample(")]
    assert "psvTempFromK(psvTempToK(v, from), to)" in qty
    assert "v * parseFloat(from) / parseFloat(to)" in qty
    assert "if (from === to || sel.value !== from) return;" in qty   # cP↔cP must not rewrite the field
    rescale = html[html.index("function psvRescale("):html.index("function psvSyncQtyUnits(")]
    assert "psvFmt(v * ratio)" in rescale and "ratio !== 1" in rescale
    # v3.8.3 — 9 significant digits (5 decimals truncated vo = 0.0194526 m³/kg to 0.01945), snapped to
    # the 6-digit value when they agree within 1e-7 so a USC→SI→USC round trip lands back on 179.7 / 0.3116
    fmt = html[html.index("function psvFmt(x) {"):]
    fmt = fmt[:fmt.index("\n    }")]
    assert "x.toPrecision(9)" in fmt and "x.toPrecision(6)" in fmt and "1e-7 * Math.abs(full)" in fmt


def test_load_example_button_resets_every_panel(html):
    assert html.count('id="psv-load-example"') == 1
    assert 'onclick="psvLoadExample()"' in html
    assert 'data-i18n="safety.psv.loadExample"' in html and 'data-i18n-title="safety.psv.loadExampleTitle"' in html
    fn = html[html.index("function psvLoadExample()"):]
    fn = fn[:fn.index("\n    }")]
    assert "['gas', 'steam', 'liquid', 'twophase'].forEach(p => { psvResetPanel(p); psvExpressPanelInSystem(p); })" in fn
    assert "updatePSVMode()" in fn and "scheduleSave()" in fn


def test_reset_panels_are_expressed_in_the_active_unit_system(html):
    """v3.8.3 — with SI selected, ↺ Load example (and the restore fallback) must present the shipped
    case in SI units (kg/h · K · kPa), not flip the card back to USC labels. Both reset paths go
    through psvExpressPanelInSystem(), which runs the two sync passes SCOPED to the reset panel so a
    user's other panels are never touched."""
    fn = html[html.index("function psvExpressPanelInSystem("):]
    fn = fn[:fn.index("\n    }")]
    assert "if (!box || units !== 'SI') return;" in fn
    assert "psvSyncPressUnits(units, box);" in fn and "psvSyncQtyUnits(units, box);" in fn
    # restore fallback uses it too
    ens = html[html.index("function psvEnsureDefaults()"):]
    ens = ens[:ens.index("\n    }")]
    assert "if (!complete) { psvResetPanel(panel); psvExpressPanelInSystem(panel); }" in ens
    # both sync functions honour the optional scope
    assert "function psvSyncPressUnits(units, scope)" in html and "if (!u || (scope && !scope.contains(u))) return;" in html
    assert "function psvSyncQtyUnits(units, scope)" in html and "if (!sel || (scope && !scope.contains(sel))) return;" in html


def test_si_expression_of_the_default_case_still_sizes_to_H(psv_module):
    """What the toggle now produces from the shipped case: 8,000 lb/h → kg/h, 560 °R → K,
    179.7 psi → kPa, run through the SI equations (API 520 Eq. 5 with C_SI = 0.03948)."""
    si = {"W": 8000 * 0.45359237, "M": 19, "k": 1.3, "T": 560 / 1.8, "Z": 1.0,
          "P1": 179.7 * 6894.75729 / 1000, "P2": 0, "Kd": 0.975, "Kb": 1.0, "Kc": 1.0}
    res = psv_module.size_gas(si, "SI")
    assert res["error"] is False and res["area_unit"] == "mm²"
    assert res["orifice"] == "H"
    assert 455 < res["area"] < 470          # ≈ 461.4 mm² (0.7152 in² — the SI constant 0.03948 vs 520 rounds differently)


def test_restore_falls_back_to_defaults_for_incomplete_panels(html):
    """v3.8.1 — the reason the defaults were invisible to returning visitors: a saved session
    restores over the HTML value= attributes. applyState() must call psvEnsureDefaults() after
    the inputs are applied and before recomputeAll(); liquid accepts EITHER P1 (certified) or
    Ps (non-certified) as the pressure requirement, or a certified case would be wiped because
    the hidden Ps is blank."""
    a = html.index("function applyState(")
    seg = html[a:html.index("function scheduleSave", a)]
    assert seg.index("applyInputs(s.inputs)") < seg.index("psvEnsureDefaults();") < seg.index("recomputeAll();")
    req = re.search(r"const PSV_PANEL_REQUIRED = \{(.*?)\n    \};", html, re.S).group(1)
    assert "['psv-P1-liq', 'psv-Ps']" in req
    for panel in ("gas:", "steam:", "liquid:", "twophase:"):
        assert panel in req
    # the reset restores the shipped defaults — inputs, selects and basis — not blanks
    reset = html[html.index("function psvResetPanel("):html.index("function psvEnsureDefaults(")]
    assert "el.defaultValue" in reset and "defaultSelected" in reset and "setPsvPressMode(" in reset
