"""LNG reference compositions (v3.3) — dataset integrity and published cross-checks.

The preset selector's whole value proposition is that the "published" tier is
*traceable*: each entry carries the composition AND the calorific value its source
published for that composition. This module re-runs the JIS K 2301:2011 chain in
Python — the same replica the other JS surfaces are verified with — and asserts the
calculator lands on the source's own published GCV and Wobbe Index.

That makes this a dual-purpose test. It catches a transcription error in the dataset,
and it independently re-verifies the JIS engine itself against five external reference
points that were not derived from the app.

Dataset doctrine, mirroring GT_MODELS:
  * one JSON.parse literal, extracted verbatim here;
  * every entry cites its source in `src`, and the citation is never dropped;
  * a "pub"/"ref" entry MUST carry gcv/wi (there is a published figure to check);
  * an "asm" entry MUST NOT (it is an assumption — there is nothing to check against,
    and inventing a cross-check would dress up a guess as a citation).
"""

import json
import math
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# MJ/Nm³. The UI passes a cross-check when |calc − published| <= LNG_PRESET_TOL; the
# suite holds the dataset to the same band it advertises on screen.
TOL = 0.05

TIERS = {"pub", "ref", "asm"}
BASES = {"mol", "vol"}


# ── JIS K 2301:2011 replica (mirrors calcGHV() in index.html) ────────────────────

# id: (mw, hhv, lhv, zi, sqrt_bi, si) — must match the gasComps table in index.html.
COMPONENTS = {
    "ch4":  (16.043,  39.84,  35.818, 0.9976, 0.049,  0.554),
    "c2h6": (30.07,   69.79,  63.76,  0.99,   0.1,    1.039),
    "c3h8": (44.097,  99.22,  91.18,  0.9789, 0.1453, 1.523),
    "ic4":  (58.123, 128.23, 118.18,  0.958,  0.2049, 2.008),
    "nc4":  (58.123, 128.66, 118.61,  0.9572, 0.2069, 2.008),
    "ic5":  (72.15,  157.76, 145.59,  0.937,  0.251,  2.493),
    "nc5":  (72.15,  158.07, 146.00,  0.918,  0.2864, 2.493),
    "nc6":  (86.177, 187.53, 173.45,  0.892,  0.3286, 2.977),
    "c2h4": (28.054,  63.06,  59.04,  0.9925, 0.0866, 0.969),
    "c3h6": (42.081,  91.98,  85.94,  0.981,  0.1378, 1.454),
    "h2":   (2.016,   12.788, 10.777, 1.0006, 0.0,    0.0696),
    "co2":  (44.01,    0.0,    0.0,   0.9933, 0.0819, 1.52),
    "n2":   (28.0135,  0.0,    0.0,   0.9995, 0.0224, 0.968),
    "o2":   (31.9988,  0.0,    0.0,   0.999,  0.0316, 1.105),
}


def _round_half_up(value, places):
    """JS Math.round(x * 10**n) / 10**n. Python's round() is banker's rounding, which
    would disagree on exact .5 ties and silently shift a 4-d.p. mole fraction."""
    return math.floor(value * 10 ** places + 0.5) / 10 ** places


def jis_properties(composition, basis):
    """Returns (hhv, wi) for a percent-composition dict, on 'mol' or 'vol' basis."""
    total = sum(composition.values())
    raw = {k: (composition.get(k, 0.0) / total if total else 0.0) for k in COMPONENTS}

    if basis == "vol":
        scaled = {k: raw[k] / COMPONENTS[k][3] for k in COMPONENTS}
        denom = sum(scaled.values())
        x = {k: _round_half_up(scaled[k] / denom, 4) if denom else 0.0 for k in COMPONENTS}
    else:
        x = {k: _round_half_up(raw[k], 4) for k in COMPONENTS}

    sum_j = sum(_round_half_up(x[k] * COMPONENTS[k][4], 5) for k in COMPONENTS)
    z_exact = 1 - sum_j ** 2

    hhv = _round_half_up(sum(x[k] * COMPONENTS[k][1] for k in COMPONENTS) / z_exact, 2)
    sg = _round_half_up(sum(x[k] * COMPONENTS[k][5] for k in COMPONENTS) / z_exact, 3)
    wi = _round_half_up(hhv / math.sqrt(sg), 2) if sg > 0 else 0.0
    return hhv, wi


# ── Fixtures ─────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def html():
    return (REPO_ROOT / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def presets(html):
    matches = re.findall(r"const LNG_PRESETS = JSON\.parse\(`(.*?)`\);", html, re.DOTALL)
    assert len(matches) == 1, (
        "expected exactly one LNG_PRESETS JSON.parse literal — keep it as a single "
        "literal so this module can extract it verbatim")
    return json.loads(matches[0])


def _ids(presets):
    return [p["id"] for p in presets]


# ── The replica must reproduce the app's own regulatory reference vector ─────────

def test_replica_reproduces_the_claude_md_reference_vector():
    """Guards the guard. If this drifts, every assertion below is meaningless."""
    hhv, wi = jis_properties(
        {"ch4": 89, "c2h6": 7, "c3h8": 2.5, "ic4": 0.7, "nc4": 0.5, "n2": 0.3}, "vol")
    assert hhv == 44.59
    assert wi == 56.00


# ── Dataset integrity ────────────────────────────────────────────────────────────

def test_dataset_shape(presets):
    assert len(presets) == 9
    assert len(_ids(presets)) == len(set(_ids(presets))), "duplicate preset ids"
    for p in presets:
        assert p["tier"] in TIERS, p["id"]
        assert p["basis"] in BASES, p["id"]
        assert isinstance(p["src"], str) and p["src"].strip(), (
            f"{p['id']}: every entry must cite its source or state its assumption")
        assert p["c"], p["id"]
        for name, value in p["c"].items():
            assert name in COMPONENTS, f"{p['id']}: unknown component {name}"
            assert value > 0, f"{p['id']}: {name} listed as {value}; omit it instead"


def test_every_tier_is_represented(presets):
    assert {p["tier"] for p in presets} == TIERS


def test_published_entries_carry_a_cross_check_and_assumed_entries_do_not(presets):
    """The tier boundary is the honesty boundary: an assumption must not display a
    cross-check, because there is no published figure it could be checked against."""
    for p in presets:
        if p["tier"] == "asm":
            assert p["gcv"] is None and p["wi"] is None, (
                f"{p['id']}: an assumed composition must not claim a published value")
        else:
            assert isinstance(p["gcv"], (int, float)), p["id"]
            assert isinstance(p["wi"], (int, float)), p["id"]


def test_giignl_entries_cite_the_paper_and_disclose_the_c4_split(presets):
    giignl = [p for p in presets if "GIIGNL" in p["src"]]
    assert len(giignl) == 5, "expected the five GIIGNL Table 1 origins"
    for p in giignl:
        assert "Table 1" in p["src"], p["id"]
        assert "2018 GIIGNL Annual Report" in p["src"], p["id"]
        # The lumped C4+ column is the one assumption inside the published tier; it must
        # stay disclosed on screen rather than only in a commit message.
        assert "50/50" in p["src"] and "iC4/nC4" in p["src"], (
            f"{p['id']}: the C4+ split assumption must be stated in the citation")
        assert p["basis"] == "mol", (
            f"{p['id']}: GIIGNL Table 1 is mole %; reading it as volume % shifts GCV "
            "by about 0.06 MJ/Nm3 against the published figure")


def test_assumed_entries_state_their_own_numbers_in_the_citation(presets):
    """An assumption is only auditable if it says what it assumed."""
    for p in (x for x in presets if x["tier"] == "asm"):
        assert "mol %" in p["src"], p["id"]
        assert "CH4" in p["src"], p["id"]


# ── The published cross-checks the UI advertises ─────────────────────────────────

@pytest.mark.parametrize("preset_id,published_gcv,published_wi", [
    ("au-nws",       45.32, 56.53),
    ("my-bintulu",   43.67, 55.59),
    ("ng-bonny",     43.41, 55.50),
    ("qa-raslaffan", 43.43, 55.40),
    ("tt-atlantic",  41.05, 54.23),
    ("jis-ref",      44.59, 56.00),
])
def test_published_figures_are_transcribed_faithfully(presets, preset_id,
                                                      published_gcv, published_wi):
    """Pins the source's numbers independently of the composition, so a typo in the
    dataset's gcv/wi fields cannot quietly widen the band it is checked against."""
    p = next(x for x in presets if x["id"] == preset_id)
    assert p["gcv"] == published_gcv
    assert p["wi"] == published_wi


def test_calculator_reproduces_every_published_gcv_and_wobbe_index(presets):
    """The headline claim. Five of these six reference points are external to this
    project entirely — they check the JIS engine, not just the dataset."""
    failures = []
    for p in presets:
        if p["gcv"] is None:
            continue
        hhv, wi = jis_properties(p["c"], p["basis"])
        if abs(hhv - p["gcv"]) > TOL:
            failures.append(f"{p['id']}: GCV calc {hhv} vs published {p['gcv']}")
        if abs(wi - p["wi"]) > TOL:
            failures.append(f"{p['id']}: WI calc {wi} vs published {p['wi']}")
    assert not failures, "cross-check outside ±%.2f MJ/Nm3:\n  %s" % (
        TOL, "\n  ".join(failures))


C4_SPLIT_MAX_SPREAD = 0.03  # MJ/Nm³ — worst observed: Bintulu's Wobbe index


def test_c4_split_assumption_is_immaterial(presets):
    """The claim made on screen — that splitting the lumped C4+ column 50/50 moves HHV
    and WI by no more than 0.03 MJ/Nm3 — is asserted here rather than trusted. Sweeps
    each GIIGNL entry's butane pool across the full iC4/nC4 range and re-runs the chain.

    The spread must also stay inside the ±0.05 band the cross-check chips advertise,
    otherwise the split alone could flip a preset's own cross-check from pass to fail.
    """
    assert C4_SPLIT_MAX_SPREAD < TOL, (
        "the C4-split spread must stay inside the cross-check tolerance")

    for p in (x for x in presets if "GIIGNL" in x["src"]):
        pool = p["c"].get("ic4", 0.0) + p["c"].get("nc4", 0.0)
        if pool <= 0:
            continue
        hhvs, wis = [], []
        for step in range(11):
            variant = dict(p["c"])
            variant["ic4"] = pool * step / 10
            variant["nc4"] = pool * (10 - step) / 10
            variant = {k: v for k, v in variant.items() if v > 0}
            hhv, wi = jis_properties(variant, p["basis"])
            hhvs.append(hhv)
            wis.append(wi)
        for label, values in (("HHV", hhvs), ("WI", wis)):
            spread = max(values) - min(values)
            assert spread <= C4_SPLIT_MAX_SPREAD + 1e-9, (
                f"{p['id']}: {label} spread across the iC4/nC4 split is {spread:.3f} "
                "MJ/Nm3, so the split is no longer immaterial and the citation's "
                "claim is now false")


def test_citations_state_the_measured_c4_sensitivity(presets):
    """The number in the citation and the number this suite enforces are the same
    number. A tightened claim that nobody re-measured is exactly how a disclosure
    becomes wrong."""
    for p in (x for x in presets if "GIIGNL" in x["src"]):
        assert f"<= {C4_SPLIT_MAX_SPREAD:.2f} MJ/Nm3" in p["src"], p["id"]


# ── Source-level guards on the wiring ────────────────────────────────────────────

def test_every_preset_id_has_a_static_option(html, presets):
    """Options are never rebuilt — a share-link restore sets comp-preset by value before
    any event fires, so a preset with no static <option> would silently fail to restore."""
    for p in presets:
        assert f'<option value="{p["id"]}">' in html, (
            f'{p["id"]}: no static <option> in the comp-preset list')


def test_custom_option_exists_and_is_the_empty_value(html):
    assert '<option value="" data-i18n="advanced.ghv.preset.custom">' in html


def test_cross_check_compares_gross_heating_value(html):
    """GCV is the GROSS calorific value: the cross-check must read hhv_mix, never the
    hv_mix that follows the HHV/LHV display toggle, or flipping the toggle would break
    the comparison against a published figure that never moved."""
    assert "lastCompCheck = { gcv: hhv_mix, wi: wi_calc };" in html
    assert "gcv: hv_mix" not in html


def test_editing_a_component_drops_the_attribution(html):
    """A citation must never label numbers the user has since edited."""
    assert "if (sel && sel.value) { sel.value = ''; renderLNGPresetInfo(); }" in html


def test_preset_info_is_repainted_from_calc_ghv(html):
    """Repainting only inside applyLNGPreset() would leave a restored share link showing
    a preset name with no citation beside it."""
    calc_ghv = html[html.index("function calcGHV()"):]
    assert "renderLNGPresetInfo();" in calc_ghv[:calc_ghv.index("function ")+20000]


def test_preset_rendering_never_uses_innerhtml(html):
    """The citation line is source-controlled text, but it is still injected next to
    user-facing state; keeping the renderer on textContent means it can never become an
    injection surface if the dataset later carries anything externally supplied."""
    start = html.index("function renderLNGPresetInfo()")
    end = html.index("function calcGHV()", start)
    # Assignment form only — the function's own comment names innerHTML to explain why
    # it is absent, and that prose should not be what keeps this test green.
    assert not re.search(r"\.innerHTML\s*\+?=", html[start:end])
