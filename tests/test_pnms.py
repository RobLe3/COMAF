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
