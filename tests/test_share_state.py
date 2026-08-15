"""Source-level guards on the v2.8 share-state format and its import sanitizer.

pytest cannot execute the JavaScript, so these cannot prove the sanitizer works — that is
verified by driving hostile payloads through the real functions in a browser engine (see
the PR description and docs/SPECIFICATION.md §6). What these DO protect is the set of
invariants that are easy to break by accident while editing nearby code, and whose failure
is silent:

  * `createCard()` interpolates module text into innerHTML and the module id into two
    inline onclick attributes. That is safe only while every externally-supplied module
    passes through `sanitizeSharedModule()` first. A second import path that skips it
    would reintroduce stored XSS via URL.
  * `applyState()` has no try/catch, so an unguarded `.forEach` on a v1 payload's absent
    `mods` would throw and kill the entire session restore.
  * The top-level `savedModules` parse must stay guarded, or corrupt storage takes out
    every function declared after it.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def html():
    return (REPO_ROOT / "index.html").read_text(encoding="utf-8")


# ── The sanitizer must exist and be the only door in ─────────────────────────────

def test_sanitizer_and_import_helpers_exist(html):
    for fn in ("function escModText(", "function sanitizeSharedModule(",
               "function importSharedModules("):
        assert fn in html, f"missing {fn!r} — the share-import sanitizer has been removed"


def test_import_path_goes_through_the_sanitizer(html):
    """importSharedModules() must call sanitizeSharedModule() and must not call
    createCard() with anything else."""
    body = re.search(r"function importSharedModules\(shared\) \{(.*?)\n    \}",
                     html, re.S)
    assert body, "could not isolate importSharedModules()"
    src = body.group(1)
    assert "sanitizeSharedModule(" in src
    # The only createCard() call in this function must be on the sanitized object.
    assert re.search(r"createCard\(m\)", src), "createCard must be called with the sanitized module"
    assert "createCard(raw" not in src, "createCard must never receive the raw payload"


def test_sanitizer_escapes_every_html_metacharacter(html):
    """& < > \" ' all matter: the first three for innerHTML, the last two because the
    module id and text reach inline onclick attribute strings."""
    esc = re.search(r"function escModText\(v\) \{(.*?)\n    \}", html, re.S)
    assert esc, "could not isolate escModText()"
    src = esc.group(1)
    for ch, ent in [("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"),
                    ('"', "&quot;"), ("'", "&#39;")]:
        assert ent in src, f"escModText does not escape {ch!r} to {ent}"
    assert ".trim()" in src, (
        "escModText must trim before slicing — a whitespace-only title is otherwise "
        "truthy and creates a blank, unidentifiable card")


def test_module_ids_are_regenerated_on_import(html):
    """Ids are `mod-${Date.now()}`, unique per user but NOT globally. A shared module can
    collide with one the recipient already has, which would give duplicate DOM ids, make
    getElementById inside createCard grab the wrong node, and make TERMINATE delete both."""
    body = re.search(r"function sanitizeSharedModule\(raw, index\) \{(.*?)\n    \}",
                     html, re.S)
    assert body, "could not isolate sanitizeSharedModule()"
    src = body.group(1)
    assert "id: `mod-${Date.now()}-s${index}`" in src, (
        "the imported module id must be regenerated, never taken from the payload")
    assert "raw.id" not in src, "sanitizeSharedModule must not trust raw.id"


def test_sanitizer_rejects_unusable_factors(html):
    body = re.search(r"function sanitizeSharedModule\(raw, index\) \{(.*?)\n    \}",
                     html, re.S).group(1)
    assert "isFinite(factor)" in body and "factor === 0" in body, (
        "a non-finite or zero factor must be rejected — zero would divide by zero on the "
        "reverse conversion")


def test_import_is_capped(html):
    assert "MOD_MAX_SHARED" in html and "MOD_MAX_TEXT_LEN" in html
    assert re.search(r"slice\(0, MOD_MAX_SHARED\)", html), (
        "the number of modules a single link may import must be capped")


# ── Version guard and backward compatibility ─────────────────────────────────────

def test_state_version_is_2(html):
    assert re.search(r"return \{ v: 2, inputs: collectInputs\(\)", html), (
        "collectState() must emit v:2 now that it carries module definitions")


def test_mods_guard_uses_array_isarray(html):
    """`applyState()` has no try/catch. An unguarded `.forEach` on a v1 payload — which
    has no `mods` at all — would throw and silently kill the whole restore."""
    body = re.search(r"function importSharedModules\(shared\) \{(.*?)\n    \}",
                     html, re.S).group(1)
    assert "Array.isArray(shared.mods)" in body, (
        "guard on mods must be Array.isArray, not truthiness")


def test_shared_module_input_keys_are_remapped(html):
    """Because the id is regenerated, the sender's `mod-<id>-in1/-in2` value keys must be
    remapped or the imported card's numbers land nowhere."""
    body = re.search(r"function importSharedModules\(shared\) \{(.*?)\n    \}",
                     html, re.S).group(1)
    assert "'in1', 'in2'" in body or '"in1", "in2"' in body
    assert "delete shared.inputs[from]" in body, "the stale sender key must be removed"


def test_import_runs_before_apply_state_in_boot(html):
    """applyInputs() can only fill inputs that already exist in the DOM, so shared modules
    must be materialized after decodeShareState() but before applyState()."""
    boot = re.search(r"window\.addEventListener\('DOMContentLoaded'.*?\n    \}\);",
                     html, re.S)
    assert boot, "could not isolate the DOMContentLoaded handler"
    src = boot.group(0)
    i_decode = src.index("decodeShareState()")
    i_import = src.index("importSharedModules(shared)")
    i_apply = src.index("applyState(stored")
    assert i_decode < i_import < i_apply, (
        "boot order must be decodeShareState -> importSharedModules -> applyState")


# ── Bundled hardening ────────────────────────────────────────────────────────────

def test_saved_modules_parse_is_guarded(html):
    """This sits at the top level of the script: an unparseable value used to throw and
    leave every function declared below it undefined."""
    assert "let savedModules = JSON.parse(" not in html, (
        "the og_custom_modules parse must be wrapped in try/catch")
    block = re.search(r"let savedModules = \[\];\s*try \{(.*?)\} catch", html, re.S)
    assert block, "savedModules must be initialised to [] and parsed inside try/catch"
    assert "Array.isArray(raw)" in block.group(1), (
        "a non-array stored value must be rejected, not assigned")


def test_report_fields_are_excluded_from_state(html):
    """The bug-report form lives inside <main>, so its free text was being base64'd into
    every share link and written to localStorage."""
    body = re.search(r"function collectInputs\(\) \{(.*?)\n    \}", html, re.S).group(1)
    assert "el.id.indexOf('report-') === 0" in body, (
        "collectInputs must skip report-* ids")


def test_share_link_length_warning_exists(html):
    assert "SHARE_URL_WARN_LEN" in html
    assert "common.shareLinkCopiedLong" in html, (
        "an over-long share link must say so — several chat and mail clients truncate "
        "around 2,000 characters, producing a link that silently restores nothing")


# ── v3.4: the query-string fallback, and the privacy asymmetry it must preserve ──

def test_decode_accepts_both_fragment_and_query(html):
    """LinkedIn strips everything after '#' when it auto-links a URL, so a posted share link
    restores nothing when clicked. decodeShareState() therefore also reads '?s='."""
    block = _decode_share_state_body(html)
    assert "location.hash" in block, "the fragment form must keep working"
    assert "location.search" in block, (
        "decodeShareState() no longer reads location.search — posted share links are silently "
        "back to restoring nothing when clicked")
    assert "[#?&]s=" in block, "the capture regex must accept the '?' separator"


def test_fragment_takes_precedence_over_query(html):
    """The fragment is the form this app emits, so a stray '?s=' left on the URL by a redirect
    must never override what the user actually pasted."""
    block = _decode_share_state_body(html)
    hash_at = block.index("location.hash")
    search_at = block.index("location.search")
    assert hash_at < search_at, (
        "location.hash must be read before location.search, or the precedence rule documented "
        "in SPECIFICATION 6 is reversed")


def test_share_button_still_emits_a_fragment_not_a_query(html):
    """THE PRIVACY INVARIANT. A fragment is never sent to the server; a query string travels in
    the request line and lands in access logs. The app reads '?s=' as a courtesy to links it did
    not build, but it must never GENERATE one — that would put every user's engineering inputs
    into server logs, contradicting the Privacy Policy and the 'never what was entered' boundary
    that CLAUDE.md holds analytics to."""
    start = html.index("function copyShareLink()")
    end = html.index("function ", start + 10)
    body = html[start:end]
    assert "'#s=' + enc" in body, "copyShareLink() must emit the fragment form"
    assert "?s=" not in body, (
        "copyShareLink() now emits a query string — that leaks the shared state into server "
        "request logs. Read '?s=', never write it.")


def test_base64_normalizer_undoes_transit_manglings(html):
    """'+', '/' and '=' all mean something in a URL, so rewriters mangle them. Each mangling
    produces a payload atob() rejects, and the only symptom is a link that restores nothing."""
    assert "function normalizeShareB64(" in html
    start = html.index("function normalizeShareB64(")
    body = html[start:html.index("\n    }", start)]
    assert "decodeURIComponent" in body, "percent-encoded payloads must be decoded"
    assert r"replace(/ /g, '+')" in body, (
        "'+' becomes a literal space in a query string; that must be undone or atob() throws")
    assert r"replace(/-/g, '+')" in body and r"replace(/_/g, '/')" in body, (
        "base64url payloads must be accepted")


def _decode_share_state_body(html):
    start = html.index("function decodeShareState()")
    return html[start:html.index("\n    }", start)]
