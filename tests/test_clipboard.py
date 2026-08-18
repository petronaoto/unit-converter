"""Unit-aware clipboard (v3.0) — source-level guards.

The mechanism is pure client-side DOM behavior, so pytest pins its structure:
every static data-unit-src must resolve to a real element id, the site census
must match the audited survey (19 dynamic-unit + 4 literal-unit + 2 template
sites; the 8 dimensionless outputs carry no attribute BY DESIGN), plain-click
behavior must remain the bare value, and the createCard() template must keep
user-supplied unit TEXT out of attribute context (the v2.8 XSS contract).
The click/long-press behavior itself is verified by hand in a browser.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def html():
    return (REPO_ROOT / "index.html").read_text(encoding="utf-8")


def test_every_static_unit_src_resolves(html):
    ok_ids = set(re.findall(r'id="([^"]+)"', html))
    for src in re.findall(r'data-unit-src="([^"]+)"', html):
        if "${" in src:
            continue  # createCard template — ids are assigned at runtime
        for ref in src.split(" "):
            assert ref in ok_ids, f"data-unit-src references missing id {ref!r}"


def test_site_census(html):
    """22 static dynamic-unit sites + 2 template sites; 5 literal-unit sites.
    If this fails after adding a card, extend the survey deliberately — do not
    just bump the number. v3.1 added 2 static (gt-out-vol-u, gt-out-mass-u) and
    2 literal ("MW" on gt-out-q, "kJ/kWh" on gt-out-hr) on the GT Fuel tab.
    v3.5 moved gt-out-q from the literal "MW" to a unit-aware select
    (gt-out-q-u: MW-th / MMBtu/h / GJ/h) — one literal site became one static
    site, so 21+1 static and 6-1 literal. v3.5 also added the LNG Cargo card:
    4 static (mass, gas, HHV energy and LHV energy — the LHV row shares the
    lc-out-e-u select) and 1 literal ("m³" on the liquid volume), so 26 / 6."""
    srcs = re.findall(r'data-unit-src="([^"]+)"', html)
    assert len([s for s in srcs if "${" not in s]) == 26
    assert len([s for s in srcs if "${" in s]) == 2
    assert len(re.findall(r'data-copy-unit="([^"]+)"', html)) == 6
    assert 'data-unit-src="gt-out-q-u"' in html
    assert srcs.count('data-unit-src="lc-out-e-u"'.split('"')[1]) == 2, "HHV and LHV rows both key off lc-out-e-u"
    # the two mode-dependent flow outputs use the visible-select fallback list
    assert 'data-unit-src="flow-vol-out-u flow-mol-out-u"' in html
    assert 'data-unit-src="flow-mass-out-u flow-mol-out2-u"' in html


def test_dimensionless_sites_carry_no_unit_attribute(html):
    """Z, SG, WI, MCP, the orifice letter and the (already-unit-bearing) orifice
    area must NOT gain a unit attribute — modifier-click stays a plain copy."""
    for target in ("z-result", "api-sg", "gp-out-z", "out-sg", "out-wi",
                   "out-mcp", "psv-out-orifice'", "psv-out-orifice-area"):
        m = re.search(r'<button onclick="copyText\([^"]*' + re.escape(target) + r'[^"]*"[^>]*>', html)
        assert m, f"copy button for {target} not found"
        assert "data-unit-src" not in m.group(0) and "data-copy-unit" not in m.group(0), target


def test_plain_click_still_copies_bare_value(html):
    """The pre-v3.0 contract survives verbatim: no text -> no copy, and the
    unit is appended ONLY under the wantUnit flag."""
    body = html[html.index("function copyText"):]
    body = body[:body.index("function copyToClipboard")]
    assert "if (!text) return;" in body
    assert "let out = String(text);" in body
    assert "btnElement._lpUnit || _copyModClick" in body
    assert "tr('common.copiedWithUnit'" in body


def test_delegation_and_long_press_source_guards(html):
    assert "function copyUnitOf(" in html
    # modifier state comes from a capture-phase listener so the 30+ inline
    # onclick attributes stay untouched
    assert re.search(r"document\.addEventListener\('click', e => \{\s*"
                     r"_copyModClick = !!\(e\.ctrlKey \|\| e\.metaKey \|\| e\.shiftKey\);\s*"
                     r"\}, true\);", html)
    assert "const COPY_BTN_SEL = 'button[onclick*=\"copyText\"], button[onclick*=\"copyToClipboard\"]';" in html
    assert "e.pointerType === 'mouse'" in html          # long-press is touch/pen only
    assert re.search(r"_lpTimer = setTimeout\(\(\) => \{", html)
    assert "}, 500);" in html                            # the long-press threshold
    assert "btn._lpDone = true;" in html                 # swallow the follow-up click
    assert "document.addEventListener('contextmenu'" in html


def test_createcard_keeps_unit_text_out_of_attributes(html):
    """Only the sanitized module id may enter an attribute; the unit text stays
    in element text content. ${m.u1}/${m.u2} appearing inside any attribute
    would reopen the share-link injection surface closed in v2.8."""
    card = html[html.index("function createCard"):]
    card = card[:card.index("function", 20)]
    assert 'data-unit-src="${m.id}-u1"' in card and 'data-unit-src="${m.id}-u2"' in card
    for attr_hit in re.findall(r'[a-zA-Z-]+="[^"]*\$\{m\.u[12]\}[^"]*"', card):
        assert attr_hit.startswith('class="'), (
            f"user-supplied unit text found in attribute context: {attr_hit}")
    assert card.count("${m.u1}") >= 1 and card.count("${m.u2}") >= 1
    # runtime id assignment for the unit spans
    assert "c.querySelector('.u1').id" in card and "c.querySelector('.u2').id" in card


def test_toast_key_exists_in_english_dictionary():
    import json
    en = json.loads((REPO_ROOT / "i18n" / "en.json").read_text(encoding="utf-8"))
    assert "{text}" in en["common"]["copiedWithUnit"]
