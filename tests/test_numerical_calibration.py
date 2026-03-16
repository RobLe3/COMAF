"""
v1.3.29 — Numerical calibration tests.
Verify that key physical quantities match expected values within tolerance.
"""

import math
import pytest
from pathlib import Path

from comaf.parser import parse
from comaf.runner import run_model
import comaf.pnms as pnms

STDLIB = Path(__file__).parent.parent / "stdlib"


# ── PNMS constant calibration ─────────────────────────────────────────────

def test_tc1_planck_time_value():
    """TC1: Planck time should be 5.391×10^-44 s (CODATA 2018)."""
    assert abs(pnms.T_P - 5.391247e-44) / 5.391247e-44 < 1e-4


def test_tc1_planck_length_value():
    """TC1: Planck length should be 1.616×10^-35 m (CODATA 2018)."""
    assert abs(pnms.LAMBDA_P - 1.616255e-35) / 1.616255e-35 < 1e-4


def test_tc1_planck_energy_value():
    """TC1: Planck energy should be ~1.956×10^9 J (CODATA 2018)."""
    assert abs(pnms.E_P - 1.9561e9) / 1.9561e9 < 1e-3


def test_tc1_plasecond_value():
    """Plasecond = 10^44 × t_p ≈ 5.39 s (verified: project_verified_numbers.md)."""
    # Verified value: 5.39 s (NOT 1 s — common misconception)
    assert abs(pnms.PLASECOND - 5.391) / 5.391 < 1e-3, (
        f"PLASECOND = {pnms.PLASECOND:.4f} s (expected ~5.391 s)"
    )


def test_tc1_plameter_value():
    """Plameter = 10^35 × λ_p ≈ 1.616 m (verified: project_verified_numbers.md)."""
    # Verified value: 1.616 m (NOT 1 m — common misconception)
    assert abs(pnms.PLAMETER - 1.616) / 1.616 < 1e-3, (
        f"PLAMETER = {pnms.PLAMETER:.4f} m (expected ~1.616 m)"
    )


def test_tc1_alpha_fsc_value():
    """Fine structure constant should be 1/137.036 (CODATA 2018)."""
    assert abs(pnms.ALPHA_FSC - 1/137.035999084) / (1/137.035999084) < 1e-6


# ── BH entropy calibration ────────────────────────────────────────────────

def test_bh_entropy_solar_mass_value():
    """S_BH(M_sun) ≈ 1.05×10^77 k_B (Bekenstein-Hawking, CODATA 2018).
    Verified value from project memory: 1.05×10^77 k_B nats.
    """
    M_SUN = 1.989e30  # kg
    s_bh_si = pnms.bh_entropy(M_SUN)
    s_bh_nats = s_bh_si / pnms.K_B   # in entropy ticks
    # Verified: 1.05e77 (from project_verified_numbers.md)
    assert abs(s_bh_nats - 1.05e77) / 1.05e77 < 0.5, (
        f"S_BH(M_sun) = {s_bh_nats:.3e} k_B (expected ~1.05×10^77 k_B)"
    )


# ── DHO entropy ring-down (TC5) ───────────────────────────────────────────

def test_tc5_entropy_ringdown_time_constant():
    """TC5: DHO entropy converges toward S_max within 5 time constants."""
    prog = parse((STDLIB / "dho_model_a_entropy_damping.comaf").read_text(encoding="utf-8"))
    tau = 10.0  # Plaseconds (from model: scale: 10.0 Plaseconds)
    result = run_model(prog, t_end=5 * tau, steps=200)
    # After 5 tau, S should be within 1% of S_max
    s_max = 10.0  # from model
    s_final = result.S[-1]
    assert abs(s_final - s_max) / s_max < 0.01, (
        f"After 5τ, S = {s_final:.4f} (expected ~{s_max:.1f}, within 1%)"
    )


def test_tc5_entropy_at_one_tau():
    """TC5: After one time constant, S(τ) ≈ S_init + (1 - 1/e) * (S_max - S_init)."""
    prog = parse((STDLIB / "dho_model_a_entropy_damping.comaf").read_text(encoding="utf-8"))
    tau = 10.0   # Plaseconds
    s_init = 1.0
    s_max = 10.0
    result = run_model(prog, t_end=tau, steps=1000)
    s_at_tau = result.S[-1]
    # Analytical: S(τ) = s_init * exp(-1) + s_max * (1 - exp(-1))
    expected = s_init * math.exp(-1) + s_max * (1 - math.exp(-1))
    assert abs(s_at_tau - expected) / expected < 0.01, (
        f"S(τ={tau}) = {s_at_tau:.4f}, expected {expected:.4f}"
    )


# ── Decoherence metric calibration ────────────────────────────────────────

def test_decoherence_metric_at_zero():
    """D(t=0) = 1 (full coherence)."""
    assert pnms.decoherence_metric(1.0, 0.0) == 1.0


def test_decoherence_metric_decreases():
    """D(t) should be monotonically decreasing for fixed grad_s > 0."""
    D_vals = [pnms.decoherence_metric(1.0, t) for t in [0, 0.1, 1.0, 10.0, 100.0]]
    for i in range(len(D_vals) - 1):
        assert D_vals[i] >= D_vals[i + 1]


def test_decoherence_metric_range():
    """D(t) should be in [0, 1] for all inputs."""
    for grad_s in [0.01, 0.1, 1.0, 10.0]:
        for t in [0, 1, 10, 100]:
            D = pnms.decoherence_metric(grad_s, t)
            assert 0.0 <= D <= 1.0, f"D({grad_s},{t}) = {D} out of [0,1]"


# ── F_collapse GRW calibration ────────────────────────────────────────────

def test_f_collapse_suppression_is_physically_reasonable():
    """(L_nucleon/lambda_p)^-3 should be ~4e-60 (Fix 2b key result)."""
    L_NUCLEON = 1e-15
    suppression = (L_NUCLEON / pnms.LAMBDA_P) ** -3
    assert 1e-62 < suppression < 1e-58, f"Suppression = {suppression:.3e}"


def test_f_collapse_rate_positive():
    """F_collapse rate should be non-negative."""
    rate = pnms.f_collapse_rate(pnms.E_P, 1.0, 0.0)
    assert rate >= 0.0
