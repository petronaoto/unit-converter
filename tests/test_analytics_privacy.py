"""Source-level guards on the v3.2 Vercel Web Analytics integration.

The whole justification for shipping analytics in an app whose selling point is that it
harvests nothing is a single boundary: **the app may record THAT a calculator was used,
never WHAT was entered into it.** That boundary is not enforced by any runtime mechanism —
it is enforced by the shape of `VA_TOOL_BY_ID_PREFIX` and by a handful of `trackEvent()`
call sites, all of which a future edit could widen in one line without anything failing.

These tests make that one line fail instead. They also keep the disclosure honest: the
Privacy Policy is a dated, versioned legal document published in ten languages, and the
release rule in MARKETING.md §5 is that no measurement ships before the policy discloses
it *in the same release*. A test is the only thing that makes "in the same release"
mechanical rather than remembered.

pytest cannot execute the JavaScript, so runtime behaviour (boot silence, per-visit event
de-duplication) is verified by driving the page in a real browser engine — see
DEVELOPMENT_PLAN.md §7.2. What is checked here is everything visible in the source.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
I18N_DIR = REPO_ROOT / "i18n"

NON_ENGLISH = ["ja", "zh", "ko", "th", "id", "ru", "es", "fr", "de"]


@pytest.fixture(scope="module")
def html():
    return (REPO_ROOT / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def code_only(html):
    """index.html with HTML comments and whole-line JS `//` comments removed.

    Necessary because the analytics block is heavily commented and those comments discuss
    the very strings these tests forbid ("assigns .value directly", "not @vercel/analytics").
    Scanning the raw text would fail on the documentation rather than on the code."""
    stripped = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    return "\n".join(l for l in stripped.splitlines() if not l.lstrip().startswith("//"))


@pytest.fixture(scope="module")
def tool_map(html):
    """The literal body of VA_TOOL_BY_ID_PREFIX, as {id_prefix: tool_slug}."""
    match = re.search(r"const VA_TOOL_BY_ID_PREFIX = \{(.*?)\n    \};", html, re.S)
    assert match, "VA_TOOL_BY_ID_PREFIX not found — was the analytics block renamed or removed?"
    parsed = dict(re.findall(r"'([a-z0-9]+)':\s*'([a-z0-9-]+)'", match.group(1)))
    # Non-vacuity guard. Every assertion built on this fixture is of the form "X is absent"
    # or "every entry satisfies Y" — both of which pass trivially on an empty dict. If the
    # regex above ever stops matching the literal's formatting, this fails loudly instead of
    # silently retiring the privacy tests.
    assert len(parsed) >= 20, f"parsed only {len(parsed)} entries — the extraction regex is stale"
    for expected in ("psv", "dp", "sp", "comp"):
        assert expected in parsed, f"known id prefix {expected!r} missing from the parsed map"
    return parsed


# ── Installation ────────────────────────────────────────────────────────────────

def test_analytics_script_and_queue_stub_are_both_present(html):
    """The stub must exist AND must come first. Without it, any event fired before the
    deferred script finishes loading throws instead of queueing into window.vaq."""
    stub = html.index("window.va = window.va || function ()")
    script = html.index('src="/_vercel/insights/script.js"')
    assert stub < script, "the va() queue stub must be declared before the analytics script tag"


def test_analytics_script_is_deferred(html):
    """A blocking script in <head> would delay first paint on a 300 kB page."""
    assert re.search(r'<script defer src="/_vercel/insights/script\.js">', html)


def test_no_npm_analytics_package_crept_in(code_only):
    """`import { Analytics } from '@vercel/analytics'` is the framework install path. It
    requires a bundler, which this project does not have — see the Vercel dashboard's
    'Get Started' panel, which defaults to the Next.js instructions and does not apply."""
    assert "@vercel/analytics" not in code_only


# ── The privacy boundary ────────────────────────────────────────────────────────

def test_report_tab_is_never_instrumented(tool_map, html):
    """The Report tab is the one place a user types prose — a name, and a free-text bug
    description. v2.8 already excluded it from localStorage and from share links. Adding
    'report' to the id-prefix map would transmit the fact of typing into it; nothing worse
    than that, but the exclusion is a promise made explicitly in Privacy §7 and it costs
    nothing to keep."""
    assert "report" not in tool_map


def test_only_fixed_slugs_are_ever_sent(tool_map):
    """Every value in the map must be a hard-coded slug. If a future edit ever derives an
    event value from element content — `e.target.value`, `.innerText` — that is the exact
    failure this whole test module exists to prevent, and it would most likely appear here
    first, as a non-literal map value."""
    for prefix, slug in tool_map.items():
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug), (prefix, slug)


def test_no_input_value_is_read_in_the_analytics_block(code_only):
    """Guard the trackEvent() call sites themselves: none of them may touch a value."""
    block = code_only[code_only.index("const VA_TOOL_BY_ID_PREFIX"):]
    for forbidden in (".value", ".innerText", ".textContent", "collectInputs", "collectState"):
        assert forbidden not in block, f"analytics block reads {forbidden} — it must send slugs only"


def test_event_names_are_a_closed_set(html):
    """Vercel caps the number of distinct custom event names per project, and an
    accidentally dynamic name (a slug interpolated into the name instead of the data)
    would blow through it and fragment the dashboard."""
    block = html[html.index("VERCEL WEB ANALYTICS — USAGE INSTRUMENTATION"):]
    names = set(re.findall(r"trackEvent\('([^']+)'", block))
    assert names == {"Tool Used", "Calculation", "Tab View", "Language", "Action"}


# ── Disclosure: the policy must match what the code does ────────────────────────

def test_english_policy_no_longer_denies_collecting_analytics(html):
    """These exact phrases were true until v3.2 and are now false. The English policy is
    the authoritative text (see docs.privacy.langNote)."""
    policy = html[html.index('<div id="tab-privacy"'):html.index('<div id="tab-report"')]
    for stale in ("Any usage telemetry or analytics", "7. No Cookies or Tracking"):
        assert stale not in policy, f"stale pre-v3.2 privacy claim still present: {stale!r}"


def test_english_policy_discloses_vercel_web_analytics(html):
    policy = html[html.index('<div id="tab-privacy"'):html.index('<div id="tab-report"')]
    assert "Vercel Web Analytics" in policy


def test_social_preview_no_longer_advertises_no_tracking(html):
    """og:/twitter: descriptions are read by crawlers and unfurlers, which never run the
    i18n pass — so they are a published claim in their own right."""
    head = html[:html.index("</head>")]
    for tag in re.findall(r'<meta [^>]*(?:og:description|twitter:description)[^>]*>', head):
        assert "no tracking" not in tag.lower(), tag


@pytest.mark.parametrize("code", NON_ENGLISH)
def test_every_translated_policy_discloses_the_analytics(code):
    """The release rule (MARKETING.md §5) is that the disclosure ships with the script. A
    translated policy left on the pre-v3.2 text would be an inaccurate legal statement for
    that language's readers, and the i18n key-parity tests cannot see it because the keys
    are all still present — only their contents went stale."""
    with open(I18N_DIR / f"{code}.json", encoding="utf-8") as handle:
        privacy = json.load(handle)["docs"]["privacy"]
    assert "Vercel Web Analytics" in privacy["b009"], f"{code}: §7 does not name the product"
    assert "3.2" in privacy["b002"], f"{code}: policy version was not bumped"
    # §7 must keep pointing at Vercel's own privacy documentation.
    assert "vercel.com/docs/analytics/privacy-policy" in privacy["b009"], code


@pytest.mark.parametrize("code", NON_ENGLISH)
def test_translated_policy_html_is_well_formed(code):
    """b009 was replaced wholesale in nine languages by a script. A dropped closing tag
    would render as raw markup inside the policy, because data-i18n-html injects it
    verbatim."""
    with open(I18N_DIR / f"{code}.json", encoding="utf-8") as handle:
        block = json.load(handle)["docs"]["privacy"]["b009"]
    for tag in ("p", "ul", "li", "h3", "strong", "em", "a"):
        opens = len(re.findall(rf"<{tag}[ >]", block))
        closes = len(re.findall(rf"</{tag}>", block))
        assert opens == closes, f"{code}: <{tag}> {opens} open vs {closes} close"
