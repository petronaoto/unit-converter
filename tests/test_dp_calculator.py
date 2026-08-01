"""Reference-value regression for api/dp_calculator.py.

The expected values come from api/CLAUDE.md's "Reference Cases" section and are
reproduced here so a change to the endpoint fails loudly rather than silently
invalidating the documentation.

This suite locks CURRENT behavior. Where current behavior is a known defect, the test
says so explicitly and still asserts it — closing an issue in the register is a
deliberate act that should also update the test, not something that slips through.
"""

import math

import pytest


# ── The pinned reference case (api/CLAUDE.md) ────────────────────────────────────

def test_reference_case_reproduces(dp_module, post_to_handler, dp_reference_payload):
    status, data = post_to_handler(dp_module, dp_reference_payload)

    assert status == 200
    assert data["error"] is False

    # ΔP_total ≈ 176.9 kPa (dpFric ≈ 2.34 kPa + dpStatic ≈ 174.6 kPa)
    assert data["dpPa"] / 1000 == pytest.approx(176.93, abs=0.05)
    assert data["dpFric"] / 1000 == pytest.approx(2.338, abs=0.005)
    assert data["dpStatic"] / 1000 == pytest.approx(174.59, abs=0.05)
    assert data["dpFric"] + data["dpStatic"] == pytest.approx(data["dpPa"], rel=1e-12)

    # vel ≈ 1.014 m/s, Re ≈ 2.20e5 (turbulent), Darcy f ≈ 0.0184
    assert data["vel"] == pytest.approx(1.0142, abs=0.0005)
    assert data["Re"] == pytest.approx(2.2011e5, rel=1e-3)
    assert data["re_regime"] == "Turbulent"
    assert data["f"] == pytest.approx(0.01835, abs=5e-5)

    # ρ_mix ≈ 251.7 kg/m³, V_e ≈ 7.72 m/s at C = 100, v/V_e ≈ 0.13 → within limit
    assert data["rho_mix"] == pytest.approx(251.69, abs=0.05)
    assert data["v_ero"] == pytest.approx(7.720, abs=0.005)
    assert data["ero_ratio"] == pytest.approx(0.1314, abs=0.0005)
    assert data["cfactor"] == 100

    assert data["badge"] == "Two-Phase (HEM)"
    assert data["L"] == pytest.approx(100.0)


def test_response_schema_is_stable(dp_module, post_to_handler, dp_reference_payload):
    """The frontend reads these keys by name; dropping one breaks the ΔP card silently."""
    _, data = post_to_handler(dp_module, dp_reference_payload)
    expected = {
        # v2.7 and earlier — removing any of these breaks the shipped ΔP card
        "error", "dpPa", "dpFric", "dpStatic", "vel", "Re", "re_regime", "f",
        "rho_mix", "v_ero", "ero_ratio", "cfactor", "badge", "badgeClass", "L",
        # v2.8 additions — all additive; nothing above was renamed or removed
        "dpFittings", "k_total", "L_eq", "L_eff", "phase_key", "re_regime_key",
    }
    assert expected <= set(data), f"missing response keys: {expected - set(data)}"


# ── Erosional velocity (API RP 14E) ──────────────────────────────────────────────

def test_erosional_velocity_uses_the_shipped_constant(dp_module, post_to_handler,
                                                      dp_reference_payload):
    """V_e = 1.2247448714 * C / sqrt(rho) as currently shipped.

    KNOWN ISSUE: the exact SI conversion of the RP 14E criterion is 1.21990
    (= 0.3048 * sqrt(16.018463)), not 1.2247448714 (= sqrt(1.5)). The shipped constant
    over-predicts V_e by +0.42 %, making the screening check slightly non-conservative.
    Logged in docs/SPECIFICATION.md §11 pending a deliberate, separately-tagged fix —
    correcting it changes the documented V_e ≈ 7.72 m/s in four places, so it must not
    happen as a side effect. When it is fixed, update this test and that register entry
    together.
    """
    _, data = post_to_handler(dp_module, dp_reference_payload)
    shipped = 1.2247448714 * data["cfactor"] / math.sqrt(data["rho_mix"])
    assert data["v_ero"] == pytest.approx(shipped, rel=1e-12)


def test_cfactor_scales_erosional_velocity(dp_module, post_to_handler,
                                           dp_reference_payload):
    """C = 125 (intermittent service) must give exactly 1.25x the C = 100 limit."""
    _, base = post_to_handler(dp_module, dp_reference_payload)
    payload = dict(dp_reference_payload, cfactor=125)
    _, hi = post_to_handler(dp_module, payload)
    assert hi["v_ero"] / base["v_ero"] == pytest.approx(1.25, rel=1e-12)
    assert hi["cfactor"] == 125


# ── Phase detection (HEM) ────────────────────────────────────────────────────────

def test_vapor_only_is_single_phase(dp_module, post_to_handler, dp_reference_payload):
    payload = dict(dp_reference_payload, l_flow=0)
    _, data = post_to_handler(dp_module, payload)
    assert data["error"] is False
    assert data["badge"] == "Single Phase (Vapor)"
    assert data["rho_mix"] == pytest.approx(10.0)


def test_liquid_only_is_single_phase(dp_module, post_to_handler, dp_reference_payload):
    payload = dict(dp_reference_payload, v_flow=0)
    _, data = post_to_handler(dp_module, payload)
    assert data["error"] is False
    assert data["badge"] == "Single Phase (Liquid)"
    assert data["rho_mix"] == pytest.approx(500.0)


def test_hem_mixture_density_is_the_no_slip_form(dp_module, post_to_handler,
                                                 dp_reference_payload):
    """1/rho = x/rho_v + (1-x)/rho_l with x = Wv/Wt."""
    _, data = post_to_handler(dp_module, dp_reference_payload)
    x = 150.0 / (150.0 + 7300.0)
    expected = 1.0 / (x / 10.0 + (1 - x) / 500.0)
    assert data["rho_mix"] == pytest.approx(expected, rel=1e-12)


# ── Unit-factor convention: every *_m / *_mult is MULTIPLY-to-SI ─────────────────
#
# These tests exist specifically because the pinned reference case cannot catch a
# regression here: it sends densities in kg/m³, whose factor is 1.0, so multiplying and
# dividing are indistinguishable. That is exactly the shape of the v2.3.1 bug, where
# density was erroneously DIVIDED by its factor. Every assertion below therefore uses a
# unit whose factor is NOT 1.

def test_liquid_density_factor_is_multiplied_not_divided(dp_module, post_to_handler,
                                                         dp_reference_payload):
    """REGRESSION GUARD for the v2.3.1 bug (api/CLAUDE.md: "always multiply").

    50 lb/ft³ must become 800.9 kg/m³, not 3.12 kg/m³.
    """
    payload = dict(dp_reference_payload,
                   l_den=50, l_den_m=16.0185,     # 50 lb/ft³
                   v_flow=0)                      # liquid only -> rho_mix == rho_l
    _, data = post_to_handler(dp_module, payload)

    assert data["rho_mix"] == pytest.approx(50 * 16.0185, rel=1e-9)


def test_vapor_density_factor_is_multiplied_not_divided(dp_module, post_to_handler,
                                                        dp_reference_payload):
    """Same guard on the OTHER phase. Both branches need their own case: a single-phase
    payload only ever exercises one of the two density conversions, so a bug in the
    unused one passes unnoticed.
    """
    payload = dict(dp_reference_payload,
                   v_den=1, v_den_m=16.0185,      # 1 lb/ft³
                   l_flow=0)                      # vapour only -> rho_mix == rho_v
    _, data = post_to_handler(dp_module, payload)

    assert data["rho_mix"] == pytest.approx(1 * 16.0185, rel=1e-9)


def test_two_phase_density_factors_are_both_multiplied(dp_module, post_to_handler,
                                                       dp_reference_payload):
    """And once more through the HEM branch, where both densities are live at the same
    time and neither is the whole answer."""
    payload = dict(dp_reference_payload,
                   v_den=1, v_den_m=16.0185,
                   l_den=50, l_den_m=16.0185)
    _, data = post_to_handler(dp_module, payload)

    x = 150.0 / (150.0 + 7300.0)
    expected = 1.0 / (x / (1 * 16.0185) + (1 - x) / (50 * 16.0185))
    assert data["rho_mix"] == pytest.approx(expected, rel=1e-9)


def test_diameter_factor_is_multiplied(dp_module, post_to_handler, dp_reference_payload):
    """4 in must become 0.1016 m. Velocity scales as 1/D², so a divide would be a 6e5x
    error — but assert the mechanism directly rather than a downstream symptom."""
    _, inches = post_to_handler(dp_module, dict(dp_reference_payload,
                                                id=4, id_mult=0.0254))
    _, metres = post_to_handler(dp_module, dict(dp_reference_payload,
                                                id=0.1016, id_mult=1))
    assert inches["vel"] == pytest.approx(metres["vel"], rel=1e-9)


def test_flow_factor_is_multiplied(dp_module, post_to_handler, dp_reference_payload):
    """7300 kg/h and 7.3 t/h are the same flow; their factors differ by 1000x."""
    _, kgh = post_to_handler(dp_module, dict(dp_reference_payload,
                                             l_flow=7300, l_flow_m=0.000277778))
    _, tph = post_to_handler(dp_module, dict(dp_reference_payload,
                                             l_flow=7.3, l_flow_m=0.277778))
    assert kgh["vel"] == pytest.approx(tph["vel"], rel=1e-6)
    assert kgh["dpPa"] == pytest.approx(tph["dpPa"], rel=1e-6)


def test_viscosity_factor_is_multiplied(dp_module, post_to_handler,
                                        dp_reference_payload):
    """0.12 cP (factor 0.001) and 0.00012 Pa·s (factor 1) are the same viscosity."""
    _, cp = post_to_handler(dp_module, dict(dp_reference_payload,
                                            l_visc=0.12, l_visc_m=0.001))
    _, pas = post_to_handler(dp_module, dict(dp_reference_payload,
                                             l_visc=0.00012, l_visc_m=1))
    assert cp["Re"] == pytest.approx(pas["Re"], rel=1e-9)


def test_length_and_elevation_factors_are_multiplied(dp_module, post_to_handler,
                                                     dp_reference_payload):
    """100 m and 328.084 ft (factor 0.3048) are the same length."""
    _, si = post_to_handler(dp_module, dict(dp_reference_payload,
                                            len=100, len_mult=1,
                                            elev=70.711, elev_mult=1))
    _, usc = post_to_handler(dp_module, dict(dp_reference_payload,
                                             len=100 / 0.3048, len_mult=0.3048,
                                             elev=70.711 / 0.3048, elev_mult=0.3048))
    assert si["dpPa"] == pytest.approx(usc["dpPa"], rel=1e-6)
    assert si["L"] == pytest.approx(usc["L"], rel=1e-9)


def test_scale_multiplies_both_mass_flows_only(dp_module, post_to_handler,
                                               dp_reference_payload):
    """`scale` applies to Wv and Wl, NOT to geometry — so doubling it must leave the
    static head untouched while changing the frictional term."""
    _, base = post_to_handler(dp_module, dp_reference_payload)
    _, doubled = post_to_handler(dp_module, dict(dp_reference_payload, scale=2))

    assert doubled["dpStatic"] == pytest.approx(base["dpStatic"], rel=1e-12)
    assert doubled["vel"] == pytest.approx(2 * base["vel"], rel=1e-9)
    assert doubled["rho_mix"] == pytest.approx(base["rho_mix"], rel=1e-12)


# ── Friction factor ──────────────────────────────────────────────────────────────

def test_laminar_branch_is_exactly_64_over_re(dp_module):
    """Re < 2300 short-circuits Colebrook. 64/Re must be exact, not iterated."""
    for re in (100.0, 1000.0, 2299.0):
        assert dp_module.get_darcy_friction_factor(re, 1e-4) == pytest.approx(64.0 / re)


def test_laminar_threshold_is_exactly_2300(dp_module):
    """Probes BOTH sides of the boundary.

    Asserting only that low-Re values give 64/Re cannot detect the threshold moving
    upward — 2299 stays laminar whether the cutoff is 2300 or 4000. The value above the
    boundary is what pins it.
    """
    assert dp_module.get_darcy_friction_factor(2299.0, 1e-4) == pytest.approx(64.0 / 2299.0)
    # At Re = 2300 exactly, Colebrook takes over and must NOT agree with 64/Re.
    turbulent = dp_module.get_darcy_friction_factor(2300.0, 1e-4)
    assert turbulent != pytest.approx(64.0 / 2300.0, rel=1e-3)
    for re in (2300.0, 3000.0, 3999.0):
        f = dp_module.get_darcy_friction_factor(re, 1e-4)
        assert f != pytest.approx(64.0 / re, rel=1e-3), f"Re={re} still on the laminar branch"


def test_colebrook_satisfies_its_own_implicit_equation(dp_module):
    """The fixed-point iteration must actually converge on Colebrook-White."""
    for re, rr in ((1e4, 1e-3), (2.2011e5, 0.045e-3 / 0.1016), (1e7, 1e-5)):
        f = dp_module.get_darcy_friction_factor(re, rr)
        residual = 1.0 / math.sqrt(f) + 2.0 * math.log10(rr / 3.7 + 2.51 / (re * math.sqrt(f)))
        assert residual == pytest.approx(0.0, abs=1e-4)


@pytest.mark.parametrize("l_visc_cp, expected_re, expected_label", [
    (0.12, 220105.5, "Turbulent"),      # the reference case itself
    (5.30, 4993.5, "Turbulent"),        # just above the 4000 boundary
    (8.00, 3308.3, "Transitional"),     # between 2300 and 4000
    (15.00, 1764.4, "Laminar"),         # below 2300
])
def test_re_regime_labels_across_all_three_bands(dp_module, post_to_handler,
                                                 dp_reference_payload,
                                                 l_visc_cp, expected_re, expected_label):
    """Every band gets its own case, including one just above each boundary.

    Testing only a deeply-laminar case cannot detect a boundary drifting upward, and
    testing only the reference case cannot detect the transitional band vanishing —
    both were live gaps found by mutating the thresholds.
    """
    _, data = post_to_handler(dp_module, dict(dp_reference_payload, l_visc=l_visc_cp))
    assert data["Re"] == pytest.approx(expected_re, rel=1e-3)
    assert data["re_regime"] == expected_label
    if expected_label == "Laminar":
        assert data["f"] == pytest.approx(64.0 / data["Re"], rel=1e-9)


# ── Guard clauses (current behavior — see docs/SPECIFICATION.md §11) ─────────────

def test_no_flow_returns_a_structured_error(dp_module, post_to_handler,
                                            dp_reference_payload):
    payload = dict(dp_reference_payload, v_flow=0, l_flow=0)
    status, data = post_to_handler(dp_module, payload)
    assert status == 200
    assert data["error"] is True
    assert data["badge"] == "No Flow"


def test_zero_pipe_id_returns_a_structured_error(dp_module, post_to_handler,
                                                 dp_reference_payload):
    status, data = post_to_handler(dp_module, dict(dp_reference_payload, id=0))
    assert status == 200
    assert data["error"] is True
    assert data["badge"] == "No Flow"


def test_zero_viscosity_still_raises(dp_module, post_to_handler, dp_reference_payload):
    """KNOWN ISSUE (docs/SPECIFICATION.md §11 #2): zero viscosity raises inside do_POST
    and escapes as a bare HTTP 500 without CORS/JSON, surfacing in the UI as a generic
    "API Connection Failed" badge.

    This test asserts the CURRENT behavior so the suite is honest about it. The fix is
    proposed and awaiting approval; when it lands, this test becomes an assertion that a
    structured error object is returned instead.
    """
    payload = dict(dp_reference_payload, v_visc=0, l_visc=0)
    with pytest.raises(ZeroDivisionError):
        post_to_handler(dp_module, payload)


def test_unknown_payload_keys_are_ignored(dp_module, post_to_handler,
                                          dp_reference_payload):
    """Every field is read via data.get(key, default), so forward-compatible payloads
    cannot break an older deployment, and old share links cannot break a newer one.

    (This test originally used `k_total` as its example of an unknown key. v2.8 gave
    that key meaning, so it now uses one that is genuinely undefined — the failure when
    k_total became real was the test doing its job.)
    """
    _, base = post_to_handler(dp_module, dp_reference_payload)
    payload = dict(dp_reference_payload,
                   some_future_key="ignored", another_unknown=42)
    _, extended = post_to_handler(dp_module, payload)
    assert extended["dpPa"] == pytest.approx(base["dpPa"], rel=1e-12)


# ── v2.8 Crane fittings (SPECIFICATION.md §9 Vector 7) ───────────────────────────

def test_omitted_k_total_reproduces_the_pre_v28_result_exactly(dp_module,
                                                               post_to_handler,
                                                               dp_reference_payload):
    """THE backward-compatibility guarantee. A pre-v2.8 payload has no k_total at all;
    the default of 0 must make dpFittings exactly zero and leave dpPa untouched, so
    every share link and bookmark predating v2.8 still reproduces Vector 2."""
    _, data = post_to_handler(dp_module, dp_reference_payload)

    assert "k_total" not in dp_reference_payload
    assert data["dpFittings"] == 0.0
    assert data["L_eq"] == 0.0
    assert data["k_total"] == 0.0
    assert data["dpPa"] / 1000 == pytest.approx(176.93, abs=0.05)
    assert data["dpPa"] == pytest.approx(data["dpFric"] + data["dpStatic"], rel=1e-12)
    # L must remain the STRAIGHT-pipe length — the client divides by it for ΔP/length.
    assert data["L"] == pytest.approx(100.0)
    assert data["L_eff"] == pytest.approx(100.0)


def test_fit1_reference_case(dp_module, post_to_handler, dp_reference_payload):
    """Vector 7: ΣK = 5.3760 (4× 90° std elbow + gate + swing check + entrance + exit)
    on the Vector 2 hydraulics."""
    _, data = post_to_handler(dp_module, dict(dp_reference_payload, k_total=5.3760))

    assert data["k_total"] == pytest.approx(5.3760)
    assert data["dpFittings"] == pytest.approx(695.8532, abs=5e-3)      # Pa
    assert data["L_eq"] == pytest.approx(29.75863, abs=5e-4)            # m
    assert data["L_eff"] == pytest.approx(129.75863, abs=5e-4)
    assert data["dpPa"] / 1000 == pytest.approx(177.6247, abs=5e-3)     # kPa


def test_fittings_do_not_disturb_the_other_terms(dp_module, post_to_handler,
                                                 dp_reference_payload):
    """dpFric, dpStatic, vel, Re, f, rho_mix and the erosion check are all properties of
    the pipe and fluid, not of the fittings. Only dpFittings and dpPa may move."""
    _, base = post_to_handler(dp_module, dp_reference_payload)
    _, fitted = post_to_handler(dp_module, dict(dp_reference_payload, k_total=5.3760))

    for key in ("dpFric", "dpStatic", "vel", "Re", "f", "rho_mix", "v_ero",
                "ero_ratio", "L"):
        assert fitted[key] == pytest.approx(base[key], rel=1e-12), f"{key} moved"


def test_k_method_agrees_with_the_equivalent_length_method(dp_module, post_to_handler,
                                                           dp_reference_payload):
    """ΔP = ΣK·ρv²/2 and 'add L_eq to the run, then apply Darcy' are the same number by
    construction, since L_eq = ΣK·D/f. If they ever diverge, one of the two has been
    reimplemented incorrectly."""
    k_total = 5.3760
    _, base = post_to_handler(dp_module, dp_reference_payload)
    _, fitted = post_to_handler(dp_module, dict(dp_reference_payload, k_total=k_total))

    # Re-run with the straight length extended by L_eq and no fittings.
    lengthened = dict(dp_reference_payload, len=100.0 + fitted["L_eq"])
    _, viaLength = post_to_handler(dp_module, lengthened)

    assert viaLength["dpFric"] - base["dpFric"] == pytest.approx(
        fitted["dpFittings"], rel=1e-9)


@pytest.mark.parametrize("k_total", [0, 0.0, -5, None])
def test_non_positive_k_total_contributes_nothing(dp_module, post_to_handler,
                                                  dp_reference_payload, k_total):
    """Zero, absent and negative ΣK all collapse to no fittings. A negative K would
    otherwise subtract pressure drop, which is physically meaningless."""
    payload = dict(dp_reference_payload)
    if k_total is not None:
        payload["k_total"] = k_total
    _, data = post_to_handler(dp_module, payload)
    assert data["dpFittings"] == 0.0
    assert data["dpPa"] / 1000 == pytest.approx(176.93, abs=0.05)


def test_fittings_scale_linearly_with_sigma_k(dp_module, post_to_handler,
                                              dp_reference_payload):
    """ΔP_fittings = ΣK·ρv²/2 is linear in ΣK — doubling the fittings doubles their loss."""
    _, one = post_to_handler(dp_module, dict(dp_reference_payload, k_total=2.0))
    _, two = post_to_handler(dp_module, dict(dp_reference_payload, k_total=4.0))
    assert two["dpFittings"] == pytest.approx(2 * one["dpFittings"], rel=1e-12)
    assert two["L_eq"] == pytest.approx(2 * one["L_eq"], rel=1e-12)


# ── v2.8 machine-readable keys (i18n Milestone 4 pattern) ────────────────────────

@pytest.mark.parametrize("override, expected_key, expected_badge", [
    ({}, "twophase", "Two-Phase (HEM)"),
    ({"l_flow": 0}, "vapor", "Single Phase (Vapor)"),
    ({"v_flow": 0}, "liquid", "Single Phase (Liquid)"),
])
def test_phase_key_accompanies_every_badge(dp_module, post_to_handler,
                                           dp_reference_payload, override,
                                           expected_key, expected_badge):
    """The frontend branches on phase_key, not on the English badge text. Before v2.8 it
    tested `badge.indexOf('Two-Phase')`, which would silently stop firing in all 10
    languages the moment the badge is localized."""
    _, data = post_to_handler(dp_module, dict(dp_reference_payload, **override))
    assert data["phase_key"] == expected_key
    assert data["badge"] == expected_badge


@pytest.mark.parametrize("l_visc_cp, expected_key", [
    (0.12, "turbulent"), (8.00, "transitional"), (15.00, "laminar"),
])
def test_re_regime_key_matches_the_english_label(dp_module, post_to_handler,
                                                 dp_reference_payload,
                                                 l_visc_cp, expected_key):
    _, data = post_to_handler(dp_module, dict(dp_reference_payload, l_visc=l_visc_cp))
    assert data["re_regime_key"] == expected_key
    assert data["re_regime"].lower() == expected_key
