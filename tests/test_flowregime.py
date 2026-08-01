"""Reference-value regression for api/flowregime.py.

Only `compute()` is exercised. It is a pure function that validates, computes fluxes and
inclination, and classifies the regime — no matplotlib rendering. `render()` and
`process()` are separate, so these tests cost no PNG generation.

The expected values come from api/CLAUDE.md's "Reference Cases" section.
"""

import math

import pytest


def test_reference_case_is_churn_slug_on_the_vertical_map(flowregime_module,
                                                          dp_reference_payload):
    """api/CLAUDE.md: must classify as Churn / Slug Flow, theta = +45.0 deg, vertical map
    (j_G ~ 0.514 m/s, j_L ~ 0.500 m/s)."""
    res = flowregime_module.compute(dp_reference_payload)

    assert res["error"] is False
    assert res["regime"] == "Churn / Slug Flow"
    assert res["regime_key"] == "churn_slug"
    assert res["map_type"] == "vertical"
    assert res["theta_deg"] == pytest.approx(45.0, abs=0.05)
    assert res["jG"] == pytest.approx(0.5139, abs=5e-4)
    assert res["jL"] == pytest.approx(0.5002, abs=5e-4)
    assert res["clamped"] is False


def test_regime_key_accompanies_every_label(flowregime_module, dp_reference_payload):
    """regime_key is what the frontend's 3D animation switches on (index.html:2916).
    It must always be present and must never be the human label."""
    res = flowregime_module.compute(dp_reference_payload)
    assert res["regime_key"] in flowregime_module.REGION_COLORS
    assert res["regime_key"] != res["regime"]


def test_every_map_region_key_has_a_colour(flowregime_module):
    """A region whose key is missing from REGION_COLORS would render uncoloured and
    would break the 3D animation switch. Covers the wavy/wave and bubbly/bubble pairs,
    which are deliberately distinct keys with near-identical meaning."""
    for map_def in (flowregime_module.VERTICAL_MAP, flowregime_module.HORIZONTAL_MAP):
        for region in map_def["regions"]:
            key = region[0] if isinstance(region, (list, tuple)) else region["key"]
            assert key in flowregime_module.REGION_COLORS, f"no colour for {key!r}"


def test_inclination_selects_the_map(flowregime_module, dp_reference_payload):
    """|theta| >= 30 deg -> vertical (Hewitt & Roberts); otherwise horizontal (Baker)."""
    # theta = asin(dz/L); dz = 10 m over L = 100 m -> 5.7 deg -> horizontal
    shallow = flowregime_module.compute(dict(dp_reference_payload, elev=10))
    assert shallow["map_type"] == "horizontal"
    assert abs(shallow["theta_deg"]) < 30.0

    # dz = 60 m over L = 100 m -> 36.9 deg -> vertical
    steep = flowregime_module.compute(dict(dp_reference_payload, elev=60))
    assert steep["map_type"] == "vertical"
    assert steep["theta_deg"] == pytest.approx(math.degrees(math.asin(0.6)), abs=0.05)


def test_downward_inclination_is_negative_and_still_vertical(flowregime_module,
                                                             dp_reference_payload):
    res = flowregime_module.compute(dict(dp_reference_payload, elev=-70.711))
    assert res["theta_deg"] == pytest.approx(-45.0, abs=0.05)
    assert res["map_type"] == "vertical"


def test_superficial_velocities_and_fluxes_are_consistent(flowregime_module,
                                                          dp_reference_payload):
    res = flowregime_module.compute(dp_reference_payload)
    area = math.pi * res["D"] ** 2 / 4.0
    assert res["GG"] == pytest.approx(res["jG"] * 10.0, rel=1e-9)   # rho_v = 10
    assert res["GL"] == pytest.approx(res["jL"] * 500.0, rel=1e-9)  # rho_l = 500
    assert res["v_mix"] == pytest.approx(res["jG"] + res["jL"], rel=1e-12)
    assert res["lambda_l"] == pytest.approx(res["jL"] / res["v_mix"], rel=1e-12)
    assert area == pytest.approx(math.pi * (4 * 0.0254) ** 2 / 4.0, rel=1e-12)


def test_density_factor_is_multiplied_not_divided(flowregime_module,
                                                  dp_reference_payload):
    """REGRESSION GUARD for the v2.3.1 bug, which affected this file too.

    flowregime.py shares dp_calculator's multiply-to-SI convention. The pinned reference
    case sends densities in kg/m³ (factor 1.0), where multiplying and dividing are
    indistinguishable — so this uses lb/ft³ (factor 16.0185), where they are not.

    10 lb/ft³ vapour = 160.185 kg/m³; j_G = Wv / (rho_v * A) must fall accordingly.
    """
    si = flowregime_module.compute(dict(dp_reference_payload,
                                        v_den=160.185, v_den_m=1))
    usc = flowregime_module.compute(dict(dp_reference_payload,
                                         v_den=10, v_den_m=16.0185))

    assert si["error"] is False and usc["error"] is False
    assert usc["jG"] == pytest.approx(si["jG"], rel=1e-9)
    # A divide would give rho_v = 0.624 kg/m³ and a ~256x larger j_G.
    assert usc["jG"] == pytest.approx(dp_reference_payload["v_flow"] * 0.000277778
                                      / (160.185 * math.pi * 0.1016 ** 2 / 4), rel=1e-6)


def test_unit_factors_round_trip_between_si_and_usc(flowregime_module,
                                                    dp_reference_payload):
    """The same physical case entered in USC units must classify identically."""
    si = flowregime_module.compute(dp_reference_payload)
    usc = flowregime_module.compute(dict(
        dp_reference_payload,
        id=4, id_mult=0.0254,
        len=100 / 0.3048, len_mult=0.3048,
        elev=70.711 / 0.3048, elev_mult=0.3048,
        v_flow=150 / 0.45359237, v_flow_m=0.000125998,   # kg/h -> lb/h
        l_flow=7300 / 0.45359237, l_flow_m=0.000125998,
        v_den=10 / 16.0185, v_den_m=16.0185,
        l_den=500 / 16.0185, l_den_m=16.0185,
    ))
    assert usc["regime_key"] == si["regime_key"]
    assert usc["map_type"] == si["map_type"]
    assert usc["theta_deg"] == pytest.approx(si["theta_deg"], rel=1e-6)
    assert usc["jG"] == pytest.approx(si["jG"], rel=1e-4)
    assert usc["jL"] == pytest.approx(si["jL"], rel=1e-4)


# ── Validation guards (all return a structured error, never an exception) ────────

@pytest.mark.parametrize("override, fragment", [
    ({"id": 0}, "Pipe ID"),
    ({"len": 0}, "Pipe length"),
    ({"elev": 200}, "exceeds the pipe length"),
    ({"v_flow": 0, "l_flow": 0}, "No flow"),
    ({"v_flow": 0}, "Single-phase"),
    ({"l_flow": 0}, "Single-phase"),
    ({"v_den": 0}, "densities must be positive"),
    ({"v_den": 600}, "must be lower than liquid density"),
])
def test_validation_guards(flowregime_module, dp_reference_payload, override, fragment):
    res = flowregime_module.compute(dict(dp_reference_payload, **override))
    assert res["error"] is True
    assert fragment in res["message"], f"got {res['message']!r}"


def test_error_responses_carry_a_badge(flowregime_module, dp_reference_payload):
    """flowregime is the one endpoint that already returns both `message` and `badge`
    (docs/SPECIFICATION.md §11 #6 tracks harmonizing the other two to this superset)."""
    res = flowregime_module.compute(dict(dp_reference_payload, id=0))
    assert res["error"] is True
    assert "message" in res
    assert "badge" in res
