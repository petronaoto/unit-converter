"""Guards on the architectural constraints in CLAUDE.md and api/CLAUDE.md.

These rules are currently enforced only by a human remembering them. They are cheap to
check mechanically, and each one has a real production consequence if it slips:

  * A non-stdlib import in dp_calculator.py or psv_calculator.py would need a
    requirements.txt entry to deploy, growing the cold-start of two endpoints that are
    deliberately dependency-free.
  * pytest leaking into requirements.txt would install a test framework into the Vercel
    production runtime.
  * The frontend having a build step would break the single-file, no-build principle.
"""

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
API_DIR = REPO_ROOT / "api"

STDLIB_ONLY_ENDPOINTS = ["dp_calculator.py", "psv_calculator.py"]


def _top_level_imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                modules.add(node.module.split(".")[0])
    return modules


@pytest.mark.parametrize("filename", STDLIB_ONLY_ENDPOINTS)
def test_endpoint_imports_only_the_standard_library(filename):
    """api/CLAUDE.md: "dp_calculator.py and psv_calculator.py use only the Python
    standard library (json, math, http.server) — do not add dependencies to them."."""
    imported = _top_level_imports(API_DIR / filename)
    non_stdlib = sorted(imported - set(sys.stdlib_module_names))
    assert not non_stdlib, (
        f"{filename} imports non-stdlib module(s) {non_stdlib}. "
        "That endpoint is required to stay dependency-free — see api/CLAUDE.md.")


def test_flowregime_declares_all_of_its_third_party_imports():
    """flowregime.py is the one endpoint allowed dependencies, but every one of them
    must appear in requirements.txt or the deployment breaks at import time."""
    imported = _top_level_imports(API_DIR / "flowregime.py")
    third_party = imported - set(sys.stdlib_module_names)

    declared = set()
    for line in (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            declared.add(line.split(">=")[0].split("==")[0].split("[")[0].strip().lower())

    undeclared = sorted(m for m in third_party if m.lower() not in declared)
    assert not undeclared, (
        f"flowregime.py imports {undeclared}, absent from requirements.txt")


def test_pytest_never_leaks_into_production_requirements():
    """requirements.txt is installed into the Vercel serverless runtime. Dev tooling
    belongs in requirements-dev.txt."""
    production = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for banned in ("pytest", "coverage", "ruff", "black", "mypy", "flake8"):
        assert banned not in production, (
            f"{banned!r} found in requirements.txt — move it to requirements-dev.txt")


def test_requirements_dev_exists_and_is_separate():
    dev = REPO_ROOT / "requirements-dev.txt"
    assert dev.is_file(), "requirements-dev.txt is missing"
    assert "pytest" in dev.read_text(encoding="utf-8").lower()


def test_frontend_has_no_build_step():
    """CLAUDE.md architecture principle 2: index.html contains all markup, styling and
    JavaScript. No bundler, no framework, no node_modules."""
    for artifact in ("package.json", "package-lock.json", "webpack.config.js",
                     "vite.config.js", "rollup.config.js", "tsconfig.json"):
        assert not (REPO_ROOT / artifact).exists(), (
            f"{artifact} found — the frontend is required to stay build-step-free")


def test_index_html_is_a_single_file_with_no_local_script_or_style_imports():
    """External CDN references (Tailwind, Three.js) are expected and allowed; a relative
    src=/href= to a local .js/.css file would mean the single-file principle has broken.

    KNOWN EXCEPTION: `/cdn-cgi/scripts/.../email-decode.min.js` (index.html:2182) is a
    Cloudflare email-obfuscation script that was baked into the file at some point and is
    disclosed in the Privacy Policy tab (index.html:2045). It is allowlisted here rather
    than silently ignored. Worth revisiting separately: the app deploys to Vercel, where
    `/cdn-cgi/` does not exist, and there is no `__cf_email__` span left in the document
    for it to decode — so it is most likely a dead 404 on every page load.
    """
    import re
    html = (REPO_ROOT / "index.html").read_text(encoding="utf-8")
    allowed = {"/cdn-cgi/scripts/5c5dd728/cloudflare-static/email-decode.min.js"}

    local_refs = set(re.findall(
        r'(?:src|href)=["\'](?!https?://|//|#|mailto:|data:)([^"\']+\.(?:js|css))["\']',
        html)) - allowed
    assert not local_refs, f"index.html references local asset files: {sorted(local_refs)}"
