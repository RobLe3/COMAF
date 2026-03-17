"""Tests for PNMS constants and conversion functions."""
import math
import pytest
from comaf import pnms


def test_planck_length():
    assert abs(pnms.LAMBDA_P - 1.616e-35) / 1.616e-35 < 0.01

def test_planck_time():
    assert abs(pnms.T_P - 5.391e-44) / 5.391e-44 < 0.01

def test_planck_energy():
    assert abs(pnms.E_P - 1.956e9) / 1.956e9 < 0.01

def test_planck_mass():
    assert abs(pnms.M_P - 2.176e-8) / 2.176e-8 < 0.01

def test_plameter_approx_1m():
    # 1 Plameter should be within 10x of 1 meter
    assert 0.1 <= pnms.PLAMETER <= 10.0

def test_plasecond_approx_1s():
    assert 0.1 <= pnms.PLASECOND <= 10.0

def test_warptick_approx_hubble_time():
    # 1 WarpTick ~ 13.8 Gyr ~ 4.35e17 s
    hubble_time_s = 13.8e9 * 365.25 * 24 * 3600
    assert abs(pnms.WARPTICK - hubble_time_s) / hubble_time_s < 0.5

def test_roundtrip_plameters():
    d = 1000.0  # 1 km in meters
    assert abs(pnms.from_plameters(pnms.to_plameters(d)) - d) / d < 1e-10

def test_roundtrip_plaseconds():
    t = 3600.0
    assert abs(pnms.from_plaseconds(pnms.to_plaseconds(t)) - t) / t < 1e-10

def test_e_jump_below_planck():
    # E_jump must always be < E_p
    for v in [0, 0.1*pnms.C, 0.9*pnms.C, 0.99*pnms.C, 0.9999*pnms.C]:
        ej = pnms.e_jump(v)
        assert ej < pnms.E_P, f"E_jump({v}) = {ej} >= E_p = {pnms.E_P}"

def test_e_jump_zero_at_rest():
    ej = pnms.e_jump(0.0)
    assert ej < 1e-10 * pnms.E_P  # very small at v=0

def test_decoherence_metric_range():
    for grad_s, t in [(0, 0), (0, 1e10), (1e-5, 1e10), (1e3, 1e20)]:
        d = pnms.decoherence_metric(grad_s, t)
        assert 0.0 <= d <= 1.0

def test_decoherence_unity_at_t0():
    assert pnms.decoherence_metric(0, 0) == 1.0
    assert pnms.decoherence_metric(1e5, 0) == 1.0

def test_bh_entropy_solar_mass():
    M_SUN = 1.989e30
    s = pnms.bh_entropy(M_SUN)
    # Should be ~10^77 k_B
    assert 1e76 < s / pnms.K_B < 1e78


# ── Uncovered conversion functions ───────────────────────────────────────────

def test_roundtrip_warpticks():
    t = pnms.WARPTICK  # one WarpTick in SI seconds
    assert abs(pnms.from_warpticks(pnms.to_warpticks(t)) - t) / t < 1e-10

def test_roundtrip_plajoules():
    e = 1e20  # J
    assert abs(pnms.from_plajoules(pnms.to_plajoules(e)) - e) / e < 1e-10

def test_roundtrip_plakilograms():
    m = 1.0  # kg
    assert abs(pnms.from_plakilograms(pnms.to_plakilograms(m)) - m) / m < 1e-10

def test_to_warpticks_one_hubble_time():
    hubble_s = 13.8e9 * 365.25 * 24 * 3600
    wt = pnms.to_warpticks(hubble_s)
    assert 0.5 < wt < 2.0  # roughly 1 WarpTick

def test_to_plajoules_one_planck_energy():
    pj = pnms.to_plajoules(pnms.E_P)
    assert abs(pj - 1e-9) / 1e-9 < 0.01  # E_p / PLAJOULE = 1e9/1e9 = 1e-9

def test_to_plakilograms_one_kg():
    pk = pnms.to_plakilograms(1.0)
    assert 0.01 < pk < 100.0  # 1 kg is a small fraction of Plakilogram


# ── l_eff edge cases ─────────────────────────────────────────────────────────

def test_l_eff_at_c_returns_lambda_p():
    assert pnms.l_eff(pnms.C) == pnms.LAMBDA_P

def test_l_eff_above_c_returns_lambda_p():
    assert pnms.l_eff(2 * pnms.C) == pnms.LAMBDA_P

def test_l_eff_at_rest_returns_l0():
    assert abs(pnms.l_eff(0.0) - pnms.PLAMETER) < 1e-30


# ── psi_factor: zero l0 hits inf branch ──────────────────────────────────────

def test_psi_factor_zero_l0_returns_inf():
    result = pnms.psi_factor(0.0, l0=0.0)
    assert result == float('inf')


# ── f_collapse ───────────────────────────────────────────────────────────────

def test_f_collapse_below_threshold_nonzero():
    # v >= C → l_eff = LAMBDA_P < LAMBDA_P is False, but at v just below C l_eff → 0
    # Use l0 = LAMBDA_P / 2 so that l_eff(0) = l0 < LAMBDA_P → theta = 1
    result = pnms.f_collapse(0.0, lambda_cosmo=0.0, r=0.0, l0=pnms.LAMBDA_P / 2)
    assert result > 0.0

def test_f_collapse_above_threshold_zero():
    # l0 >> LAMBDA_P → l_eff(0) >> LAMBDA_P → theta = 0 → result = 0
    result = pnms.f_collapse(0.0, lambda_cosmo=0.0, r=0.0, l0=pnms.PLAMETER)
    assert result == 0.0

def test_f_collapse_cosmological_suppression():
    # Large lambda_cosmo * r suppresses the result
    r1 = pnms.f_collapse(0.0, 0.0, 0.0, l0=pnms.LAMBDA_P / 2)
    r2 = pnms.f_collapse(0.0, 1.0, 100.0, l0=pnms.LAMBDA_P / 2)
    assert r2 < r1


# ── warp_velocity ─────────────────────────────────────────────────────────────

def test_warp_velocity_at_zero_curvature():
    v = pnms.warp_velocity(0.0)
    assert abs(v - pnms.C) < 1.0  # exp(0) = 1 → v = C

def test_warp_velocity_increases_with_curvature():
    v_low = pnms.warp_velocity(1.0)
    v_high = pnms.warp_velocity(100.0)
    assert v_high > v_low > pnms.C
