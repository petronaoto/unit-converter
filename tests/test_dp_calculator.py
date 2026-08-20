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

    # ρ_mix ≈ 251.7 kg/m³, V_e ≈ 7.69 m/s at C = 100, v/V_e ≈ 0.13 → within limit
    assert data["rho_mix"] == pytest.approx(251.69, abs=0.05)
    # v2.8 — V_e moved 7.720 -> 7.689 when the RP 14E SI constant was corrected from
    # sqrt(1.5) to the exact 1.2199033 (issue #9). The verdict is unchanged.
    assert data["v_ero"] == pytest.approx(7.689, abs=0.005)
    assert data["ero_ratio"] == pytest.approx(0.1319, abs=0.0005)
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

def test_erosional_velocity_constant_is_the_exact_unit_conversion(dp_module,
                                                                  post_to_handler,
                                                                  dp_reference_payload):
    """FIXED IN v2.8 (closes docs/SPECIFICATION.md §11 issue #9).

    The SI constant is an exact unit conversion, not a fitted value:

        Ve[ft/s] = C / sqrt(rho[lb/ft3]),   rho[lb/ft3] = rho_SI / 16.0184634
        Ve[m/s]  = 0.3048 * sqrt(16.0184634) * C / sqrt(rho_SI)
                 = 1.2199032517 * C / sqrt(rho_SI)

    where 16.0184634 = 0.45359237 / 0.3048**3. It was shipped as 1.2247448714 — exactly
    sqrt(1.5) — which over-predicted Ve by +0.40 % and made this screening check very
    slightly NON-conservative.

    Derived here from first principles rather than hard-coded, so the assertion cannot
    drift with the implementation.
    """
    _, data = post_to_handler(dp_module, dp_reference_payload)

    lb_per_ft3_to_kg_per_m3 = 0.45359237 / 0.3048 ** 3
    exact = 0.3048 * math.sqrt(lb_per_ft3_to_kg_per_m3)
    assert exact == pytest.approx(1.2199032517, abs=5e-10)

    expected = exact * data["cfactor"] / math.sqrt(data["rho_mix"])
    assert data["v_ero"] == pytest.approx(expected, rel=1e-9)
    # And the old wrong value must not come back.
    wrong = 1.2247448714 * data["cfactor"] / math.sqrt(data["rho_mix"])
    assert data["v_ero"] != pytest.approx(wrong, rel=1e-6)


def test_erosional_velocity_round_trips_through_field_units(dp_module, post_to_handler,
                                                            dp_reference_payload):
    """The whole point of the constant: computing Ve in ft/s from lb/ft3 and converting,
    versus computing directly in SI, must agree."""
    _, data = post_to_handler(dp_module, dp_reference_payload)
    rho_lb_ft3 = data["rho_mix"] / (0.45359237 / 0.3048 ** 3)
    ve_ft_s = data["cfactor"] / math.sqrt(rho_lb_ft3)
    assert data["v_ero"] == pytest.approx(ve_ft_s * 0.3048, rel=1e-9)


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


def test_zero_viscosity_returns_structured_error(dp_module, post_to_handler,
                                                 dp_reference_payload):
    """FIXED (closes docs/SPECIFICATION.md §11 #2): zero viscosity used to raise inside
    do_POST and escape as a bare HTTP 500 without CORS/JSON, surfacing in the UI as a
    generic "API Connection Failed" badge. It is now a structured 200 error carrying
    the harmonized {error, message, badge, badgeClass} superset."""
    payload = dict(dp_reference_payload, v_visc=0, l_visc=0)
    status, data = post_to_handler(dp_module, payload)
    assert status == 200
    assert data["error"] is True
    assert data["badge"] == "Invalid Input"
    assert "message" in data and "badgeClass" in data


def test_zero_density_returns_structured_error(dp_module, post_to_handler,
                                               dp_reference_payload):
    """Same §11 #2 family: a zero density on a flowing phase divided by zero in the
    HEM mixture (or velocity) expression. Now a structured error."""
    status, data = post_to_handler(dp_module, dict(dp_reference_payload, v_den=0))
    assert status == 200
    assert data["error"] is True
    assert data["badge"] == "Invalid Input"


def test_vapor_only_payload_does_not_require_liquid_properties(dp_module,
                                                               post_to_handler,
                                                               dp_reference_payload):
    """The §11 #2 guard must check only phases that actually FLOW: a vapor-only run
    with zeroed liquid density/viscosity fields is legitimate and must still compute."""
    payload = dict(dp_reference_payload, l_flow=0, l_den=0, l_visc=0)
    status, data = post_to_handler(dp_module, payload)
    assert status == 200
    assert data["error"] is False
    assert data["phase_key"] == "vapor"


def test_zero_cfactor_is_rejected_not_defaulted(dp_module, post_to_handler,
                                                dp_reference_payload):
    """FIXED (closes §11 #3): cfactor 0 was silently mapped to 100 by an `or 100.0`.
    A present-but-non-positive C-factor is now a structured error; only an ABSENT
    cfactor still defaults to 100 (pre-v2.4 payload compatibility, checked by
    test_cfactor_default_when_absent below)."""
    status, data = post_to_handler(dp_module, dict(dp_reference_payload, cfactor=0))
    assert status == 200
    assert data["error"] is True
    assert data["badge"] == "Invalid Input"


def test_negative_cfactor_is_rejected(dp_module, post_to_handler, dp_reference_payload):
    """FIXED (closes §11 #3): a negative C-factor produced a negative Ve, which made
    ero_ratio read 0.0 and the UI show a green WITHIN LIMIT badge — a non-conservative
    lie. Now a structured error."""
    status, data = post_to_handler(dp_module, dict(dp_reference_payload, cfactor=-50))
    assert status == 200
    assert data["error"] is True
    assert data["badge"] == "Invalid Input"


def test_cfactor_default_when_absent(dp_module, post_to_handler, dp_reference_payload):
    """An omitted cfactor (every pre-v2.4 payload and share link) must still default
    to 100 and reproduce Vector 2's erosional velocity."""
    payload = dict(dp_reference_payload)
    payload.pop("cfactor", None)
    status, data = post_to_handler(dp_module, payload)
    assert status == 200
    assert data["error"] is False
    assert data["cfactor"] == 100.0
    assert data["v_ero"] == pytest.approx(7.689, abs=5e-3)


def test_dp_error_responses_carry_the_harmonized_superset(dp_module, post_to_handler,
                                                          dp_reference_payload):
    """§11 #6: dp error responses used to carry badge but no message. Every error
    shape must now include the full {error, message, badge, badgeClass} superset."""
    no_flow = post_to_handler(dp_module, dict(dp_reference_payload, v_flow=0,
                                              l_flow=0))[1]
    bad_prop = post_to_handler(dp_module, dict(dp_reference_payload, v_den=0))[1]
    for data in (no_flow, bad_prop):
        assert data["error"] is True
        for field in ("message", "badge", "badgeClass"):
            assert field in data, f"missing {field}"


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
    assert data["dpFittings"] == pytest.approx(695.8544, abs=5e-3)      # Pa
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


def test_negative_phase_flow_is_rejected(dp_module, post_to_handler,
                                         dp_reference_payload):
    """A negative flow on ONE phase slipped every pre-existing guard (Wt stayed
    positive) and could zero the HEM mixture-density denominator EXACTLY -> bare 500
    (x/rho_v + (1-x)/rho_l = -0.1 + 0.1 for v_flow=-10/l_flow=20 at 10/20 kg/m³), or
    nearly -> dpPa ~ 1e21 presented as a normal result. The UI's number inputs carry
    no min attribute, so this was user-reachable."""
    status, data = post_to_handler(dp_module, dict(dp_reference_payload,
                                                   v_flow=-10, l_flow=20,
                                                   v_den=10, l_den=20))
    assert status == 200
    assert data["error"] is True
    assert data["badge"] == "Invalid Input"


def test_negative_roughness_is_rejected(dp_module, post_to_handler,
                                        dp_reference_payload):
    """Negative roughness drove the Colebrook argument negative -> math domain error
    -> bare 500, and was typeable in the UI. Zero (hydraulically smooth) stays valid."""
    status, data = post_to_handler(dp_module, dict(dp_reference_payload, rough=-0.045))
    assert status == 200
    assert data["error"] is True
    smooth = post_to_handler(dp_module, dict(dp_reference_payload, rough=0))[1]
    assert smooth["error"] is False


def test_non_numeric_field_is_a_structured_error(dp_module, post_to_handler,
                                                 dp_reference_payload):
    """float('abc') / float(None) raised outside any try -> bare 500. The extraction
    block (and the cfactor/k_total coercions) are now guarded."""
    for corrupt in (dict(dp_reference_payload, cfactor="abc"),
                    dict(dp_reference_payload, v_flow=None),
                    dict(dp_reference_payload, k_total="abc")):
        status, data = post_to_handler(dp_module, corrupt)
        assert status == 200
        assert data["error"] is True
        assert data["badge"] == "Invalid Input"


def test_nan_input_is_a_structured_error(dp_module, post_to_handler,
                                         dp_reference_payload):
    """NaN passes every ordered comparison and ends up as a bare NaN token in the
    response — invalid RFC 8259 JSON that a browser's res.json() rejects. An isfinite
    sweep now rejects NaN/Infinity in any extracted field."""
    for corrupt in (dict(dp_reference_payload, v_den=float("nan")),
                    dict(dp_reference_payload, id=float("inf"))):
        status, data = post_to_handler(dp_module, corrupt)
        assert status == 200
        assert data["error"] is True
        assert data["badge"] == "Invalid Input"


def test_dp_non_object_json_body_is_a_structured_400(dp_module, post_to_handler):
    """A valid-JSON non-object body ([1,2,3]) used to crash at data.get() -> bare
    500. Now the structured 400 branch."""
    status, data = post_to_handler(dp_module, [1, 2, 3])
    assert status == 400
    assert data["error"] is True
    assert data["badge"] == "Bad Request"


# ── v3.7 selectable two-phase methods (SPECIFICATION.md §9 Vector 14) ──────────────
#
# tp_method picks the two-phase FRICTIONAL correlation: hem (default), lm
# (Lockhart-Martinelli + Chisholm C), msh (Müller-Steinhagen & Heck 1986), friedel
# (Friedel 1979, consumes `sigma` [N/m], default 0.010). The method changes only
# dpFric: dpStatic, dpFittings, vel, Re, f and the RP 14E terms stay on the
# homogeneous no-slip basis. All pins computed independently against the Vector 2
# hydraulics before implementation (see SPECIFICATION.md §9 Vector 14).

def test_absent_tp_method_reproduces_the_hem_result_exactly(dp_module, post_to_handler,
                                                            dp_reference_payload):
    """The absent-field default is load-bearing, exactly like k_total and cfactor:
    every pre-v3.7 payload and share link must keep producing 176.93 kPa under the
    'Two-Phase (HEM)' badge, bit-for-bit."""
    absent = post_to_handler(dp_module, dp_reference_payload)[1]
    explicit = post_to_handler(dp_module, dict(dp_reference_payload, tp_method="hem"))[1]
    assert absent["badge"] == "Two-Phase (HEM)"
    assert absent["tp_method"] == "hem"
    # WHOLE-response equality (not approx): absent and explicit "hem" must take the
    # identical code path, so every field is float-identical — that is the contract.
    assert absent == explicit
    assert absent["dpPa"] / 1000 == pytest.approx(176.93, abs=0.05)
    # empty-string and null forms also mean "hem" (defensive share-link tolerance)
    for empty in ("", None):
        d = post_to_handler(dp_module, dict(dp_reference_payload, tp_method=empty))[1]
        assert d == explicit


def test_lm_reference_case(dp_module, post_to_handler, dp_reference_payload):
    """Lockhart-Martinelli on the Vector 2 hydraulics: both phase-alone flows are
    turbulent (Re_l 2.12e5, Re_g 4.35e4) -> Chisholm C = 20, X = 6.1663,
    phi_L^2 = 4.2697 -> dpFric 4.843 kPa, total 179.433 kPa."""
    data = post_to_handler(dp_module, dict(dp_reference_payload, tp_method="lm"))[1]
    assert data["error"] is False
    assert data["badge"] == "Two-Phase (Lockhart-Martinelli)"
    assert data["tp_method"] == "lm"
    assert data["lm_C"] == 20
    assert data["lm_X"] == pytest.approx(6.1663, abs=5e-4)
    assert data["phi2"] == pytest.approx(4.2697, abs=5e-4)
    assert data["dpFric"] / 1000 == pytest.approx(4.8429, abs=5e-3)
    assert data["dpPa"] / 1000 == pytest.approx(179.433, abs=0.05)


def test_msh_reference_case(dp_module, post_to_handler, dp_reference_payload):
    """Müller-Steinhagen & Heck on the Vector 2 hydraulics: A = 11.791 Pa/m,
    B = 529.67 Pa/m -> dpFric 3.243 kPa, total 177.833 kPa."""
    data = post_to_handler(dp_module, dict(dp_reference_payload, tp_method="msh"))[1]
    assert data["error"] is False
    assert data["badge"] == "Two-Phase (Müller-Steinhagen-Heck)"
    assert data["dpFric"] / 1000 == pytest.approx(3.2429, abs=5e-3)
    assert data["dpPa"] / 1000 == pytest.approx(177.833, abs=0.05)


def test_friedel_reference_case(dp_module, post_to_handler, dp_reference_payload):
    """Friedel at the default sigma = 0.010 N/m: E = 0.9783, F = 0.0473, H = 21.088,
    Fr = 1.0320, We = 2630.2 -> phi_LO^2 = 3.4294 -> dpFric 4.0435 kPa,
    total 178.634 kPa."""
    data = post_to_handler(dp_module, dict(dp_reference_payload, tp_method="friedel"))[1]
    assert data["error"] is False
    assert data["badge"] == "Two-Phase (Friedel)"
    assert data["sigma"] == pytest.approx(0.010, rel=1e-12)
    assert data["phi2"] == pytest.approx(3.4294, abs=5e-4)
    assert data["dpFric"] / 1000 == pytest.approx(4.0435, abs=5e-3)
    assert data["dpPa"] / 1000 == pytest.approx(178.634, abs=0.05)


def test_method_changes_only_the_frictional_term(dp_module, post_to_handler,
                                                 dp_reference_payload):
    """The contract that keeps the RP 14E / NORSOK screens comparable across methods:
    everything except dpFric (and therefore dpPa) is method-independent."""
    results = {m: post_to_handler(dp_module, dict(dp_reference_payload, tp_method=m,
                                                  k_total=5.3760))[1]
               for m in ("hem", "lm", "msh", "friedel")}
    base = results["hem"]
    for m, d in results.items():
        for field in ("dpStatic", "dpFittings", "vel", "Re", "f", "rho_mix",
                      "v_ero", "ero_ratio", "L_eq"):
            assert d[field] == pytest.approx(base[field], rel=1e-12), (m, field)
        assert d["dpPa"] == pytest.approx(d["dpFric"] + d["dpStatic"] + d["dpFittings"],
                                          rel=1e-12)


def test_single_phase_ignores_tp_method(dp_module, post_to_handler,
                                        dp_reference_payload):
    """A single-phase flow has no two-phase multiplier: the method is echoed but the
    numbers are identical to the default path, and the badge stays single-phase."""
    for override in ({"l_flow": 0}, {"v_flow": 0}):
        base = post_to_handler(dp_module, dict(dp_reference_payload, **override))[1]
        lm = post_to_handler(dp_module, dict(dp_reference_payload, tp_method="lm",
                                             **override))[1]
        assert lm["badge"] == base["badge"]
        assert lm["dpPa"] == pytest.approx(base["dpPa"], rel=1e-12)
        assert lm["tp_method"] == "lm"


def test_unknown_tp_method_is_rejected(dp_module, post_to_handler,
                                       dp_reference_payload):
    """A PRESENT unknown method is a structured error carrying the harmonized
    superset — never a silent fallback that would let a typo report HEM numbers
    under a correlation the caller thinks they chose. Falsy JSON values (0, false,
    [], {}) are NOT the absent/null/empty-string forms and must be rejected too —
    an `or "hem"` coercion would silently swallow them (v3.7 review)."""
    for bad in ("beggs-brill", "HEM", 42, ["lm"], 0, False, [], {}):
        status, data = post_to_handler(dp_module,
                                       dict(dp_reference_payload, tp_method=bad))
        assert status == 200
        assert data["error"] is True
        for field in ("error", "message", "badge", "badgeClass"):
            assert field in data
        assert data["badge"] == "Invalid Input"


def test_sigma_validation_matches_the_cfactor_contract(dp_module, post_to_handler,
                                                       dp_reference_payload):
    """Absent sigma -> 0.010 N/m; present non-positive / non-finite / non-numeric ->
    structured error, regardless of method (same policy as cfactor)."""
    for bad in (0, -0.01, float("nan"), "abc"):
        status, data = post_to_handler(dp_module,
                                       dict(dp_reference_payload, sigma=bad))
        assert status == 200
        assert data["error"] is True
        assert data["badge"] == "Invalid Input"
    # sigma enters only through We^-0.035 (We = G^2 D / (sigma rho_h)), so a HIGHER
    # sigma gives a LOWER Weber number and a HIGHER multiplier — pin the sign so a
    # future refactor cannot silently invert the We exponent.
    lo = post_to_handler(dp_module, dict(dp_reference_payload, tp_method="friedel",
                                         sigma=0.005))[1]
    hi = post_to_handler(dp_module, dict(dp_reference_payload, tp_method="friedel",
                                         sigma=0.020))[1]
    assert lo["phi2"] < hi["phi2"]


def test_friedel_requires_vapor_viscosity_below_liquid(dp_module, post_to_handler,
                                                       dp_reference_payload):
    """mu_v >= mu_l makes Friedel's (1 - mu_v/mu_l)^0.7 term complex-valued; the
    guard returns a structured error instead of a bare 500."""
    status, data = post_to_handler(dp_module, dict(dp_reference_payload,
                                                   tp_method="friedel",
                                                   v_visc=0.12, l_visc=0.12))
    assert status == 200
    assert data["error"] is True
    assert data["badge"] == "Invalid Input"
    assert "viscosity" in data["message"].lower()
    # the same viscosities are perfectly legal under the other methods
    for m in ("hem", "lm", "msh"):
        ok = post_to_handler(dp_module, dict(dp_reference_payload, tp_method=m,
                                             v_visc=0.12, l_visc=0.12))[1]
        assert ok["error"] is False


@pytest.mark.parametrize("v_visc_cp, l_visc_cp, expected_c", [
    (0.012, 0.12, 20),   # both phase-alone flows turbulent           -> tt
    (0.012, 60.0, 12),   # liquid-alone laminar, gas-alone turbulent  -> vt
    (0.80,  0.12, 10),   # liquid-alone turbulent, gas-alone laminar  -> tv
    (0.80,  60.0, 5),    # both laminar                               -> vv
])
def test_lm_chisholm_c_follows_the_phase_alone_regimes(dp_module, post_to_handler,
                                                       dp_reference_payload,
                                                       v_visc_cp, l_visc_cp,
                                                       expected_c):
    """Chisholm's C by the phase-ALONE Reynolds numbers (threshold 2300, matching
    the friction function): tt 20, vt 12, tv 10, vv 5. Viscosities chosen to move
    Re_l = 2.12e5/(l_visc/0.12) and Re_g = 4.35e4/(v_visc/0.012) across 2300."""
    data = post_to_handler(dp_module, dict(dp_reference_payload, tp_method="lm",
                                           v_visc=v_visc_cp, l_visc=l_visc_cp))[1]
    assert data["error"] is False
    assert data["lm_C"] == expected_c


def test_lm_degenerate_phase_ratio_returns_the_phase_alone_limit(dp_module,
                                                                 post_to_handler,
                                                                 dp_reference_payload):
    """v3.7 adversarial review: a phase ratio at/below machine epsilon collapses
    x to exactly 0.0/1.0 (or underflows a phase-alone gradient to 0.0) while both
    flows still pass the Wv>0/Wl>0 gates. The LM multiplier is undefined there;
    its physical limit is the surviving phase flowing alone — which must come back
    as a normal 200 with finite JSON and no phi2/lm_X/lm_C diagnostics, never a
    bare ZeroDivisionError 500 (the v3.0 PR-1 contract)."""
    # all-gas limit: x rounds to exactly 1.0
    status, gas = post_to_handler(dp_module, dict(dp_reference_payload,
                                                  v_flow=1e6, l_flow=1e-10,
                                                  tp_method="lm"))
    assert status == 200
    assert gas["error"] is False
    assert math.isfinite(gas["dpPa"]) and gas["dpFric"] > 0
    assert "phi2" not in gas and "lm_X" not in gas and "lm_C" not in gas

    # all-liquid limit: (G*x)^2 underflows to 0.0 with Wv still > 0
    status, liq = post_to_handler(dp_module, dict(dp_reference_payload,
                                                  v_flow=1e-300,
                                                  tp_method="lm"))
    assert status == 200
    assert liq["error"] is False
    assert math.isfinite(liq["dpPa"]) and liq["dpFric"] > 0
    assert "phi2" not in liq


def test_msh_rejects_a_negative_frictional_gradient(dp_module, post_to_handler,
                                                    dp_reference_payload):
    """v3.7 adversarial review: with swapped-label densities (vapor > ~2x liquid)
    the MSH interpolation term goes negative and would silently SUBTRACT friction
    from dpPa under a normal badge — the Known-Issue-#3 defect class. It is now a
    structured error; the same inputs stay legal under HEM (which has no density-
    ordering assumption)."""
    inverted = dict(dp_reference_payload, tp_method="msh", elev=0,
                    v_flow=9000, v_den=900, v_visc=0.5,
                    l_flow=1000, l_den=100, l_visc=0.3)
    status, data = post_to_handler(dp_module, inverted)
    assert status == 200
    assert data["error"] is True
    assert data["badge"] == "Invalid Input"
    for field in ("error", "message", "badge", "badgeClass"):
        assert field in data
    ok = post_to_handler(dp_module, dict(inverted, tp_method="hem"))[1]
    assert ok["error"] is False
    assert ok["dpFric"] > 0
