"""LNG Cargo Estimator (v3.5) — Vector 13 pins, vessel-dataset provenance and source guards;
plus the v3.5 GT Fuel unit switches (lb/scf density, MMBtu/GJ energy, scf volume).

Two things this module exists to protect:

  * PROVENANCE. The vessel catalogue is deliberately a curated set of representative ships,
    each carrying its OWN public source URL, so the app never reproduces the IGU World LNG
    Report's Appendix 3 (all-rights-reserved; EU/UK database right; Rystad Energy data). If a
    row ever loses its source, or a source points at an AIS/spotter site (MarineTraffic,
    VesselFinder, ...) whose terms forbid reuse, this fails. Photos are Wikimedia Commons
    CC/PD works only, and every one must be credited from assets/vessels/CREDITS.json.

  * THE STANDARD-DENSITY TRAP. rho_std is mass per STANDARD volume, and the app's standard
    bases are 0 C (Nm3) and 60 F (scf) via the mandated 37.3258. So lb/scf -> kg/Nm3 is
    0.45359237 x 37.3258 = 16.9307, NOT the 16.0185 that converts an actual-condition lb/ft3.
    Using 16.0185 reads 5.7 % high, silently. The factor is derived, named and pinned.
"""

import json
import os
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# The AIS/spotter sites whose terms forbid reuse — never a cited source, never an image host.
DISALLOWED_HOSTS = ("marinetraffic.com", "vesselfinder.com", "balticshipping.com", "fleetmon.com",
                    "equasis.org", "myshiptracking.com", "vesseltracker.com", "shipspotting.com")
FREE_LICENCES = re.compile(r"^(CC BY(-SA)?( \d\.\d( [A-Z]{2})?)?|Public domain)$")


@pytest.fixture(scope="module")
def html():
    return (REPO_ROOT / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def spec():
    return (REPO_ROOT / "docs" / "SPECIFICATION.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def vessels(html):
    m = re.findall(r"const LNG_VESSELS = JSON\.parse\(`(.*?)`\);", html, re.DOTALL)
    assert len(m) == 1, "LNG_VESSELS must stay ONE JSON.parse literal (extraction contract)"
    return json.loads(m[0])


@pytest.fixture(scope="module")
def credits():
    with open(REPO_ROOT / "assets" / "vessels" / "CREDITS.json", encoding="utf-8") as fh:
        return {c["imo"]: c for c in json.load(fh)}


# ── Named, derived unit constants ────────────────────────────────────────────────

def test_energy_and_density_constants_are_derived_not_hardcoded(html):
    """The literal lines are pinned: a well-meaning edit that types 16.93 or 3.412 by hand
    loses the derivation that makes the value auditable."""
    for line in ("const GJ_PER_MMBTU = 1.055056;",
                 "const MJ_PER_MWH = 3600;",
                 "const KG_PER_LB = 0.45359237;",
                 "const RHO_LBSCF_TO_KGNM3 = KG_PER_LB * 37.3258;"):
        assert line in html, line


def test_lb_scf_density_uses_the_standard_volume_factor():
    """0.8193 kg/Nm3 <-> 0.04839 lb/scf. With the actual-density factor it would read 0.05115."""
    factor = 0.45359237 * 37.3258
    assert abs(factor - 16.9307) < 5e-5
    assert abs(0.8193 / factor - 0.04839) < 5e-6
    assert abs(0.8193 / 16.0185 - 0.05115) < 5e-6      # the trap, documented on screen
    assert abs(0.8193 / 16.0185 / (0.8193 / factor) - 1.057) < 1e-3


def test_gt_density_select_never_uses_the_actual_density_factor(html):
    """gt-rho-u must route through RHO_LBSCF_TO_KGNM3; the mf-/dp- density selects keep 16.0185
    because those ARE actual-condition densities."""
    assert 'id="gt-rho-u"' in html
    assert "(gv('gt-rho-u') === 'lbscf' ? RHO_LBSCF_TO_KGNM3 : 1)" in html
    m = re.search(r'<select id="gt-rho-u"[^>]*>(.*?)</select>', html)
    assert m and "16.0185" not in m.group(1)
    assert 'value="lbscf"' in m.group(1) and 'value="kgnm3"' in m.group(1)


def test_import_from_ghv_respects_the_density_unit(html):
    assert "(rhoU === 'lbscf' ? lastGHV.rho / RHO_LBSCF_TO_KGNM3 : lastGHV.rho).toFixed(5)" in html


def test_gt_last_result_rho_stays_si(html):
    """sendGTToMassVol writes gtLastResult.rho into mf-rho with mf-rho-u = kg/m3; the stored
    density must therefore be kg/Nm3 whatever the select shows."""
    assert "gtLastResult = { P: P, Q: Q, V: V, mkg: mkg, rho: rho, avail: avail };" in html
    assert "const rho = (parseValue(gv('gt-rho')) || 0) * (gv('gt-rho-u') === 'lbscf' ? RHO_LBSCF_TO_KGNM3 : 1);" in html


# ── GT totals: the defaults must still reproduce Vector 11's strings ─────────────

def test_gt_totals_default_units_are_unchanged(html):
    for sel, first in (("gt-tot-vol-u", 'value="nm3"'), ("gt-tot-e-u", 'value="mwh"'), ("gt-tot-q-u", 'value="gj"'),
                       ("gt-out-q-u", 'value="mwth"'), ("gt-rho-u", 'value="kgnm3"')):
        m = re.search(r'<select id="%s"[^>]*>\s*<option ([^>]*)>' % sel, html)
        assert m and first in m.group(1), f"{sel}: first option must be {first}"


def test_gt_totals_have_a_fuel_energy_column(html):
    for k in "hdmy":
        assert f'id="gt-tot-{k}-q"' in html
    assert "'gt-tot-h-q', 'gt-tot-d-q', 'gt-tot-m-q', 'gt-tot-y-q'" in html, "new outputs must be blanked on invalid input"


def test_vector11_totals_in_switched_units():
    """Vector 11 (M701JAC 448 MW, eta 44 %, LHV 40.25, rho 0.8193, 92 %) through the new unit
    families — the figures shown in the proposal mock-up, reproduced here."""
    P, eff, lhv, rho, avail = 448.0, 0.44, 40.25, 0.8193, 0.92
    Q = P / eff; V = Q * 3600 / lhv; mkg = V * rho
    yr = 8760 * avail
    assert f"{V*yr*37.3258/1e9:,.3f}" == "27.394"          # Bscf
    assert f"{Q*yr*3.6/1.055056/1e6:,.2f}" == "28.00"       # TBtu fuel energy in
    assert f"{P*yr*3.6/1.055056/1e6:,.2f}" == "12.32"       # TBtu sent out
    assert f"{P*yr*3.6/1e6:,.2f}" == "13.00"                # PJ sent out
    assert f"{Q*3.6/1.055056:,.1f}" == "3,474.2"            # MMBtu/h fuel energy input
    assert f"{V*37.3258/1e6:,.2f}" == "3.40"                # MMscf hourly


# ── Vessel dataset ───────────────────────────────────────────────────────────────

def test_dataset_shape(vessels):
    assert len(vessels) == 36
    ids = [v["id"] for v in vessels]
    assert len(ids) == len(set(ids)), "duplicate vessel ids"
    for v in vessels:
        assert re.fullmatch(r"\d{7}", v["id"]), v["id"]           # IMO number
        assert v["name"].strip() and v["owner"].strip() and v["builder"].strip(), v["id"]
        assert 20000 <= v["cap"] <= 270000, v["id"]
        assert v["cont"] in {"membrane", "moss", "ssp", "typec"}, v["id"]
        assert v["type"] in {"qmax", "qflex", "conv", "ice", "fsru", "fsu", "mid", "small"}, v["id"]
        assert 1970 <= v["year"] <= 2026, v["id"]
        assert v["prop"].strip(), v["id"]


def test_every_class_containment_and_propulsion_is_represented(vessels):
    """The point of a curated set is coverage: every vessel type, all four containment systems,
    all nine propulsion families in the end-2025 fleet."""
    assert {v["type"] for v in vessels} == {"qmax", "qflex", "conv", "ice", "fsru", "fsu", "mid", "small"}
    assert {v["cont"] for v in vessels} == {"membrane", "moss", "ssp", "typec"}
    assert {v["prop"] for v in vessels} >= {"DFDE", "Steam", "X-DF", "ME-GI", "ME-GA", "SSD", "Steam reheat", "STaGE", "TFDE"}


def test_every_vessel_carries_its_own_public_source(vessels):
    """PROVENANCE. No row may cite the IGU report as its source, and no row may cite an
    AIS/spotter site — the first would reproduce a rights-reserved table, the second breaches
    those sites' terms of use."""
    for v in vessels:
        assert v["src"].strip() and not v["src"].startswith("("), f"{v['id']} {v['name']}: source label missing"
        assert v["srcUrl"].startswith("https://") or v["srcUrl"].startswith("http://"), f"{v['id']}: source URL missing"
        assert not any(h in v["srcUrl"].lower() for h in DISALLOWED_HOSTS), f"{v['id']}: AIS/spotter site cited as source"
        assert "igu.org" not in v["srcUrl"].lower() and "datocms" not in v["srcUrl"].lower(), f"{v['id']}: IGU report cited as the row's source"


def test_photos_are_free_licensed_credited_and_present(vessels, credits):
    """Every photo flag must correspond to a real file AND a CREDITS.json entry with a CC/PD
    licence, and the credit rendered on screen must be the credit recorded there."""
    for v in vessels:
        path = REPO_ROOT / "assets" / "vessels" / f"{v['id']}.jpg"
        if v["photo"]:
            assert path.exists(), f"{v['id']}: photo flagged but file missing"
            c = credits.get(v["id"])
            assert c, f"{v['id']}: photo without a CREDITS.json entry"
            assert FREE_LICENCES.match(c["licence"]), f"{v['id']}: non-free licence {c['licence']!r}"
            assert v["credit"] == c["credit_line"], f"{v['id']}: on-screen credit differs from CREDITS.json"
            assert v["creditUrl"] == c["file_page_url"] and "commons.wikimedia.org" in v["creditUrl"]
            assert path.stat().st_size <= 130 * 1024, f"{v['id']}: thumbnail over 130 KB"
            assert not any(h in c["file_page_url"].lower() for h in DISALLOWED_HOSTS)
        else:
            assert not path.exists(), f"{v['id']}: file present but photo flag is 0"
            assert v["credit"] == "" and v["creditUrl"] == ""
    # and no orphan images
    for f in os.listdir(REPO_ROOT / "assets" / "vessels"):
        if f.endswith(".jpg"):
            assert any(v["id"] + ".jpg" == f and v["photo"] for v in vessels), f"orphan image {f}"


def test_credits_readme_disclaims_mit(credits):
    readme = (REPO_ROOT / "assets" / "vessels" / "README.md").read_text(encoding="utf-8")
    assert "MIT" in readme and ("NOT" in readme or "not covered" in readme.lower())
    for imo, c in credits.items():
        assert c["author"].strip() and c["credit_line"].strip() and c["file_page_url"].startswith("https://commons.wikimedia.org/wiki/File:")


# ── Static option list, wiring, source guards ───────────────────────────────────

def test_vessel_select_options_are_static_and_complete(html, vessels):
    """Options are hidden/disabled by the filters, never rebuilt — a share-link restore sets
    lc-vessel before any event fires (same rule as gt-model / comp-preset)."""
    start = html.index('id="lc-vessel"')
    end = html.index("</select>", start)
    block = html[start:end]
    assert '<option value="" data-i18n="advanced.lngCargo.manualOption">' in block
    opt_ids = set(re.findall(r'<option value="(\d{7})">', block))
    assert opt_ids == {v["id"] for v in vessels}
    assert "innerHTML" not in html[html.index("function lcFilterVesselOptions"):html.index("function lcSetFilter")]


def test_card_reads_the_ghv_bridge_and_never_recomputes_jis(html):
    """rho_liq / rho_std / HHV / LHV arrive through lastLNGProps, assigned INSIDE calcGHV — the
    card must not touch gasComps, ISO6578_VM or calcLNGDensity itself."""
    assert "lastLNGProps = { rhoLiq: rho_liq, tLiqK: tLiqK, rhoStd: rho_std, hhv: hhv_mix, lhv: lhv_mix, mw: mw_mix };" in html
    assert "lastGHV = { hhv: hhv_mix, lhv: lhv_mix, rho: rho_std };" in html   # untouched
    body = html[html.index("function calcLNGCargo()"):html.index("function lcRenderCatalogueIfStale")]
    for forbidden in ("gasComps", "ISO6578_VM", "calcLNGDensity(", "sqrtbi"):
        assert forbidden not in body, forbidden


def test_card_is_wired_into_recompute_and_ghv(html):
    assert "calcGTFuel, calcLNGCargo, updatePSVMode].forEach" in html
    assert "calcLNGCargo();   // v3.5 — the cargo card follows every composition change" in html
    assert "if (typeof calcLNGCargo === 'function') calcLNGCargo();   // v3.5 — cargoes-per-year chip" in html
    for fn in ("function calcLNGCargo(", "function selectLNGVessel(", "function lcVesselChanged(",
               "function lcFilterVesselOptions(", "function lcSetFilter(", "function renderLNGCatalogue(",
               "function lcRenderCatalogueIfStale(", "function lcRenderVessel("):
        assert fn in html, fn


def test_vessel_panel_uses_no_innerhtml(html):
    body = html[html.index("function lcRenderVessel("):html.index("function calcLNGCargo()")]
    assert ".innerHTML" not in body


def test_catalogue_escapes_and_links_out_only(html):
    body = html[html.index("function renderLNGCatalogue("):html.index("// --- ADVANCED ENG & HYDRAULICS ---") if "// --- ADVANCED ENG & HYDRAULICS ---" in html[html.index("function renderLNGCatalogue("):] else None]
    assert "escH(" in body
    assert "marinetraffic.com/en/ais/details/ships/imo:" in html and "vesselfinder.com/vessels/details/" in html
    assert 'rel="noopener noreferrer nofollow"' in html
    assert "<iframe" not in html.lower().split("adv-lng-cargo")[1][:20000]


def test_analytics_map_has_the_lc_prefix(html):
    assert "'lc': 'lng-cargo'," in html


def test_export_report_has_section_7(html):
    assert "js.export.section7Title" in html and "${lc}" in html


# ── Vector 13 — the worked example the docs quote ────────────────────────────────

# rho_liq is the app's ISO 6578 (Klosek-McKinley) value for the Australia NWS preset at 113.15 K,
# read from lastLNGProps and pinned here to the precision the chain needs. rho_std / HHV / LHV are
# the same preset's Vector 12 figures.
V13 = dict(rho_liq=467.31677, rho_std=0.83108, hhv=45.32, lhv=40.93, cap=174000, fill=0.985)


def _fmt(n, dp): return f"{n:,.{dp}f}"


def test_vector13_cargo_chain():
    Vl = V13["cap"] * V13["fill"]
    massT = Vl * V13["rho_liq"] / 1000
    nm3 = massT * 1000 / V13["rho_std"]
    mj = nm3 * V13["hhv"]
    assert _fmt(Vl, 0) == "171,390"
    assert _fmt(massT, 0) == "80,093"
    assert _fmt(nm3 / 1000, 0) == "96,373"
    assert _fmt(nm3 * 37.3258 / 1e6, 0) == "3,597"                       # MMscf
    assert _fmt(mj / 1000 / 1.055056 / 1e6, 3) == "4.140"                # TBtu, HHV
    assert _fmt(nm3 * V13["lhv"] / 1000 / 1.055056 / 1e6, 3) == "3.739"  # TBtu, LHV
    assert _fmt((mj / 1000 / 1.055056) / massT, 2) == "51.69"            # MMBtu/t
    assert _fmt(nm3 / Vl, 0) == "562"                                     # Nm3 per m3 liquid
    # delivered: heel 3,000 m3, BOR 0.10 %/day, 15 days
    Vd = Vl - 3000 - Vl * 0.001 * 15
    assert _fmt(Vd, 0) == "165,819"
    assert _fmt(Vd * V13["rho_liq"] / 1000 * 1000 / V13["rho_std"] * V13["hhv"] / 1000 / 1.055056 / 1e6, 3) == "4.005"


def test_vector13_page_and_spec_agree(html, spec):
    """The same digits appear at least twice in the page (How To Use + Theory) and once in
    the SPECIFICATION vector table — a change to any copy without the others fails."""
    for token in ("171,390", "80,093", "96,373", "4.140", "3.739", "51.69"):
        assert html.count(token) >= 2, f"{token} appears fewer than twice in index.html"
        assert token in spec, f"{token} missing from SPECIFICATION.md"


# ── Theory sub-heading numbering after the v3.5 renumber ─────────────────────────

SUBHEAD = re.compile(r"<h4[^>]*>\s*([0-9IVX]+)\.(\d+)\s")


@pytest.mark.parametrize("fname", ["index.html"] + [f"i18n/{l}.json" for l in
                         ("ja", "zh", "ko", "th", "id", "ru", "es", "fr", "de")])
def test_theory_subheadings_are_arabic_and_match_their_part(fname):
    """v3.5 inserted Part IX and shifted X–XIII by script. The Roman placeholder used during
    that renumber leaked into the English h4 sub-headings once ('X.1 Pressure Drop …'); this
    pins Arabic numbers everywhere and, for the inline English, that each 10.x/11.x/12.x
    heading really sits under Part X/XI/XII. v3.6 swapped Parts XI and XII (GT Fuel moved
    ahead of Safety in the tab order): XI is now the 4-heading GT Part, XII the 7-heading PRV Part."""
    text = (REPO_ROOT / fname).read_text(encoding="utf-8")
    heads = SUBHEAD.findall(text)
    assert heads, fname
    roman = [f"{a}.{b}" for a, b in heads if not a.isdigit()]
    assert not roman, f"{fname}: Roman-numbered sub-headings {roman}"
    if fname == "index.html":
        for part, want in ((10, 5), (11, 4), (12, 7)):
            got = [f"{a}.{b}" for a, b in heads if a == str(part)]
            assert len(got) == want, f"Part {part}: expected {want} sub-headings, got {got}"


# ── v3.6 Advanced sub-panes: every card must sit inside exactly one pane ─────────

def test_advanced_sub_panes_are_div_balanced_and_own_their_cards():
    """v3.6.1: a stray </div> that had closed the ΔP card's NORSOK line-sizing grid on the very
    next line since v2.8 made the ΔP card end one level early, so the Flow Regime card became a
    sibling of the sub-panes and stayed visible on every sub-tab. Pin each pane to a balanced
    <div> count and each headline card to its pane."""
    html = (REPO_ROOT / "index.html").read_text(encoding="utf-8")
    bounds = ['<div id="adv-sub-gasq"', '<div id="adv-sub-hyd"', '<div id="adv-sub-gtfuel"', '<div id="tab-safety"']
    idx = [html.index(b) for b in bounds]
    assert idx == sorted(idx), "sub-panes out of order"
    owner = {"advanced.ghv.title": "gasq", "advanced.lngCargo.title": "gasq",
             "advanced.deltaP.title": "hyd", "advanced.flowRegime.title": "hyd", "gtfuel.sel.title": "gtfuel"}
    for pane, start, end in zip(("gasq", "hyd", "gtfuel"), idx, idx[1:]):
        region = html[start:end]
        # the pane's own <div> is the +1 that its final </div> cancels; a card leaking out shows as ≠ 0
        opens, closes = len(re.findall(r"<div\b", region)), region.count("</div>")
        extra = 1 if pane == "gtfuel" else 0          # the last region also holds tab-advanced's own </div>
        assert opens + extra == closes, f"{pane}: {opens} <div> vs {closes} </div> — a card is leaking out of the pane"
        for key, want in owner.items():
            if f'data-i18n="{key}"' in region:
                assert want == pane, f"{key} found in pane {pane}, expected {want}"
    assert 'data-i18n="advanced.flowRegime.title"' in html[idx[1]:idx[2]]
