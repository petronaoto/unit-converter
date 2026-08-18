"""GT Fuel tab (v3.1) — Vector 11 pins, dataset integrity and source-level guards.

The card is client-side JavaScript, so pytest verifies it the same way the other
JS surfaces are verified: the GT_MODELS dataset is extracted from the JSON.parse
literal (the IF97 extraction contract), the estimator arithmetic is re-run here
in Python through the exact path the UI takes, and the resulting display strings
are pinned against both the documentation tabs and docs/SPECIFICATION.md §9
Vector 11. The browser side is verified by hand, same as Vectors 1, 8 and 9.

Dataset doctrine: every entry is transcribed from a named vendor publication
(src field), and vendors round heat rate and efficiency independently — the
HR ≡ 3600/η identity must therefore hold within a small tolerance, which makes
transcription errors loud without demanding impossible exactness.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

VENDORS = {"MHI", "GE Vernova", "Siemens Energy"}
CLASSES = {"HD", "AD", "IND"}
SVGS = {"hd", "ad", "ind"}
HR_TOL_KJ = 30.0  # worst published pair observed: LM6000 at ~20 kJ/kWh


@pytest.fixture(scope="module")
def html():
    return (REPO_ROOT / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def spec():
    return (REPO_ROOT / "docs" / "SPECIFICATION.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def models(html):
    matches = re.findall(r"const GT_MODELS = JSON\.parse\(`(.*?)`\);", html, re.DOTALL)
    assert len(matches) == 1
    return json.loads(matches[0])


# ── Dataset integrity ────────────────────────────────────────────────────────────

def test_dataset_shape(models):
    assert len(models) == 31
    ids = [m["id"] for m in models]
    assert len(ids) == len(set(ids)), "duplicate model ids"
    for m in models:
        assert m["vendor"] in VENDORS, m["id"]
        assert m["hz"] in (0, 50, 60), m["id"]
        assert m["cls"] in CLASSES, m["id"]
        assert m["svg"] in SVGS, m["id"]
        assert m["scMW"] > 0 and 0 < m["scEff"] < 100, m["id"]
        assert m["hrKJ"] > 0, m["id"]
        assert isinstance(m["src"], str) and m["src"].strip(), (
            f"{m['id']}: every entry must cite its vendor source")


def test_all_three_vendors_and_classes_present(models):
    assert {m["vendor"] for m in models} == VENDORS
    assert {m["cls"] for m in models} == CLASSES


def test_heat_rate_consistent_with_efficiency(models):
    """Published HR must equal 3600/η within rounding — a transcription tripwire."""
    for m in models:
        implied = 360000.0 / m["scEff"]  # 3600 / (eff/100), kJ/kWh
        dev = abs(m["hrKJ"] - implied)
        assert dev <= HR_TOL_KJ, (
            f"{m['id']}: published HR {m['hrKJ']} vs 3600/eta {implied:.1f} "
            f"(dev {dev:.1f} kJ/kWh)")


def test_combined_cycle_entries_exceed_simple_cycle(models):
    for m in models:
        for cc in m["cc"]:
            assert cc["mw"] > m["scMW"], f"{m['id']}/{cc['cfg']}"
            assert cc["eff"] > m["scEff"], f"{m['id']}/{cc['cfg']}"
            assert cc["cfg"].strip(), m["id"]


def test_reference_mhi_rows_match_brochure(models):
    """Spot-pins straight from the MHI performance table (METP-11GT01E1-E-0)."""
    by_id = {m["id"]: m for m in models}
    m701jac = by_id["m701jac"]
    assert (m701jac["scMW"], m701jac["scEff"], m701jac["hrKJ"]) == (448.0, 44.0, 8182)
    assert (m701jac["exhKgS"], m701jac["exhC"], m701jac["titC"]) == (765, 663, 1650)
    assert m701jac["cc"][0]["mw"] == 650.0
    h25 = by_id["h25"]
    assert (h25["scMW"], h25["scEff"], h25["hrKJ"]) == (41.03, 36.2, 9949)
    m501jac = by_id["m501jac"]
    assert (m501jac["scMW"], m501jac["cc"][1]["mw"], m501jac["cc"][1]["eff"]) == (
        453.0, 1332.0, 64.2)


# ── Named constants ──────────────────────────────────────────────────────────────

def test_gt_constants_are_derived_not_hardcoded(html):
    assert "const GT_HV_FACTOR = 0.001055056 * 37.3258;" in html, (
        "Btu/scf conversion must be the derived product, same as HV_FACTOR")
    assert "const GT_H_YEAR = 8760, GT_H_MONTH = 730;" in html


# ── Vector 11 — docs/SPECIFICATION.md §9 ─────────────────────────────────────────
# Inputs: M701JAC (448) prefill + Vector 1's reference gas.
P_MW = 448.0
ETA = 0.44
LHV = 40.25      # MJ/Nm³
RHO = 0.8193     # kg/Nm³ (the card's default input, 4 dp)
AVAIL = 0.92


def fmt(n, dp):
    """Mirror of the card's toLocaleString('en-US', {min/maxFractionDigits: dp})."""
    return f"{n:,.{dp}f}"


def test_vector11_core_numbers():
    q = P_MW / ETA
    hr = 3600.0 / ETA
    v = q * 3600.0 / LHV
    mkg = v * RHO
    assert fmt(q, 2) == "1,018.18"
    assert fmt(hr, 0) == "8,182"                      # matches MHI's published HR
    assert fmt(hr / 1.055056, 0) == "7,755"
    assert fmt(v / 1000.0, 2) == "91.07"              # kNm³/h display
    assert fmt(round(v), 0) == "91,067"               # Nm³/h, docs prose
    assert fmt(mkg / 1000.0, 2) == "74.61"            # t/h display
    assert fmt(round(mkg), 0) == "74,611"             # kg/h, docs prose
    assert fmt(v * 37.3258 * 24 / 1e6, 2) == "81.58"  # MMSCFD display


def test_vector11_totals():
    q = P_MW / ETA
    v = q * 3600.0 / LHV
    mkg = v * RHO
    yearly_vol = v * 8760 * AVAIL
    yearly_mass_t = mkg * 8760 * AVAIL / 1000.0
    monthly_vol = v * 730 * AVAIL
    assert fmt(yearly_vol / 1e6, 2) == "733.93"       # MMNm³ display
    assert fmt(yearly_mass_t, 0) == "601,308"         # t display
    assert fmt(monthly_vol / 1e6, 2) == "61.16"       # MMNm³ display
    assert fmt(P_MW * 8760 * AVAIL / 1000.0, 1) == "3,610.5"  # GWh, docs prose


def test_vector11_hv_unit_conversion():
    """LHV 40.25 MJ/Nm³ in Btu/scf through the shared factor."""
    factor = 0.001055056 * 37.3258
    assert round(40.25 / factor, 1) == 1022.1
    assert round(1.0 / factor, 3) == 25.393


def test_vector11_page_and_spec_agree(html, spec):
    """The worked example must print the same digits in the How To Use tab, the
    Theory tab and SPECIFICATION §9 (test_npsh.py doctrine)."""
    for token in ("1,018.18", "8,182", "7,755", "91.07", "74.61", "81.58",
                  "733.93", "601,308"):
        assert html.count(token) >= 2, f"{token} missing from a documentation tab"
        assert token in spec, f"{token} missing from SPECIFICATION.md"


def test_m701jac_prefill_reproduces_vector11(models):
    """One click on the default model must land exactly on Vector 11's inputs."""
    m = next(m for m in models if m["id"] == "m701jac")
    assert m["scMW"] == P_MW
    assert m["scEff"] == ETA * 100


# ── Source-level guards ──────────────────────────────────────────────────────────

def test_gt_functions_exist_and_are_wired(html):
    for fn in ("function calcGTFuel(", "function selectGTModel(",
               "function renderGTCatalogue(", "function importGHVToGT(",
               "function sendGTToMassVol(", "function gtFilterModelOptions("):
        assert fn in html, f"{fn} missing"
    m = re.search(r"\[calcGHV,.*?\]\.forEach", html)
    assert m and "calcGTFuel" in m.group(0), "calcGTFuel missing from recomputeAll()"
    # v3.6 — GT Fuel is a sub-pane of the Advanced tab, not a top-level tab. The legacy
    # 'gtfuel' tab id must keep working (pre-v3.6 share links) by mapping onto the sub-tab.
    tabs_src = html[html.index("const tabs = ["):html.index("const tabs = [") + 200]
    assert "'gtfuel'" not in tabs_src, "gtfuel must not be a top-level tab from v3.6"
    assert "if (tabId === 'gtfuel') { tabId = 'advanced'; switchAdvSub('gtfuel', true); }" in html, (
        "legacy switchTab('gtfuel') mapping missing")
    for needle in ('id="adv-sub-gtfuel"', 'id="advbtn-gtfuel"', "function switchAdvSub(",
                   "ADV_SUBS = ['gasq', 'hyd', 'gtfuel']", "advSub: currentAdvSub"):
        assert needle in html, f"{needle} missing"


def test_last_ghv_bridge(html):
    """The Advanced-tab import bridge: declared null, assigned inside calcGHV()."""
    assert "let lastGHV = null;" in html
    body = html[html.index("function calcGHV"):]
    body = body[:body.index("\n    function ")]
    assert "lastGHV = { hhv: hhv_mix, lhv: lhv_mix, rho: rho_std };" in body


def test_model_select_options_are_static_and_complete(html, models):
    """Share-link restore sets gt-model before any event fires, so every dataset
    id must exist as a static <option> (options are filtered, never rebuilt)."""
    sel = html[html.index('id="gt-model"'):html.index('id="gt-cycle"')]
    opts = set(re.findall(r'<option value="([a-z0-9\-]+)"', sel))
    assert opts == {m["id"] for m in models}


def test_svg_symbols_exist_for_all_archetypes(html, models):
    for key in sorted({m["svg"] for m in models}):
        assert f'<symbol id="gt-svg-{key}"' in html, f"missing thumbnail symbol {key}"
