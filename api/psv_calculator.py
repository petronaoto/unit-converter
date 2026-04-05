# api/psv_calculator.py  — API 520 PRV Sizing (§5.6–§5.10 + Annex C)
import json
import math
from http.server import BaseHTTPRequestHandler

# API 526 Standard Effective Orifice Areas (letter, in², mm²)
API_526 = [
    ('D', 0.110,  71.0),
    ('E', 0.196,  126.5),
    ('F', 0.307,  198.1),
    ('G', 0.503,  324.5),
    ('H', 0.785,  506.5),
    ('J', 1.287,  830.3),
    ('K', 1.838,  1186.0),
    ('L', 2.853,  1840.6),
    ('M', 3.600,  2322.6),
    ('N', 4.340,  2800.0),
    ('P', 6.380,  4116.1),
    ('Q', 11.05,  7129.0),
    ('R', 16.00,  10322.6),
    ('T', 26.00,  16774.2),
]

def select_orifice(area_in2):
    for letter, a_in2, a_mm2 in API_526:
        if a_in2 >= area_in2:
            return letter, a_in2, a_mm2
    return ('T+', area_in2, area_in2 * 645.16)

def calc_C(k, units):
    """Coefficient C for gas/vapor critical flow (Eq. 8 USC / Eq. 9 SI)"""
    exp = (k + 1.0) / (k - 1.0)
    val = math.sqrt(k * (2.0 / (k + 1.0)) ** exp)
    return 520.0 * val if units == 'USC' else 0.03948 * val

def critical_pressure_ratio(k):
    """Pcf/P1 = (2/(k+1))^(k/(k-1))  (Eq. 1)"""
    return (2.0 / (k + 1.0)) ** (k / (k - 1.0))

def calc_F2(k, r):
    """Subcritical flow coefficient F2 (Eq. 18); r = P2/P1"""
    if r <= 0.0 or r >= 1.0:
        return 0.0
    t1 = k / (k - 1.0)
    t2 = r ** (2.0 / k)
    t3 = 1.0 - r ** ((k - 1.0) / k)
    t4 = 1.0 - r
    return math.sqrt(t1 * t2 * t3 / t4) if t4 > 0 else 0.0

def calc_KN_USC(P1_psia):
    """Napier correction KN, USC (Eq. 23/24)"""
    if P1_psia <= 1500.0:
        return 1.0
    return (0.1906 * P1_psia - 1000.0) / (0.2292 * P1_psia - 1061.0)

def calc_KN_SI(P1_kPa):
    """Napier correction KN, SI (Eq. 23/25)"""
    if P1_kPa <= 10339.0:
        return 1.0
    return (0.02764 * P1_kPa - 1000.0) / (0.03324 * P1_kPa - 1061.0)

def calc_Kv(Re):
    """Viscosity correction factor Kv (Eq. 30)"""
    if Re <= 0:
        return 1.0
    return 1.0 / (0.9935 + 2.878 / math.sqrt(Re) + 342.75 / (Re ** 1.5))

def omega_eta_c(omega):
    """Critical pressure ratio η_c via Eq. C.15 approximation"""
    if omega <= 0:
        return 0.55
    base = 1.0 + (1.0446 - 0.0093431 * math.sqrt(omega)) * omega ** (-0.56261)
    exp  = -0.70356 + 0.014685 * math.log(omega)
    return min(max(base ** exp, 0.05), 0.99)


# ── §5.6 Gas/Vapor ───────────────────────────────────────────────────────────
def size_gas(data, units):
    W  = float(data.get('W',  0))
    M  = float(data.get('M',  28.0))
    k  = float(data.get('k',  1.3))
    T  = float(data.get('T',  300.0))
    Z  = float(data.get('Z',  1.0))
    P1 = float(data.get('P1', 0))
    P2 = float(data.get('P2', 0))
    Kd = float(data.get('Kd', 0.975))
    Kb = float(data.get('Kb', 1.0))
    Kc = float(data.get('Kc', 1.0))

    if P1 <= 0 or W <= 0 or M <= 0:
        return {'error': True, 'message': 'W, M, and P1 must be > 0'}

    pcr = critical_pressure_ratio(k)
    Pcf = pcr * P1
    critical = P2 <= Pcf
    C = calc_C(k, units)

    if critical:
        # Eq. 2 (USC) / Eq. 5 (SI)
        A = (W / (C * Kd * P1 * Kb * Kc)) * math.sqrt(T * Z / M)
        regime = 'Critical Flow'
        badge_cls = 'px-2 py-1 text-[10px] rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
    else:
        # Eq. 12 (USC) / Eq. 15 (SI)
        r  = P2 / P1
        F2 = calc_F2(k, r)
        if F2 <= 0:
            return {'error': True, 'message': 'Cannot compute F2 — check k, P1, P2'}
        if units == 'USC':
            A = (W / (735.0 * F2 * Kd * Kc)) * math.sqrt(T * Z / (M * P1 * (P1 - P2)))
        else:
            A = (17.9 * W / (F2 * Kd * Kc)) * math.sqrt(T * Z / (M * P1 * (P1 - P2)))
        regime = f'Subcritical Flow (r = {r:.3f})'
        badge_cls = 'px-2 py-1 text-[10px] rounded bg-amber-500/20 text-amber-400 border border-amber-500/30'

    A_in2 = A / 645.16 if units == 'SI' else A
    letter, oa_in2, oa_mm2 = select_orifice(A_in2)
    return {
        'error': False,
        'area': round(A, 4),  'area_unit': 'mm²' if units == 'SI' else 'in²',
        'orifice': letter,
        'orifice_area': round(oa_mm2 if units == 'SI' else oa_in2, 3),
        'orifice_unit': 'mm²' if units == 'SI' else 'in²',
        'flow_regime': regime,
        'C':   round(C, 4),
        'Pcf': round(Pcf, 3),
        'critical_ratio': round(pcr, 4),
        'badge': regime, 'badgeClass': badge_cls,
    }


# ── §5.7 Steam ───────────────────────────────────────────────────────────────
def size_steam(data, units):
    W   = float(data.get('W',   0))
    P1  = float(data.get('P1',  0))
    Kd  = float(data.get('Kd',  0.975))
    Kb  = float(data.get('Kb',  1.0))
    Kc  = float(data.get('Kc',  1.0))
    KSH = float(data.get('KSH', 1.0))

    if P1 <= 0 or W <= 0:
        return {'error': True, 'message': 'W and P1 must be > 0'}

    if units == 'USC':
        KN = calc_KN_USC(P1)
        A  = W / (51.5 * P1 * Kd * Kb * Kc * KN * KSH)
    else:
        KN = calc_KN_SI(P1)
        A  = 190.5 * W / (P1 * Kd * Kb * Kc * KN * KSH)

    A_in2 = A / 645.16 if units == 'SI' else A
    letter, oa_in2, oa_mm2 = select_orifice(A_in2)
    return {
        'error': False,
        'area': round(A, 4),  'area_unit': 'mm²' if units == 'SI' else 'in²',
        'orifice': letter,
        'orifice_area': round(oa_mm2 if units == 'SI' else oa_in2, 3),
        'orifice_unit': 'mm²' if units == 'SI' else 'in²',
        'flow_regime': 'Steam — Critical Flow',
        'KN': round(KN, 4), 'KSH': KSH,
        'badge': 'Steam Critical Flow',
        'badgeClass': 'px-2 py-1 text-[10px] rounded bg-blue-500/20 text-blue-400 border border-blue-500/30',
    }


# ── §5.8 Liquid — Certified PRV ──────────────────────────────────────────────
def size_liquid_cert(data, units):
    Q  = float(data.get('Q',  0))
    Gl = float(data.get('Gl', 1.0))
    P1 = float(data.get('P1', 0))
    P2 = float(data.get('P2', 0))
    Kd = float(data.get('Kd', 0.65))
    Kw = float(data.get('Kw', 1.0))
    Kc = float(data.get('Kc', 1.0))
    mu = float(data.get('mu', 0))

    dP = P1 - P2
    if dP <= 0:
        return {'error': True, 'message': 'P1 must be greater than P2'}
    if Q <= 0:
        return {'error': True, 'message': 'Flow rate Q must be > 0'}

    # First pass: Kv = 1.0
    Kv = 1.0; Re = 1e9
    if units == 'USC':
        A = (Q / (38.0 * Kd * Kw * Kc * Kv)) * math.sqrt(Gl / dP)
    else:
        A = (11.78 * Q / (Kd * Kw * Kc * Kv)) * math.sqrt(Gl / dP)

    if mu > 0:
        A_in2_prelim = A / 645.16 if units == 'SI' else A
        _, A_std_in2, A_std_mm2 = select_orifice(A_in2_prelim)
        Re = (Q * (2800.0 * Gl) / (mu * math.sqrt(A_std_in2))
              if units == 'USC'
              else Q * (18800.0 * Gl) / (mu * math.sqrt(A_std_mm2)))
        Kv = calc_Kv(Re)
        if units == 'USC':
            A = (Q / (38.0 * Kd * Kw * Kc * Kv)) * math.sqrt(Gl / dP)
        else:
            A = (11.78 * Q / (Kd * Kw * Kc * Kv)) * math.sqrt(Gl / dP)

    A_in2 = A / 645.16 if units == 'SI' else A
    letter, oa_in2, oa_mm2 = select_orifice(A_in2)
    return {
        'error': False,
        'area': round(A, 4),  'area_unit': 'mm²' if units == 'SI' else 'in²',
        'orifice': letter,
        'orifice_area': round(oa_mm2 if units == 'SI' else oa_in2, 3),
        'orifice_unit': 'mm²' if units == 'SI' else 'in²',
        'flow_regime': 'Liquid — Certified PRV',
        'Kv': round(Kv, 4),
        'Re': round(Re, 1) if Re < 1e8 else None,
        'badge': 'Liquid (§5.8 Certified)',
        'badgeClass': 'px-2 py-1 text-[10px] rounded bg-blue-500/20 text-blue-400 border border-blue-500/30',
    }


# ── §5.9 Liquid — Non-Certified PRV ─────────────────────────────────────────
def size_liquid_noncert(data, units):
    Q  = float(data.get('Q',  0))
    Gl = float(data.get('Gl', 1.0))
    Ps = float(data.get('Ps', 0))   # set pressure
    P2 = float(data.get('P2', 0))
    Kd = float(data.get('Kd', 0.62))
    Kw = float(data.get('Kw', 1.0))
    Kc = float(data.get('Kc', 1.0))
    Kp = float(data.get('Kp', 1.0))
    mu = float(data.get('mu', 0))

    dP_eff = 1.25 * Ps - P2
    if dP_eff <= 0:
        return {'error': True, 'message': '1.25 × Ps must exceed P2'}
    if Q <= 0:
        return {'error': True, 'message': 'Flow rate Q must be > 0'}

    Kv = 1.0; Re = 1e9
    if units == 'USC':
        A = (Q / (38.0 * Kd * Kw * Kc * Kv * Kp)) * math.sqrt(Gl / dP_eff)
    else:
        A = (11.78 * Q / (Kd * Kw * Kc * Kv * Kp)) * math.sqrt(Gl / dP_eff)

    if mu > 0:
        A_in2_prelim = A / 645.16 if units == 'SI' else A
        _, A_std_in2, A_std_mm2 = select_orifice(A_in2_prelim)
        Re = (Q * (2800.0 * Gl) / (mu * math.sqrt(A_std_in2))
              if units == 'USC'
              else Q * (18800.0 * Gl) / (mu * math.sqrt(A_std_mm2)))
        Kv = calc_Kv(Re)
        if units == 'USC':
            A = (Q / (38.0 * Kd * Kw * Kc * Kv * Kp)) * math.sqrt(Gl / dP_eff)
        else:
            A = (11.78 * Q / (Kd * Kw * Kc * Kv * Kp)) * math.sqrt(Gl / dP_eff)

    A_in2 = A / 645.16 if units == 'SI' else A
    letter, oa_in2, oa_mm2 = select_orifice(A_in2)
    return {
        'error': False,
        'area': round(A, 4),  'area_unit': 'mm²' if units == 'SI' else 'in²',
        'orifice': letter,
        'orifice_area': round(oa_mm2 if units == 'SI' else oa_in2, 3),
        'orifice_unit': 'mm²' if units == 'SI' else 'in²',
        'flow_regime': 'Liquid — Non-Certified PRV',
        'Kv': round(Kv, 4), 'Kp': Kp,
        'Re': round(Re, 1) if Re < 1e8 else None,
        'badge': 'Liquid (§5.9 Non-Certified)',
        'badgeClass': 'px-2 py-1 text-[10px] rounded bg-purple-500/20 text-purple-400 border border-purple-500/30',
    }


# ── §5.10 Two-Phase — Omega Method (Annex C.2.2) ─────────────────────────────
def size_twophase(data, units):
    W         = float(data.get('W',   0))
    vo        = float(data.get('vo',  0))   # specific volume at inlet
    v9        = float(data.get('v9',  0))   # spec. vol. at 90 % of Po (flash)
    Po_input  = float(data.get('Po',  0))   # psia (USC) or kPa abs (SI)
    Pa_input  = float(data.get('Pa',  0))   # psia (USC) or kPa abs (SI)
    Kd        = float(data.get('Kd',  0.85))
    Kb        = float(data.get('Kb',  1.0))
    Kc        = float(data.get('Kc',  1.0))
    Kv        = float(data.get('Kv',  1.0))

    if vo <= 0 or v9 <= 0:
        return {'error': True, 'message': 'vo and v9 must be > 0'}
    if Po_input <= 0:
        return {'error': True, 'message': 'Relieving pressure Po must be > 0'}

    # Convert SI inputs from kPa → Pa for flux formula
    Po = Po_input * 1000.0 if units == 'SI' else Po_input
    Pa = Pa_input * 1000.0 if units == 'SI' else Pa_input

    # Step 1: Omega parameter (Eq. C.12)
    omega = 9.0 * (v9 / vo - 1.0)
    if omega < 0:
        return {'error': True, 'message': f'ω = {omega:.3f} < 0 — v9 must exceed vo'}

    # Step 2: Critical pressure ratio (Eq. C.15 approximation)
    eta_c = omega_eta_c(omega)
    Pc    = eta_c * Po
    critical = Pc >= Pa

    # Step 3: Mass flux
    if critical:
        if units == 'USC':
            G = 68.09 * eta_c * math.sqrt(Po / (vo * omega))
        else:
            G = eta_c * math.sqrt(Po / (vo * omega))
        regime = 'Two-Phase Critical (Omega)'
    else:
        eta_a = Pa / Po
        inner = -2.0 * omega * math.log(eta_a) + (omega - 1.0) * (1.0 - eta_a)
        denom = omega * (1.0 / eta_a - 1.0) + 1.0
        if inner <= 0 or denom <= 0:
            return {'error': True, 'message': 'Cannot compute subcritical mass flux — check inputs'}
        if units == 'USC':
            G = 68.09 * math.sqrt(inner) * math.sqrt(Po / vo) / denom
        else:
            G = math.sqrt(inner) * math.sqrt(Po / vo) / denom
        regime = 'Two-Phase Subcritical (Omega)'

    # Step 4: Required area (Eq. C.20 / C.21)
    if units == 'USC':
        A     = 0.04 * W / (Kd * Kb * Kc * Kv * G)
        A_in2 = A
    else:
        A     = 277.8 * W / (Kd * Kb * Kc * Kv * G)
        A_in2 = A / 645.16

    letter, oa_in2, oa_mm2 = select_orifice(A_in2)
    Pc_display = round(Pa_input * eta_c, 3)   # in original input units (kPa or psia)

    return {
        'error': False,
        'area': round(A, 4),  'area_unit': 'mm²' if units == 'SI' else 'in²',
        'orifice': letter,
        'orifice_area': round(oa_mm2 if units == 'SI' else oa_in2, 3),
        'orifice_unit': 'mm²' if units == 'SI' else 'in²',
        'flow_regime': regime,
        'omega': round(omega, 4),
        'eta_c': round(eta_c, 4),
        'Pc':    Pc_display,
        'G':     round(G, 3),
        'badge': 'Two-Phase (Omega Method)',
        'badgeClass': 'px-2 py-1 text-[10px] rounded bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30',
    }


# ── HTTP Handler ─────────────────────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            n    = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(n))
        except Exception:
            self._respond(400, {'error': True, 'message': 'Bad Request'})
            return

        mode  = data.get('mode',  'gas')
        units = data.get('units', 'USC')
        dispatch = {
            'gas':           size_gas,
            'steam':         size_steam,
            'liquid_cert':   size_liquid_cert,
            'liquid_noncert': size_liquid_noncert,
            'twophase':      size_twophase,
        }
        fn = dispatch.get(mode)
        if fn is None:
            result = {'error': True, 'message': f'Unknown mode: {mode}'}
        else:
            try:
                result = fn(data, units)
            except Exception as e:
                result = {'error': True, 'message': str(e)}

        self._respond(200, result)

    def _respond(self, code, body):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode('utf-8'))