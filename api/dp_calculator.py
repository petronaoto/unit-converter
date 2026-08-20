# api/dp_calculator.py
import json
import math
from http.server import BaseHTTPRequestHandler

def get_darcy_friction_factor(Re, rel_roughness):
    if Re < 2300:
        return 64.0 / Re
    f = 0.02
    diff = 1.0
    iter_count = 0
    while diff > 1e-6 and iter_count < 100:
        term = (rel_roughness / 3.7) + (2.51 / (Re * math.sqrt(f)))
        f_new = 1.0 / math.pow(-2.0 * math.log10(term), 2)
        diff = abs(f_new - f)
        f = f_new
        iter_count += 1
    return f


# v3.7 — selectable two-phase frictional-gradient correlations. `tp_method` in the
# payload picks one; an ABSENT tp_method defaults to "hem", which reproduces every
# pre-v3.7 payload and share link bit-for-bit (same load-bearing-default pattern as
# `k_total` and `cfactor`). The method changes ONLY the frictional term: the static
# term stays rho_ns*g*dz on the no-slip (homogeneous) density, dpFittings stays
# k_total*rho_ns*v^2/2, and the reported vel/Re/f remain the homogeneous-mixture
# values that feed the API RP 14E and NORSOK screens. All phase-alone and
# whole-flow-as-one-phase friction factors reuse the app's Colebrook-White function
# at the actual pipe relative roughness (an engineering adaptation — the original
# correlations were fitted with smooth-pipe Blasius-type factors).
TP_METHOD_LABELS = {
    "hem": "HEM",
    "lm": "Lockhart-Martinelli",
    "msh": "Müller-Steinhagen-Heck",
    "friedel": "Friedel",
}


def two_phase_dpdz(method, G, x, D, rr, rhol, rhov, mul, muv, sigma):
    """Frictional pressure gradient [Pa/m] for a two-phase mixture (0 < x < 1).

    Returns (dpdz, extras) where extras carries method-specific diagnostics.
    Raises ValueError with a user-facing message when the method's own validity
    guard fails (only Friedel has one: it needs mu_v < mu_l).
    """
    if method == "lm":
        # Lockhart & Martinelli (1949) with the Chisholm (1967) C constants.
        # Each phase flowing ALONE in the full pipe bore; X^2 = (dP/dz)_L / (dP/dz)_G.
        Re_l = G * (1.0 - x) * D / mul
        Re_g = G * x * D / muv
        dpdz_l = (get_darcy_friction_factor(Re_l, rr) / D
                  * math.pow(G * (1.0 - x), 2) / (2.0 * rhol)) if Re_l > 0.0 else 0.0
        dpdz_g = (get_darcy_friction_factor(Re_g, rr) / D
                  * math.pow(G * x, 2) / (2.0 * rhov)) if Re_g > 0.0 else 0.0
        if dpdz_l <= 0.0 or dpdz_g <= 0.0:
            # An extreme phase ratio collapsed x to 0/1 in double precision, or a
            # phase-alone gradient underflowed to 0.0: X and phi_L^2 are undefined,
            # but their physical limit is the surviving phase flowing alone. Return
            # that gradient with no X/C/phi2 diagnostics (they do not exist in the
            # limit) instead of dividing by zero into a bare 500 (v3.7 review).
            return max(dpdz_l, dpdz_g), {}
        X2 = dpdz_l / dpdz_g
        X = math.sqrt(X2)
        # C by phase-alone regime (liquid-gas): tt 20, vt 12, tv 10, vv 5.
        # "Viscous" uses the same Re < 2300 threshold as the friction function.
        liq_lam = Re_l < 2300
        gas_lam = Re_g < 2300
        C = 5 if (liq_lam and gas_lam) else 10 if gas_lam else 12 if liq_lam else 20
        phi_l2 = 1.0 + C / X + 1.0 / X2
        return phi_l2 * dpdz_l, {"phi2": phi_l2, "lm_X": X, "lm_C": C}

    if method == "msh":
        # Mueller-Steinhagen & Heck (1986): linear interpolation between the
        # all-liquid (A) and all-gas (B) gradients, dP/dz = Gc*(1-x)^(1/3) + B*x^3.
        Re_lo = G * D / mul
        Re_go = G * D / muv
        f_lo = get_darcy_friction_factor(Re_lo, rr)
        f_go = get_darcy_friction_factor(Re_go, rr)
        A_lo = f_lo / D * G * G / (2.0 * rhol)
        B_go = f_go / D * G * G / (2.0 * rhov)
        Gc = A_lo + 2.0 * (B_go - A_lo) * x
        dpdz = Gc * math.pow(1.0 - x, 1.0 / 3.0) + B_go * math.pow(x, 3)
        if dpdz <= 0.0:
            # Gc goes negative when the entered vapor density exceeds ~2x the liquid
            # density (swapped-label inputs) — outside the correlation's domain, and
            # a negative "friction" term would silently subtract from dpPa under a
            # normal badge (the Known-Issue-#3 defect class). Reject it (v3.7 review).
            raise ValueError("The Müller-Steinhagen-Heck correlation requires liquid density above vapor density — check the phase property inputs.")
        return dpdz, {}

    # Friedel (1979): phi_lo^2 on the all-flow-as-liquid gradient.
    if muv >= mul:
        raise ValueError("The Friedel correlation requires vapor viscosity below liquid viscosity.")
    Re_lo = G * D / mul
    Re_go = G * D / muv
    f_lo = get_darcy_friction_factor(Re_lo, rr)
    f_go = get_darcy_friction_factor(Re_go, rr)
    dpdz_lo = f_lo / D * G * G / (2.0 * rhol)
    rho_h = 1.0 / (x / rhov + (1.0 - x) / rhol)
    E = math.pow(1.0 - x, 2) + x * x * (rhol * f_go) / (rhov * f_lo)
    F = math.pow(x, 0.78) * math.pow(1.0 - x, 0.224)
    H = (math.pow(rhol / rhov, 0.91) * math.pow(muv / mul, 0.19)
         * math.pow(1.0 - muv / mul, 0.7))
    Fr = G * G / (9.81 * D * rho_h * rho_h)
    We = G * G * D / (sigma * rho_h)
    phi_lo2 = E + 3.24 * F * H / (math.pow(Fr, 0.045) * math.pow(We, 0.035))
    return phi_lo2 * dpdz_lo, {"phi2": phi_lo2}

class handler(BaseHTTPRequestHandler):
    def _error(self, message, badge, code=200):
        # Structured-error writer for the v3.0 PR-1 validation guards. The harmonized
        # superset {error, message, badge, badgeClass} — never let an input problem
        # escape as a bare 500 without CORS/JSON again.
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "error": True, "message": message, "badge": badge,
            "badgeClass": "px-2 py-1 text-[10px] rounded bg-red-500/20 text-red-400"
        }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            if not isinstance(data, dict):
                raise ValueError('body must be a JSON object')
        except (ValueError, KeyError, json.JSONDecodeError):
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": True,
                "message": "Bad request — the payload is not valid JSON.",
                "badge": "Bad Request",
                "badgeClass": "px-2 py-1 text-[10px] rounded bg-red-500/20 text-red-400"
            }).encode())
            return

        # Extract frontend payload. The float() coercions sit in their own try so a
        # non-numeric value (string, null) is a structured error, not an uncaught
        # ValueError/TypeError -> bare 500 (v3.0 PR-1 — same class as §11 #2).
        try:
            scale = float(data.get('scale', 1))
            D = float(data.get('id', 0)) * float(data.get('id_mult', 1))
            L = float(data.get('len', 0)) * float(data.get('len_mult', 1))
            eps = float(data.get('rough', 0)) * float(data.get('rough_mult', 1))
            dz = float(data.get('elev', 0)) * float(data.get('elev_mult', 1))

            Wv = float(data.get('v_flow', 0)) * float(data.get('v_flow_m', 1)) * scale
            rhov = float(data.get('v_den', 1)) * float(data.get('v_den_m', 1))
            muv = float(data.get('v_visc', 0.01)) * float(data.get('v_visc_m', 1))

            Wl = float(data.get('l_flow', 0)) * float(data.get('l_flow_m', 1)) * scale
            rhol = float(data.get('l_den', 1)) * float(data.get('l_den_m', 1))
            mul = float(data.get('l_visc', 1)) * float(data.get('l_visc_m', 1))
        except (TypeError, ValueError):
            self._error("Invalid numeric input.", "Invalid Input")
            return

        # NaN passes every ordered comparison below (NaN <= 0 is False) and Infinity
        # breaks downstream arithmetic; both would end up as bare NaN/Infinity tokens
        # in the response body, which RFC 8259 JSON cannot carry and browsers refuse
        # to parse (v3.0 PR-1).
        if not all(map(math.isfinite, (scale, D, L, eps, dz, Wv, rhov, muv, Wl, rhol, mul))):
            self._error("Invalid numeric input.", "Invalid Input")
            return

        # A NEGATIVE flow on one phase slipped every earlier guard and could zero the
        # HEM mixture-density denominator exactly (x/rho_v + (1-x)/rho_l = 0 -> bare
        # 500) or nearly (dpPa ~ 1e21 presented as a normal result). Reachable from
        # the UI — the number inputs carry no min attribute (v3.0 PR-1).
        if Wv < 0 or Wl < 0:
            self._error("Phase mass flows must be zero or positive.", "Invalid Input")
            return

        # Negative roughness makes the Colebrook argument negative -> math domain
        # error -> bare 500. Zero (hydraulically smooth) remains valid (v3.0 PR-1).
        if eps < 0:
            self._error("Pipe roughness must be zero or positive.", "Invalid Input")
            return

        Wt = Wv + Wl

        if Wt <= 0 or D <= 0:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": True, "message": "No flow — enter a positive mass flow and pipe ID.", "badge": "No Flow", "badgeClass": "px-2 py-1 text-[10px] rounded bg-red-500/20 text-red-400"}).encode())
            return

        # Zero or negative density/viscosity on a flowing phase previously escaped as a
        # ZeroDivisionError -> bare HTTP 500 without CORS or a JSON body, which the
        # frontend could only render as a generic "API Connection Failed" badge. Only
        # the phases that actually flow are checked, so a vapor-only payload does not
        # require liquid properties (and vice versa). Closes SPECIFICATION.md §11 #2.
        if (Wv > 0 and (rhov <= 0 or muv <= 0)) or (Wl > 0 and (rhol <= 0 or mul <= 0)):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": True, "message": "Phase density and viscosity must be positive values.", "badge": "Invalid Input", "badgeClass": "px-2 py-1 text-[10px] rounded bg-red-500/20 text-red-400"}).encode())
            return

        # v3.7 — two-phase method selection. An absent/null/empty-string tp_method
        # means "hem" (load-bearing default: pre-v3.7 payloads and share links
        # reproduce exactly). Every OTHER present value — including falsy JSON like
        # 0, false, [] — must pass the validation below, never silently fall back.
        tp_method = data.get('tp_method', 'hem')
        if tp_method is None or tp_method == '':
            tp_method = 'hem'
        if not isinstance(tp_method, str) or tp_method not in TP_METHOD_LABELS:
            self._error("Unknown two-phase method — use one of: hem, lm, msh, friedel.", "Invalid Input")
            return
        # Surface tension [N/m] is consumed by the Friedel correlation only, but a
        # PRESENT value is validated regardless of method (same policy as cfactor:
        # absent -> default, present-and-invalid -> reject). The UI enters mN/m and
        # sends N/m; 0.010 N/m is a representative light-hydrocarbon default.
        try:
            sigma = float(data.get('sigma', 0.010))
        except (TypeError, ValueError):
            self._error("Invalid numeric input.", "Invalid Input")
            return
        if not math.isfinite(sigma) or sigma <= 0:
            self._error("Surface tension must be a positive number in N/m (Friedel correlation).", "Invalid Input")
            return

        # Determine Phase & Mixture Properties (HEM Model)
        # v2.8 — `phase_key` accompanies each English `badge`. The frontend used to test
        # `badge.indexOf('Two-Phase')`, which breaks the moment the badge is localized;
        # it now branches on this key instead (i18n Milestone 4 pattern, matching the
        # `regime_key` that flowregime.py already returns).
        if Wv > 0 and Wl == 0:
            badge = "Single Phase (Vapor)"
            phase_key = "vapor"
            badgeClass = "px-2 py-1 text-[10px] rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
            rho, mu = rhov, muv
        elif Wl > 0 and Wv == 0:
            badge = "Single Phase (Liquid)"
            phase_key = "liquid"
            badgeClass = "px-2 py-1 text-[10px] rounded bg-blue-500/20 text-blue-400 border border-blue-500/30"
            rho, mu = rhol, mul
        else:
            badge = "Two-Phase (%s)" % TP_METHOD_LABELS[tp_method]
            phase_key = "twophase"
            badgeClass = "px-2 py-1 text-[10px] rounded bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30"
            x = Wv / Wt
            rho = 1.0 / ((x / rhov) + ((1 - x) / rhol))
            mu = x * muv + (1 - x) * mul

        # Hydraulic Calculations
        area = math.pi * math.pow(D, 2) / 4.0
        if area <= 0.0:
            # a subnormal-tiny D (e.g. 1e-300) passes D > 0 but underflows D^2 to 0.0
            self._error("Invalid numeric input.", "Invalid Input")
            return
        vel = Wt / (rho * area)
        Re = rho * vel * D / mu
        f_d = get_darcy_friction_factor(Re, eps / D)

        # Frictional (Darcy-Weisbach) + static-head terms, reported separately
        dpFric = f_d * (L / D) * rho * math.pow(vel, 2) / 2.0
        dpStatic = rho * 9.81 * dz

        # v3.7 — a non-HEM correlation replaces ONLY the two-phase frictional term.
        # vel/Re/f above stay the homogeneous-mixture values (they feed the RP 14E
        # and NORSOK screens); dpStatic and dpFittings stay on the no-slip density.
        tp_extras = {}
        if phase_key == "twophase" and tp_method != "hem":
            try:
                dpdz_tp, tp_extras = two_phase_dpdz(
                    tp_method, Wt / area, Wv / Wt, D, eps / D,
                    rhol, rhov, mul, muv, sigma)
            except ValueError as e:
                self._error(str(e), "Invalid Input")
                return
            dpFric = dpdz_tp * L

        # v2.8 — Crane TP-410 fittings. `k_total` is ΣK, summed CLIENT-side from Crane's
        # resistance-coefficient table (K = n·f_T, plus direct-K entrance/exit terms) and
        # sent as a single number, which keeps the Crane table out of this stdlib-only
        # endpoint. The loss is a fixed number of velocity heads: ΔP = ΣK·ρv²/2.
        #
        # DEFAULT 0 IS LOAD-BEARING: an omitted or zero k_total makes dpFittings exactly
        # 0.0, so every pre-v2.8 payload and share link reproduces the pinned reference
        # case (176.93 kPa) bit-for-bit. Do not change this default.
        #
        # L_eq is the equivalent straight length that would produce the same loss at the
        # ACTUAL flowing friction factor (L_eq = ΣK·D/f). It is reported for information
        # only — dpFittings above is computed directly from ΣK and never round-trips
        # through L_eq. Note `L` in the response deliberately remains the STRAIGHT-pipe
        # length, because the client divides by it to render ΔP per unit length; `L_eff`
        # carries the fittings-inclusive figure.
        try:
            k_total = float(data.get('k_total', 0) or 0)
        except (TypeError, ValueError):
            self._error("Invalid numeric input.", "Invalid Input")
            return
        if not math.isfinite(k_total) or k_total < 0:
            k_total = 0.0
        dpFittings = k_total * rho * math.pow(vel, 2) / 2.0
        L_eq = (k_total * D / f_d) if f_d > 0 else 0.0

        dpPa = dpFric + dpStatic + dpFittings

        # Flow-regime label for Reynolds number (single-phase reference only)
        if Re < 2300:
            re_regime = "Laminar"
            re_regime_key = "laminar"
        elif Re < 4000:
            re_regime = "Transitional"
            re_regime_key = "transitional"
        else:
            re_regime = "Turbulent"
            re_regime_key = "turbulent"

        # API RP 14E erosional velocity limit: Ve = C / sqrt(rho_mix)
        #
        # SI form Ve[m/s] = 1.2199033 * C / sqrt(rho[kg/m3]); C=100 continuous,
        # 125 intermittent. The constant is an exact unit conversion, not a fitted value:
        #     Ve[ft/s] = C / sqrt(rho[lb/ft3]),  rho[lb/ft3] = rho_SI / 16.0184634
        #     Ve[m/s]  = 0.3048 * sqrt(16.0184634) * C / sqrt(rho_SI)
        #              = 0.3048 * 4.00230725 * C / sqrt(rho_SI)
        #              = 1.2199032517 * C / sqrt(rho_SI)
        # where 16.0184634 = 0.45359237 / 0.3048^3 (lb/ft3 -> kg/m3).
        #
        # v2.8 — was 1.2247448714, which is exactly sqrt(1.5): a rounded "1.22" that had
        # been "precisioned" into the wrong closed form. It over-predicted Ve by +0.40 %,
        # making this screening check very slightly NON-conservative. Fixing it moves the
        # documented reference value from Ve ~ 7.72 to ~ 7.69 m/s at C=100; see
        # docs/SPECIFICATION.md §11 issue #9 and Vector 2.
        # An ABSENT cfactor still defaults to 100 (pre-v2.4 payloads and share links),
        # but a PRESENT non-positive or non-finite value is now rejected instead of
        # being silently mapped to 100 (cfactor: 0) or passed through to produce a
        # negative Ve under a green WITHIN LIMIT badge (negative cfactor). The UI
        # cannot send 0 — index.html maps a blank/zero field to 100 client-side — so
        # this only tightens the contract for direct API callers. Closes §11 #3.
        try:
            C_ero = float(data.get('cfactor', 100))
        except (TypeError, ValueError):
            self._error("Invalid numeric input.", "Invalid Input")
            return
        if not math.isfinite(C_ero) or C_ero <= 0:
            self._error("Erosion C-factor must be a positive number (API RP 14E; 100 continuous, 125 intermittent).", "Invalid Input")
            return
        v_ero = 1.2199032517 * C_ero / math.sqrt(rho) if rho > 0 else 0.0
        ero_ratio = (vel / v_ero) if v_ero > 0 else 0.0

        response = {
            "error": False,
            "dpPa": dpPa,
            "dpFric": dpFric,
            "dpStatic": dpStatic,
            "dpFittings": dpFittings,
            "vel": vel,
            "Re": Re,
            "re_regime": re_regime,
            "re_regime_key": re_regime_key,
            "f": f_d,
            "rho_mix": rho,
            "v_ero": v_ero,
            "ero_ratio": ero_ratio,
            "cfactor": C_ero,
            "k_total": k_total,
            "L_eq": L_eq,
            "badge": badge,
            "badgeClass": badgeClass,
            "phase_key": phase_key,
            "tp_method": tp_method,
            "sigma": sigma,
            "L": L,
            "L_eff": L + L_eq
        }
        # Method-specific diagnostics (v3.7): phi2 for lm/friedel, lm_X/lm_C for lm.
        response.update(tp_extras)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
