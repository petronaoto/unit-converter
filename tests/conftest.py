"""Shared fixtures for the reference-value regression suite (v2.8).

Two jobs:

1. Import the three `api/*.py` endpoints as plain modules. They are Vercel serverless
   functions, not a package — there is no `__init__.py` and there must not be one, so
   they are loaded by file path via importlib.

2. Provide `post_to_handler`, which drives a `BaseHTTPRequestHandler` subclass's
   `do_POST` without a socket.

   Why this exists: `api/psv_calculator.py` and `api/flowregime.py` keep their math in
   module-level pure functions (`size_gas(...)`, `compute(...)`) and can be called
   directly. `api/dp_calculator.py` does NOT — all of its physics lives inline inside
   `handler.do_POST`, interleaved with `self.send_response()` / `self.wfile.write()`.

   Adding a `compute()` function to dp_calculator.py purely for testability would be a
   refactor of working, deployed code, which CLAUDE.md preservation rules 1-3 forbid
   without explicit instruction. This harness makes that refactor unnecessary: the
   endpoint is tested exactly as it is deployed, through its real HTTP entry point.

   The trick is `handler.__new__(cls)` to construct the instance WITHOUT running
   `BaseHTTPRequestHandler.__init__`, which would otherwise try to set up a socket and
   immediately call `handle()`. The response plumbing is then stubbed out and the JSON
   body is captured from a `BytesIO` standing in for `wfile`.

   This deliberately couples to stdlib internals rather than a public API. It is kept in
   this one place so that a future Python release breaking it is a one-line fix here
   rather than a change scattered across the test files.
"""

import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
API_DIR = REPO_ROOT / "api"


def _load(module_name, filename):
    """Load an api/*.py endpoint as a module, by path."""
    path = API_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"expected endpoint at {path}")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="session")
def dp_module():
    return _load("_og_dp_calculator", "dp_calculator.py")


@pytest.fixture(scope="session")
def psv_module():
    return _load("_og_psv_calculator", "psv_calculator.py")


@pytest.fixture(scope="session")
def flowregime_module():
    # Imports numpy/matplotlib/seaborn at module scope, so CI must install
    # requirements.txt for this one. dp and psv need no install at all.
    return _load("_og_flowregime", "flowregime.py")


@pytest.fixture(scope="session")
def post_to_handler():
    """Return f(module, payload) -> (status, decoded_json_body).

    Drives `module.handler.do_POST` with a fake request. See the module docstring for
    why this is preferable to refactoring the endpoint.
    """

    def _post(module, payload):
        body = json.dumps(payload).encode("utf-8")

        # Bypass BaseHTTPRequestHandler.__init__ — it would attempt socket setup.
        inst = module.handler.__new__(module.handler)

        captured = {"status": None}
        inst.headers = {"Content-Length": str(len(body))}
        inst.rfile = io.BytesIO(body)
        inst.wfile = io.BytesIO()
        inst.send_response = lambda code, *a, **kw: captured.__setitem__("status", code)
        inst.send_header = lambda *a, **kw: None
        inst.end_headers = lambda *a, **kw: None

        inst.do_POST()

        raw = inst.wfile.getvalue()
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            # flowregime returns a PNG on the success path; callers that hit it
            # should be testing compute() directly instead.
            decoded = raw
        return captured["status"], decoded

    return _post


# ── The v2.3 default ΔP inputs, pinned in api/CLAUDE.md ──────────────────────────
# ID = 4 in, L = 100 m, Δz = 70.711 m, vapor 150 kg/h @ 10 kg/m³ / 0.012 cP,
# liquid 7,300 kg/h @ 500 kg/m³ / 0.12 cP. Every *_mult / *_m value below is a
# multiply-to-SI factor, matching the option values the frontend actually sends.
DP_REFERENCE_PAYLOAD = {
    "scale": 1,
    "id": 4, "id_mult": 0.0254,
    "len": 100, "len_mult": 1,
    "rough": 0.045, "rough_mult": 0.001,
    "elev": 70.711, "elev_mult": 1,
    "v_flow": 150, "v_flow_m": 0.000277778,
    "v_den": 10, "v_den_m": 1,
    "v_visc": 0.012, "v_visc_m": 0.001,
    "l_flow": 7300, "l_flow_m": 0.000277778,
    "l_den": 500, "l_den_m": 1,
    "l_visc": 0.12, "l_visc_m": 0.001,
    "cfactor": 100,
}


@pytest.fixture
def dp_reference_payload():
    return dict(DP_REFERENCE_PAYLOAD)
