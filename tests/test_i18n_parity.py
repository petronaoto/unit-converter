"""Key-parity checks across the 10 i18n dictionaries. Pure standard library.

This is the cheapest and highest-value test in the suite. Missing translation keys fail
*silently* at runtime — `tr()` falls back to `en.json` and then to rendering the raw
dot-path, and `data-i18n-html` falls back to the inline English cached in
`i18nHtmlOriginals`. Nothing errors, so a dictionary that got skipped during a feature
commit stays broken until a user in that language notices.

The asymmetry these tests encode, which is deliberate and documented in CLAUDE.md:

  * `en.json` carries the 368 working-tool keys and NO `docs` key at all — English
    documentation prose lives inline in index.html and is cached at runtime.
  * The 9 non-English files carry those same working-tool keys PLUS the `docs.*` block.

So parity is asserted on the working-tool keys for all 10 files, and separately on the
`docs.*` keys for the 9 non-English files.
"""

import json
import re
from pathlib import Path

import pytest

I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"
INDEX_HTML = Path(__file__).resolve().parent.parent / "index.html"

# Kept explicit rather than globbed: if a language file goes missing, that should fail
# the suite, not silently shrink its scope.
LANGUAGES = ["en", "ja", "zh", "ko", "th", "id", "ru", "es", "fr", "de"]
NON_ENGLISH = [c for c in LANGUAGES if c != "en"]


def _flatten(obj, prefix=""):
    """{'a': {'b': 1}} -> {'a.b'}"""
    keys = set()
    for key, value in obj.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            keys |= _flatten(value, path + ".")
        else:
            keys.add(path)
    return keys


def _load(code):
    with open(I18N_DIR / f"{code}.json", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def dictionaries():
    return {code: _load(code) for code in LANGUAGES}


@pytest.fixture(scope="module")
def flat_keys(dictionaries):
    return {code: _flatten(data) for code, data in dictionaries.items()}


@pytest.fixture(scope="module")
def html_source():
    return INDEX_HTML.read_text(encoding="utf-8")


# ── File presence and shape ──────────────────────────────────────────────────────

def test_all_ten_dictionaries_exist():
    missing = [c for c in LANGUAGES if not (I18N_DIR / f"{c}.json").is_file()]
    assert not missing, f"missing dictionaries: {missing}"


def test_english_deliberately_has_no_docs_block(dictionaries):
    """English documentation prose lives inline in index.html, not in en.json.
    Adding a `docs` key here would create a second source of truth for it."""
    assert "docs" not in dictionaries["en"]


def test_every_non_english_dictionary_has_a_docs_block(dictionaries):
    for code in NON_ENGLISH:
        assert "docs" in dictionaries[code], f"{code}.json has no docs block"


# ── Working-tool key parity ──────────────────────────────────────────────────────

@pytest.mark.parametrize("code", NON_ENGLISH)
def test_working_tool_keys_match_english_exactly(code, flat_keys):
    """Every non-English dictionary must carry exactly the same working-tool keys as
    en.json — no missing keys (silent English fallback) and no orphans (dead weight
    that usually means a key was renamed in en.json but not here)."""
    english = flat_keys["en"]
    other = {k for k in flat_keys[code] if not k.startswith("docs.")}

    missing = sorted(english - other)
    orphaned = sorted(other - english)

    assert not missing, f"{code}.json is missing {len(missing)} key(s): {missing[:12]}"
    assert not orphaned, f"{code}.json has {len(orphaned)} orphan key(s): {orphaned[:12]}"


# ── docs.* key parity ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("code", NON_ENGLISH)
def test_docs_keys_match_across_non_english_dictionaries(code, flat_keys):
    """The docs.* block must be identical across all 9 translated files. ja.json is the
    comparison baseline only because it shipped first; any of the 9 would do."""
    baseline = {k for k in flat_keys["ja"] if k.startswith("docs.")}
    other = {k for k in flat_keys[code] if k.startswith("docs.")}

    missing = sorted(baseline - other)
    extra = sorted(other - baseline)

    assert not missing, f"{code}.json missing docs keys: {missing[:12]}"
    assert not extra, f"{code}.json has extra docs keys: {extra[:12]}"


# ── index.html <-> dictionary agreement ──────────────────────────────────────────

# -label was added in v3.3 for <optgroup> labels, which cannot use plain data-i18n:
# that sets textContent, which on an optgroup would delete its <option> children.
ATTR_PATTERN = re.compile(
    r'data-i18n(?:-title|-aria|-placeholder|-label)?=["\']([^"\']+)["\']')
HTML_ATTR_PATTERN = re.compile(r'data-i18n-html=["\']([^"\']+)["\']')


def test_every_data_i18n_attribute_resolves_in_english(html_source, flat_keys):
    """Every data-i18n / -title / -aria / -placeholder key must exist in en.json.
    A key that does not resolve renders as its own raw dot-path in the UI."""
    referenced = set(ATTR_PATTERN.findall(html_source))
    referenced -= set(HTML_ATTR_PATTERN.findall(html_source))  # those live in docs.*

    unresolved = sorted(referenced - flat_keys["en"])
    assert not unresolved, f"data-i18n keys absent from en.json: {unresolved}"


def test_every_data_i18n_html_key_resolves_in_the_translated_dictionaries(html_source,
                                                                          flat_keys):
    """Every data-i18n-html block key must exist in all 9 non-English dictionaries.
    (Keys must NOT exist in en.json — English is the inline HTML itself.)

    v2.8.1 closed the temporary PENDING_TRANSLATION exemption that covered the 14
    v2.8 doc blocks; there is no allowlist any more — new documentation ships
    translated in the same commit, or this test fails."""
    referenced = set(HTML_ATTR_PATTERN.findall(html_source))
    assert referenced, "expected data-i18n-html blocks in index.html; found none"

    for code in NON_ENGLISH:
        unresolved = sorted(referenced - flat_keys[code])
        assert not unresolved, f"{code}.json missing doc blocks: {unresolved[:12]}"


TR_CALL_PATTERN = re.compile(r"""\btr\(\s*['"]([A-Za-z0-9_.]+)['"]""")


def test_every_tr_call_resolves_in_english(html_source, flat_keys):
    """Every literal key passed to tr() must exist in en.json.

    This is the direction that matters when ADDING code: a typo'd or forgotten key in a
    new tr() call renders its own raw dot-path in the UI (e.g. "basic.gasProps.warnLge"),
    in every language at once, and nothing errors. The reverse direction is covered by
    test_no_english_key_is_dead.

    Keys assembled dynamically (tr('advanced.deltaP.re' + suffix)) are not matched by
    this regex and are not expected to be — those are covered by the dead-key test from
    the other side.
    """
    called = set(TR_CALL_PATTERN.findall(html_source))
    assert called, "expected tr() calls in index.html; found none — has tr() been renamed?"

    unresolved = sorted(called - flat_keys["en"])
    assert not unresolved, f"tr() keys absent from en.json: {unresolved}"


def test_no_english_key_is_dead(html_source, flat_keys):
    """Every key in en.json should be reachable — either from a data-i18n attribute or
    from a tr('...') call. Keys reached only through a ternary are matched by the
    substring scan, which is why this looks for the quoted key anywhere in the file
    rather than for a literal tr('key') call."""
    dead = [key for key in sorted(flat_keys["en"])
            if f"'{key}'" not in html_source and f'"{key}"' not in html_source]
    assert not dead, f"en.json keys never referenced by index.html: {dead}"


# ── Placeholder consistency ──────────────────────────────────────────────────────

PLACEHOLDER = re.compile(r"\{(\w+)\}")


def _placeholders(value):
    return set(PLACEHOLDER.findall(value)) if isinstance(value, str) else set()


def _leaf(data, path):
    node = data
    for part in path.split("."):
        node = node[part]
    return node


@pytest.mark.parametrize("code", NON_ENGLISH)
def test_interpolation_placeholders_survive_translation(code, dictionaries, flat_keys):
    """tr() does literal {token} replacement — it is not ICU. A translator who drops or
    renames a placeholder produces a string with a visible raw `{pr}` in it, or silently
    loses the value. Both are invisible until someone reads that language's UI."""
    english = dictionaries["en"]
    other = dictionaries[code]

    mismatches = []
    for key in sorted(flat_keys["en"]):
        expected = _placeholders(_leaf(english, key))
        if not expected:
            continue
        actual = _placeholders(_leaf(other, key))
        if expected != actual:
            mismatches.append(f"{key}: en={sorted(expected)} {code}={sorted(actual)}")

    assert not mismatches, f"placeholder drift in {code}.json:\n  " + "\n  ".join(mismatches)


# ── Number formatting (SPECIFICATION.md §12: en-US in every language) ────────────

NUMERIC_TOKEN = re.compile(r"\d+[.,]\d+")


@pytest.mark.parametrize("code", NON_ENGLISH)
def test_numeric_tokens_are_en_us_in_every_language(code, dictionaries, flat_keys):
    """Numbers stay en-US (decimal point, comma thousands) in all 10 dictionaries.

    This is not cosmetic. `fmtN` and `toFixed()` emit en-US regardless of UI language, so
    a dictionary written with locale separators puts two conventions in one sentence. The
    v2.8 `basic.gasProps.warnPapay` string did exactly that: the live Pr/Tr values arrive
    as "16.20" from `toFixed(2)` while the literal envelope read "1,05 ≤ Tr ≤ 3,0" — and
    the Z-Factor card beside it stated the same envelope with dots.

    Any numeric token appearing in a translation must also appear in the English source
    for that key. Translations may drop a number, but may not invent a differently
    formatted one.
    """
    english = dictionaries["en"]
    other = dictionaries[code]

    offenders = []
    for key in sorted(flat_keys["en"]):
        en_tokens = set(NUMERIC_TOKEN.findall(str(_leaf(english, key))))
        tokens = set(NUMERIC_TOKEN.findall(str(_leaf(other, key))))
        invented = tokens - en_tokens
        if invented:
            offenders.append(f"{key}: {sorted(invented)} not in en {sorted(en_tokens)}")

    assert not offenders, (
        f"{code}.json uses non-en-US number formatting:\n  " + "\n  ".join(offenders))


# ── Version-string consistency (CLAUDE.md version-bump checklist) ────────────────

# Matches "V3.2", "v3.2" AND the spelled-out "Version 3.2" / "バージョン 3.2" / "Versión 3.2"
# forms. Widened in v3.2: the original `[Vv](\d+\.\d+...)` required a digit immediately after
# the V, so it never matched ANY of the ten `footer.copyright` values — every one of which is
# "… • Version 3.1" or its translation. The key was listed in the loop below and in this
# docstring, but contributed nothing, and a bump that updated pageTitle and mailtoBody while
# leaving all ten footers behind passed cleanly. The trailing `(?![\d.])` stops "3.1" from
# matching inside "3.10".
VERSION = re.compile(r"(?:[Vv]|[Vv]ers[iãóé]?[oóõe]?n?|バージョン|版本|버전|เวอร์ชัน|Versi)\s*(\d+\.\d+(?:\.\d+)?)(?![\d.])")


def test_version_strings_agree_across_all_dictionaries(dictionaries):
    """CLAUDE.md's version-bump checklist exists because v2.6 shipped displaying
    "Version 2.5" in three places. The version is duplicated into meta.pageTitle,
    footer.copyright and report.mailtoBody in every one of the 10 files — this catches a
    bump that missed a file."""
    seen = {}
    for code, data in dictionaries.items():
        for path in ("meta.pageTitle", "footer.copyright", "report.mailtoBody"):
            found = VERSION.findall(_leaf(data, path))
            # Non-vacuity: a key that yields no match is a silent hole in this test, which is
            # exactly how the footers drifted. Every one of these three carries a version.
            assert found, f"{code}:{path} contains no recognisable version string"
            for version in found:
                seen.setdefault(version, []).append(f"{code}:{path}")

    assert len(seen) == 1, (
        "inconsistent version strings across dictionaries: "
        + json.dumps({k: v for k, v in seen.items()}, indent=2))
