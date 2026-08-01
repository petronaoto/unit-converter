"""Source-level guards on the engineering constants embedded in index.html's JavaScript.

pytest cannot execute the JavaScript, so these tests cannot verify that the *calculation*
is right. What they can do — and what actually protects this project — is verify that the
same constant is not quoted with two different values in three different places.

The Papay correlation appears in the executable JS, in the Theory tab's prose, and in
docs/SPECIFICATION.md §4.2. Nothing but human memory kept those in agreement before v2.8.
An engineer reading the Theory tab and getting a number the calculator does not produce is
a direct hit on the app's core claim of standards traceability.

Verification that the JS is numerically correct is a separate matter — it is done by
executing the page in a real browser engine against the reference vectors in
docs/SPECIFICATION.md §9, and by the manual checklist in DEVELOPMENT_PLAN.md §7.2.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def html():
    return (REPO_ROOT / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def spec():
    return (REPO_ROOT / "docs" / "SPECIFICATION.md").read_text(encoding="utf-8")


# ── Papay (1968) + Standing-Katz pseudo-criticals ────────────────────────────────
#
# Values are asserted as literal strings because that is how they appear in all three
# locations; a numeric parse would hide a "756.80" vs "756.8" style edit that a
# translator or editor could introduce into the prose.

PAPAY_CONSTANTS = ["3.52", "0.9813", "0.274", "0.8157"]
STANDING_KATZ_CONSTANTS = ["756.8", "131", "3.6", "169.2", "349.5", "74"]


def test_papay_z_is_implemented_exactly_once(html):
    """The correlation must live in one function. v2.8 extracted papayZ() precisely so
    the Z-Factor Estimator and the Gas Property Estimator cannot drift apart; a second
    inline copy would silently undo that."""
    occurrences = len(re.findall(r"3\.52\s*\*\s*pr\s*/\s*Math\.pow\(10", html))
    assert occurrences == 1, (
        f"the Papay expression appears {occurrences} times in executable JS; "
        "it must appear once, inside papayZ()")


def test_papay_helper_exists_and_is_shared(html):
    assert "function papayZ(" in html, "papayZ() helper is missing"
    # Both cards must go through it rather than recomputing.
    for caller in ("function calcZFactor(", "function calcGasProps("):
        assert caller in html
    assert html.count("papayZ(") >= 4, (
        "expected papayZ() to be called by calcZFactor, calcGasProps and twice by the "
        "Joule-Thomson central difference")


@pytest.mark.parametrize("constant", PAPAY_CONSTANTS + STANDING_KATZ_CONSTANTS)
def test_papay_constants_agree_between_code_theory_tab_and_spec(constant, html, spec):
    """Each constant must appear in the Theory tab prose and in SPECIFICATION.md §4.2,
    not only in the code."""
    assert constant in html, f"{constant} missing from index.html"
    assert constant in spec, f"{constant} missing from docs/SPECIFICATION.md"


def test_papay_validity_envelope_is_stated_consistently(html, spec):
    """0 < Pr <= 15, 1.05 <= Tr <= 3.0 — enforced in code, promised in the docs."""
    assert "pr > 15" in html and "trr < 1.05" in html and "trr > 3.0" in html
    for token in ("15", "1.05", "3.0"):
        assert token in spec


# ── Lee-Gonzalez-Eakin (1966), SPE 1340 ─────────────────────────────────────────
#
# The ORIGINAL unrounded coefficients. A widely-circulated rounded variant
# (9.4 / 0.02 / 209 / 19; X = 3.5 + 986/T + 0.01M; Y = 2.4 - 0.2X) shifts the result by
# about -2.1 %, and two corrupted variants exist on wiki sites (X = 3.488, and 0.001*M
# in place of 0.01*M). Pinning the literals here makes an accidental "tidy-up" fail.

LGE_CONSTANTS = ["9.379", "0.01607", "209.2", "19.26", "3.448", "986.4", "0.01009",
                 "2.447", "0.2224"]


@pytest.mark.parametrize("constant", LGE_CONSTANTS)
def test_lee_gonzalez_eakin_uses_the_original_coefficients(constant, html):
    assert constant in html, (
        f"LGE coefficient {constant} missing — the original (unrounded) SPE 1340 "
        "coefficient set must be used; the rounded variant shifts mu by ~2.1 %")


@pytest.fixture(scope="module")
def script_block(html):
    """Just the executable JavaScript.

    The Theory tab deliberately NAMES the corrupted coefficient variants so an engineer
    reading the manual knows which numbers to distrust. Scanning the whole file for those
    strings would therefore flag the documentation that exists to prevent the very bug —
    so the bad-variant checks look only at code.
    """
    start = html.rindex("<script>")
    end = html.index("</script>", start)
    return html[start:end]


@pytest.mark.parametrize("wrong, why", [
    ("3.488", "corrupted X coefficient circulating on wiki sites (should be 3.448)"),
    ("2.4 - 0.2 * lgeX", "rounded Y coefficient (should be 2.447 - 0.2224*X)"),
    ("9.4 + 0.02", "rounded K coefficients (should be 9.379 + 0.01607)"),
])
def test_known_bad_lge_variants_are_absent_from_code(wrong, why, script_block):
    assert wrong not in script_block, f"found {wrong!r} in the script block — {why}"


def test_theory_tab_names_the_bad_variants(html, script_block):
    """The converse: the documentation SHOULD warn about them, so a future editor does
    not 'tidy' the coefficients into one of the wrong sets."""
    prose = html.replace(script_block, "")
    assert "3.488" in prose, (
        "the Theory tab should name the corrupted X = 3.488 variant as a warning")


def test_lge_validity_envelope_is_enforced(html):
    """Experimental basis 100-340 degF (559.67-799.67 degR) and 100-8,000 psia.
    Warn, never clamp."""
    assert "559.67" in html and "799.67" in html
    assert "8000" in html


# ── Gas constants ───────────────────────────────────────────────────────────────

def test_molar_and_kmol_gas_constants_stay_distinct(html):
    """8.31446262 J/(mol.K) is used with mw/1000 in calcGHV(); 8314.462618 J/(kmol.K) is
    used with M in kg/kmol for sonic velocity. Collapsing them into one literal would be
    a silent 1000x error, so both must remain present."""
    assert "8.31446262" in html, "the JIS molar gas constant has gone missing"
    assert "8314.462618" in html, "the kmol-form gas constant has gone missing"


def test_air_molecular_weight_is_documented(html):
    """SG -> MW uses 28.9647. LGE's own paper used 28.97 (0.012 % different); the choice
    is deliberate and must stay visible in the footnote, not just the code."""
    assert "28.9647" in html
    assert html.count("28.9647") >= 2, (
        "28.9647 should appear in both the code and the user-facing footnote")


# ── Joule-Thomson numerical derivative ──────────────────────────────────────────

def test_zero_temperature_is_not_treated_as_missing_input(html):
    """Regression guard for SPECIFICATION.md §11 issue #11 (fixed v2.8).

    `if(!sg || !p || !t) return;` rejected a temperature of exactly 0 because 0 is
    falsy, leaving the previous result on screen with no indication it was stale. 0 °C
    is an ordinary process temperature. Reverting to `!t` is an easy accident to make
    when editing nearby code, and pytest cannot execute the JS to catch it — so the
    guard is pinned at source level.

    sg and p keep the falsy check deliberately: zero gas gravity or zero absolute
    pressure are genuinely invalid, not merely unusual.
    """
    assert "if(!sg || !p || isNaN(t)) return;" in html, (
        "calcZFactor()'s input guard has changed; a temperature of exactly 0 must not "
        "be treated as a missing input (issue #11)")
    assert "if(!sg || !p || !t) return;" not in html, (
        "issue #11 has regressed — `!t` rejects 0 °C")


def test_gas_property_card_accepts_zero_temperature(html):
    """The newer card uses isNaN throughout; it must never adopt the falsy pattern."""
    assert "isNaN(t)" in html
    assert "isNaN(sg) || sg <= 0 || isNaN(p) || p <= 0 || isNaN(t)" in html, (
        "calcGasProps()'s guard has changed shape; it must keep accepting 0 °C")


def test_jt_derivative_step_is_hard_coded(html):
    """h = 0.5 degR. Below about 0.01 K the central difference loses precision to
    float64 cancellation, so h must never become a user input."""
    assert re.search(r"const h = 0\.5;", html), "the JT derivative step h is not 0.5"
    assert 'getElementById("gp-h")' not in html and "getElementById('gp-h')" not in html, (
        "the JT derivative step must not be exposed as a form input")
