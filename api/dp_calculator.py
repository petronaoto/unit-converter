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

class handler(BaseHTTPRequestHandler):
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
        except (ValueError, KeyError, json.JSONDecodeError):
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": True,
                "badge": "Bad Request",
                "badgeClass": "px-2 py-1 text-[10px] rounded bg-red-500/20 text-red-400"
            }).encode())
            return

        # Extract frontend payload
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

        Wt = Wv + Wl

        if Wt <= 0 or D <= 0:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": True, "badge": "No Flow", "badgeClass": "px-2 py-1 text-[10px] rounded bg-red-500/20 text-red-400"}).encode())
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
            badge = "Two-Phase (HEM)"
            phase_key = "twophase"
            badgeClass = "px-2 py-1 text-[10px] rounded bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30"
            x = Wv / Wt
            rho = 1.0 / ((x / rhov) + ((1 - x) / rhol))
            mu = x * muv + (1 - x) * mul

        # Hydraulic Calculations
        area = math.pi * math.pow(D, 2) / 4.0
        vel = Wt / (rho * area)
        Re = rho * vel * D / mu
        f_d = get_darcy_friction_factor(Re, eps / D)

        # Frictional (Darcy-Weisbach) + static-head terms, reported separately
        dpFric = f_d * (L / D) * rho * math.pow(vel, 2) / 2.0
        dpStatic = rho * 9.81 * dz

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
        k_total = float(data.get('k_total', 0) or 0)
        if k_total < 0:
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
        C_ero = float(data.get('cfactor', 100)) or 100.0
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
            "L": L,
            "L_eff": L + L_eq
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
