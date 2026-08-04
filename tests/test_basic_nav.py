"""Basic Eng quick-links strip (v3.0) — anchor integrity.

Nine cards, nine pills: every link must resolve to a real card anchor, and the
anchors must keep their sticky-header clearance. The i18n parity suite already
guarantees the basic.nav.* labels exist in all 10 dictionaries.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

CARDS = ["basic-pipe", "basic-z", "basic-api", "basic-visc", "basic-mf",
         "basic-gp", "basic-steam", "basic-npsh", "basic-cmp"]


@pytest.fixture(scope="module")
def html():
    return (REPO_ROOT / "index.html").read_text(encoding="utf-8")


def test_every_pill_resolves_to_an_anchored_card(html):
    nav = re.search(r'<nav data-i18n-aria="basic\.nav\.aria".*?</nav>', html, re.DOTALL)
    assert nav, "Basic Eng quick-links strip missing"
    hrefs = re.findall(r'href="#([^"]+)"', nav.group(0))
    assert hrefs == CARDS, f"pill order/targets drifted: {hrefs}"
    for cid in CARDS:
        m = re.search(r'<div id="' + cid + r'" class="([^"]*)"', html)
        assert m, f"card anchor {cid} missing"
        assert "scroll-mt-64 md:scroll-mt-40" in m.group(1), (
            f"{cid} lost its sticky-header clearance (header measures 226 px at "
            "mobile width, 134 px at desktop — see the nav strip comment)")


def test_every_pill_is_translated(html):
    nav = re.search(r'<nav data-i18n-aria="basic\.nav\.aria".*?</nav>', html, re.DOTALL)
    keys = re.findall(r'data-i18n="(basic\.nav\.[a-z]+)"', nav.group(0))
    assert len(keys) == 9 and len(set(keys)) == 9
