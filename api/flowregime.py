# api/flowregime.py
# Two-phase flow regime map visualizer (seaborn / matplotlib, server-side rendering).
# Receives the same payload as dp_calculator.py and returns a base64 PNG flow regime
# map plus the classified regime, for the "Flow Regime" card in the Advanced tab.
import os
import io
import json
import math
import base64

os.environ.setdefault('MPLCONFIGDIR', '/tmp')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import Polygon as MplPolygon, Arc, FancyArrowPatch
import numpy as np
import seaborn as sns
from http.server import BaseHTTPRequestHandler

# ---- Theme (matches the app's slate/neon Tailwind palette) ----
BG = '#020617'      # slate-950
AX_BG = '#0f172a'   # slate-900
GRID = '#1e293b'    # slate-800
TEXT = '#e2e8f0'    # slate-200
MUTED = '#94a3b8'   # slate-400
ACCENT = '#fbbf24'  # amber-400

REGION_COLORS = {
    'bubbly':     '#3b82f6',  # blue-500
    'bubble':     '#3b82f6',
    'churn_slug': '#d946ef',  # fuchsia-500
    'slug':       '#d946ef',
    'wavy':       '#22d3ee',  # cyan-400
    'wave':       '#22d3ee',
    'annular':    '#f59e0b',  # amber-500
    'disperse':   '#22c55e',  # green-500
    'stratified': '#818cf8',  # indigo-400
}

# Map boundaries are simplified piecewise-linear approximations (in log10 space) of
# the classic vertical upflow map of Hewitt & Roberts (1969) and the horizontal-flow
# map of Baker (1954). Indicative only — not a mechanistic model.
# Vertical map: x = log10(jL [m/s]), y = log10(jG [m/s])
VERTICAL_MAP = {
    'name': 'Vertical flow regime map (Hewitt & Roberts type)',
    'xlabel': r'Liquid volumetric flux  $j_L$  [m/s]',
    'ylabel': r'Gas volumetric flux  $j_G$  [m/s]',
    'xlim': (-2.0, 1.0),
    'ylim': (-2.0, 2.0),
    # classification priority order; churn_slug is the background region
    'regions': [
        ('disperse',   'Disperse',          [(0.477, -2), (1, -2), (1, 2), (0.477, 2)]),
        ('annular',    'Annular',           [(-2, 1.35), (0.477, 0.95), (0.477, 2), (-2, 2)]),
        ('wavy',       'Wavy',              [(-2, 0.45), (-0.35, 0.45), (-0.35, 0.55), (-2, 1.20)]),
        ('bubbly',     'Bubbly',            [(-1.5, -2), (0.477, -2), (0.477, -0.15)]),
        ('churn_slug', 'Churn / Slug Flow', [(-2, -2), (1, -2), (1, 2), (-2, 2)]),
    ],
    'labels': {
        'churn_slug': ((-0.85, -0.55), 0),
        'bubbly':     ((-0.10, -1.55), 0),
        'annular':    ((-0.80, 1.62), 0),
        'wavy':       ((-1.55, 0.70), 0),
        'disperse':   ((0.74, 0.60), 90),
    },
}

# Horizontal map: x = log10(GL [kg/s.m2]), y = log10(GG [kg/s.m2])
HORIZONTAL_MAP = {
    'name': 'Horizontal flow regime map (Baker type)',
    'xlabel': r'Liquid mass flux  $G_L$  [kg/s·m²]',
    'ylabel': r'Gas mass flux  $G_G$  [kg/s·m²]',
    'xlim': (1.0, 4.0),
    'ylim': (-2.0, 2.0),
    'regions': [
        ('disperse',   'Disperse',   [(3.4, -2), (4, -2), (4, 2), (3.4, 2)]),
        ('annular',    'Annular',    [(1, 1.0), (3.4, 0.64), (3.4, 2), (1, 2)]),
        ('wave',       'Wave',       [(1, 0.0), (2.2, 0.0), (2.2, 0.82), (1, 1.0)]),
        ('stratified', 'Stratified', [(1, -2), (2.4, -2), (2.4, -0.4), (1, -0.4)]),
        ('bubble',     'Bubble',     [(2.4, -2), (3.4, -2), (3.4, -0.8), (2.4, -0.8)]),
        ('slug',       'Slug Flow',  [(1, -2), (4, -2), (4, 2), (1, 2)]),
    ],
    'labels': {
        'slug':       ((2.70, -0.15), 0),
        'stratified': ((1.60, -1.25), 0),
        'wave':       ((1.45, 0.45), 0),
        'bubble':     ((2.88, -1.50), 0),
        'annular':    ((1.85, 1.55), 0),
        'disperse':   ((3.70, 0.40), 90),
    },
}

ERR_BADGE_CLASS = "px-2 py-1 text-[10px] rounded bg-red-500/20 text-red-400"
OK_BADGE_CLASS = "px-2 py-1 text-[10px] rounded bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30"


def _err(message):
    return {"error": True, "message": message, "badge": "Cannot Visualize", "badgeClass": ERR_BADGE_CLASS}


def _blend(hex_color, bg_hex, alpha):
    """Blend a color onto the background so stacked patches stay clean (no alpha bleed)."""
    c = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(bg_hex[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(int(alpha * ci + (1 - alpha) * bi) for ci, bi in zip(c, b))


def classify(map_def, x, y):
    for key, label, verts in map_def['regions']:
        if MplPath(verts).contains_point((x, y)):
            return key, label
    key, label, _ = map_def['regions'][-1]
    return key, label


def compute(data):
    """Validate inputs, compute fluxes and inclination, classify the regime."""
    try:
        scale = float(data.get('scale', 1))
        D = float(data.get('id', 0)) * float(data.get('id_mult', 1))
        L = float(data.get('len', 0)) * float(data.get('len_mult', 1))
        dz = float(data.get('elev', 0)) * float(data.get('elev_mult', 1))
        Wv = float(data.get('v_flow', 0)) * float(data.get('v_flow_m', 1)) * scale
        rhov = float(data.get('v_den', 1)) * float(data.get('v_den_m', 1))
        Wl = float(data.get('l_flow', 0)) * float(data.get('l_flow_m', 1)) * scale
        rhol = float(data.get('l_den', 1)) * float(data.get('l_den_m', 1))
    except (TypeError, ValueError):
        return _err("Invalid numeric input.")

    if D <= 0:
        return _err("Pipe ID must be a positive value.")
    if L <= 0:
        return _err("Pipe length must be a positive value.")
    if abs(dz) > L:
        return _err("Physically impossible geometry: |elevation change| (%.3g m) exceeds the pipe length (%.3g m)." % (abs(dz), L))
    if Wv <= 0 and Wl <= 0:
        return _err("No flow — enter vapor and liquid mass flows.")
    if Wv <= 0 or Wl <= 0:
        return _err("Single-phase flow detected. The two-phase flow regime map requires BOTH a vapor and a liquid mass flow greater than zero.")
    if rhov <= 0 or rhol <= 0:
        return _err("Phase densities must be positive values.")
    if rhov >= rhol:
        return _err("Physically impossible phase properties: vapor density (%.4g kg/m³) must be lower than liquid density (%.4g kg/m³)." % (rhov, rhol))

    theta_deg = math.degrees(math.asin(dz / L))
    A = math.pi * D * D / 4.0
    jG = Wv / (rhov * A)   # superficial gas velocity [m/s]
    jL = Wl / (rhol * A)   # superficial liquid velocity [m/s]
    GG = Wv / A            # gas mass flux [kg/s.m2]
    GL = Wl / A            # liquid mass flux [kg/s.m2]

    if abs(theta_deg) >= 30.0:
        map_def, map_type = VERTICAL_MAP, 'vertical'
        x, y = math.log10(jL), math.log10(jG)
    else:
        map_def, map_type = HORIZONTAL_MAP, 'horizontal'
        x, y = math.log10(GL), math.log10(GG)

    (x0, x1), (y0, y1) = map_def['xlim'], map_def['ylim']
    xc, yc = min(max(x, x0), x1), min(max(y, y0), y1)
    clamped = (xc != x) or (yc != y)
    key, label = classify(map_def, xc, yc)

    return {
        "error": False,
        "regime_key": key,
        "regime": label,
        "map_type": map_type,
        "map_def": map_def,
        "theta_deg": theta_deg,
        "D": D, "L": L, "dz": dz,
        "jG": jG, "jL": jL, "GG": GG, "GL": GL,
        "v_mix": jG + jL,
        "lambda_l": jL / (jG + jL),
        "x": xc, "y": yc,
        "clamped": clamped,
    }


def _log_ticks(lo, hi):
    ticks = list(range(int(math.ceil(lo)), int(math.floor(hi)) + 1))
    labels = []
    for t in ticks:
        if t == 0:
            labels.append('1')
        elif t == 1:
            labels.append('10')
        else:
            labels.append(r'$10^{%d}$' % t)
    return ticks, labels


def render(res):
    """Render the regime map + inclination schematic; return a data-URI PNG string."""
    sns.set_theme(style='dark', rc={
        'figure.facecolor': BG, 'axes.facecolor': AX_BG,
        'axes.edgecolor': GRID, 'grid.color': GRID,
        'text.color': TEXT, 'axes.labelcolor': MUTED,
        'xtick.color': MUTED, 'ytick.color': MUTED,
        'font.family': 'DejaVu Sans',
    })
    map_def = res['map_def']
    fig = plt.figure(figsize=(8.6, 4.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[2.5, 1.0], height_ratios=[1.0, 1.15],
                          wspace=0.28, hspace=0.35,
                          left=0.075, right=0.97, top=0.82, bottom=0.14)
    ax = fig.add_subplot(gs[:, 0])
    ax_info = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[1, 1])
    ax_info.axis('off')

    # --- Regime map (drawn in log10 space; background region first, others on top) ---
    palette = {k: _blend(c, AX_BG, 0.32) for k, c in REGION_COLORS.items()}
    for key, label, verts in reversed(map_def['regions']):
        ax.add_patch(MplPolygon(verts, closed=True, facecolor=palette[key],
                                edgecolor=REGION_COLORS[key], linewidth=1.1, zorder=2))
    region_labels = {k: l for k, l, _ in map_def['regions']}
    for key, ((lx, ly), rot) in map_def['labels'].items():
        hl = key == res['regime_key']
        ax.text(lx, ly, region_labels[key].upper(),
                ha='center', va='center', rotation=rot, zorder=4,
                fontsize=8 if not hl else 9, fontweight='bold',
                color='#ffffff' if hl else _blend(REGION_COLORS[key], '#ffffff', 0.55))

    (x0, x1), (y0, y1) = map_def['xlim'], map_def['ylim']
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    xt, xl = _log_ticks(x0, x1)
    yt, yl = _log_ticks(y0, y1)
    ax.set_xticks(xt); ax.set_xticklabels(xl, fontsize=8)
    ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=8)
    ax.grid(True, linewidth=0.5, alpha=0.55, zorder=1)
    ax.set_xlabel(map_def['xlabel'], fontsize=9)
    ax.set_ylabel(map_def['ylabel'], fontsize=9)
    ax.set_title(map_def['name'], fontsize=8.5, color=MUTED, pad=6)

    # operating point: halo + star
    ax.scatter([res['x']], [res['y']], s=900, marker='o', facecolor=ACCENT, alpha=0.18, zorder=5, edgecolor='none')
    ax.scatter([res['x']], [res['y']], s=300, marker='*', facecolor=ACCENT, edgecolor='white', linewidth=0.9, zorder=6)
    ha = 'left' if res['x'] < (x0 + x1) / 2 else 'right'
    dx = 0.08 if ha == 'left' else -0.08
    va = 'bottom' if res['y'] < (y0 + y1) / 2 else 'top'
    dy = 0.10 if va == 'bottom' else -0.10
    ax.annotate('OPERATING POINT', (res['x'] + dx, res['y'] + dy), ha=ha, va=va,
                fontsize=7.5, fontweight='bold', color=ACCENT, zorder=6)

    # --- Inclination schematic ---
    th = math.radians(res['theta_deg'])
    px, py = math.cos(th), math.sin(th)
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.plot([0, 1.05], [0, 0], ls='--', lw=1, color=MUTED, alpha=0.7)               # horizontal datum
    ax2.plot([0, px], [0, py], lw=9, color=REGION_COLORS[res['regime_key']],
             solid_capstyle='round', alpha=0.85, zorder=3)                            # pipe
    ax2.plot([0, px], [0, py], lw=2.2, color='white', solid_capstyle='round', alpha=0.55, zorder=4)
    if abs(res['theta_deg']) > 0.05:
        ax2.add_patch(Arc((0, 0), 0.62, 0.62, theta1=min(0, res['theta_deg']),
                          theta2=max(0, res['theta_deg']), color=ACCENT, lw=1.4, zorder=4))
        ax2.plot([px, px], [py, 0], ls=':', lw=1, color=MUTED, alpha=0.8)             # elevation drop line
    ax2.add_patch(FancyArrowPatch((0.55 * px, 0.55 * py), (0.80 * px, 0.80 * py),
                                  arrowstyle='-|>', mutation_scale=16, color='white', zorder=5))
    ax2.text(0.40, -0.02 if th >= 0 else 0.06, 'θ = %+.1f°' % res['theta_deg'],
             fontsize=10, fontweight='bold', color=ACCENT,
             ha='left', va='top' if th >= 0 else 'bottom')
    pad = 0.30
    ax2.set_xlim(-0.18, 1.22)
    ax2.set_ylim(min(0, py) - pad, max(0, py) + pad)
    ax2.set_title('INCLINATION  (Δz / L)', fontsize=8.5, color=MUTED, pad=6)
    info = ('L = %.4g m   Δz = %+.4g m\n'
            '$j_G$ = %.3g m/s   $j_L$ = %.3g m/s\n'
            '$G_G$ = %.3g kg/s·m²\n'
            '$G_L$ = %.3g kg/s·m²\n'
            '$v_{mix}$ = %.3g m/s') % (res['L'], res['dz'], res['jG'], res['jL'],
                                       res['GG'], res['GL'], res['v_mix'])
    ax_info.text(0.0, 0.98, info, transform=ax_info.transAxes, fontsize=7.6, color=TEXT,
                 va='top', ha='left', linespacing=1.75,
                 bbox=dict(boxstyle='round,pad=0.55', facecolor=AX_BG, edgecolor=GRID))

    fig.suptitle('FLOW REGIME:  %s' % res['regime'].upper(), x=0.075, y=0.955,
                 ha='left', fontsize=13, fontweight='bold', color=ACCENT)
    footer = 'Simplified boundaries adapted from Hewitt & Roberts (1969) and Baker (1954) — indicative only.'
    if res['clamped']:
        footer = '⚠ Operating point lies outside the map range — shown clamped at the boundary.  ' + footer
    fig.text(0.075, 0.02, footer, fontsize=7, color=MUTED if not res['clamped'] else ACCENT)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=115, facecolor=BG)
    plt.close(fig)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')


def process(data):
    res = compute(data)
    if res.get('error'):
        return res
    image = render(res)
    badge = '%s | θ = %+.1f°' % (res['regime'], res['theta_deg'])
    return {
        "error": False,
        "image": image,
        "regime": res['regime'],
        "regime_key": res['regime_key'],
        "map_type": res['map_type'],
        "theta_deg": res['theta_deg'],
        "jG": res['jG'], "jL": res['jL'],
        "GG": res['GG'], "GL": res['GL'],
        "v_mix": res['v_mix'],
        "lambda_l": res['lambda_l'],
        "clamped": res['clamped'],
        "badge": badge,
        "badgeClass": OK_BADGE_CLASS,
    }


class handler(BaseHTTPRequestHandler):
    def _respond(self, code, payload):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(content_length))
        except (ValueError, KeyError, json.JSONDecodeError):
            self._respond(400, {"error": True, "message": "Bad request.", "badge": "Bad Request", "badgeClass": ERR_BADGE_CLASS})
            return
        try:
            self._respond(200, process(data))
        except Exception:
            self._respond(500, {"error": True, "message": "Rendering failed on the server.", "badge": "Server Error", "badgeClass": ERR_BADGE_CLASS})
