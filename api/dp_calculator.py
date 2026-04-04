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
        rhov = float(data.get('v_den', 1)) / float(data.get('v_den_m', 1))
        muv = float(data.get('v_visc', 0.01)) * float(data.get('v_visc_m', 1))

        Wl = float(data.get('l_flow', 0)) * float(data.get('l_flow_m', 1)) * scale
        rhol = float(data.get('l_den', 1)) / float(data.get('l_den_m', 1))
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
        if Wv > 0 and Wl == 0:
            badge = "Single Phase (Vapor)"
            badgeClass = "px-2 py-1 text-[10px] rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
            rho, mu = rhov, muv
        elif Wl > 0 and Wv == 0:
            badge = "Single Phase (Liquid)"
            badgeClass = "px-2 py-1 text-[10px] rounded bg-blue-500/20 text-blue-400 border border-blue-500/30"
            rho, mu = rhol, mul
        else:
            badge = "Two-Phase (HEM)"
            badgeClass = "px-2 py-1 text-[10px] rounded bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30"
            x = Wv / Wt
            rho = 1.0 / ((x / rhov) + ((1 - x) / rhol))
            mu = x * muv + (1 - x) * mul

        # Hydraulic Calculations
        area = math.pi * math.pow(D, 2) / 4.0
        vel = Wt / (rho * area)
        Re = rho * vel * D / mu
        f_d = get_darcy_friction_factor(Re, eps / D)

        dpPa = (f_d * (L / D) * rho * math.pow(vel, 2) / 2.0) + (rho * 9.81 * dz)

        response = {
            "error": False,
            "dpPa": dpPa,
            "vel": vel,
            "badge": badge,
            "badgeClass": badgeClass,
            "L": L
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
