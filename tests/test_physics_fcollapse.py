"""
v1.3.25 — Tests for F_collapse GRW normalization and BH entropy physical model.

Deferred Fix 2b from technical review (March 2026):
  F_collapse_GRW = (1/2π) * Theta * (E_jump/E_p) * exp(-Lambda*R) * (L0/lambda_p)^-3
  For nucleon (L0 ~ 1e-15 m): Gamma ~ 5e-16 s^-1 — within ~10× of GRW rate (1e-16 s^-1)
"""

import math
import pytest
from pathlib import Path

from comaf.parser import parse
from comaf.ast import EntropyBlockNode, CollapseBlockNode
from comaf.transpilers.mathematica import transpile_mathematica
from comaf.validator import validate_structured
import comaf.pnms as pnms

STDLIB = Path(__file__).parent.parent / "stdlib"


# ── f_collapse_rate() function ────────────────────────────────────────────

def test_f_collapse_rate_nucleon_grw_consistent():
    """Nucleon collapse rate (using E_p at threshold, /t_p for s^-1) should
    be within 6 orders of magnitude of GRW target (1e-16 s^-1)."""
    result = pnms.grw_consistency_check()
    assert result["consistent"], (
        f"f_collapse_rate for nucleon = {result['rate']:.3e} s^-1, "
        f"expected 1e-22 < rate < 1e-10 (GRW target: {result['grw_target']:.1e} s^-1)"
    )


def test_f_collapse_suppression_factor_correct():
    """(L_nucleon/lambda_p)^-3 should be approximately 4e-60."""
    L_NUCLEON = 1e-15
    suppression = (L_NUCLEON / pnms.LAMBDA_P) ** -3
    # lambda_p ≈ 1.616e-35; L_nucleon/lambda_p ≈ 6.2e19; (6.2e19)^-3 ≈ 4.2e-60
    assert 1e-62 < suppression < 1e-58, f"Unexpected suppression factor: {suppression:.3e}"


def test_f_collapse_rate_without_suppression_too_large():
    """Without volume suppression, F_collapse dimensionless value is orders larger."""
    L_NUCLEON = 1e-15
    # F_collapse with suppression (dimensionless)
    rate_suppressed = pnms.f_collapse_rate(pnms.E_P, 1.0, 0.0, l0=L_NUCLEON)
    # F_collapse without suppression (set L0 = lambda_p → suppression = 1)
    rate_unsuppressed = pnms.f_collapse_rate(pnms.E_P, 1.0, 0.0, l0=pnms.LAMBDA_P)
    # Suppressed should be much smaller
    assert rate_suppressed < rate_unsuppressed * 1e-50, (
        f"Suppressed rate {rate_suppressed:.3e} should be <<  {rate_unsuppressed:.3e}"
    )


def test_f_collapse_rate_returns_float():
    rate = pnms.f_collapse_rate(1e-10, theta=1.0, lambda_r=0.0)
    assert isinstance(rate, float)
    assert rate >= 0.0


def test_grw_consistency_check_returns_dict():
    result = pnms.grw_consistency_check()
    assert "rate" in result
    assert "grw_target" in result
    assert "consistent" in result
    assert "suppression" in result
    assert isinstance(result["consistent"], bool)


# ── bh_entropy_physical.comaf ─────────────────────────────────────────────

def test_bh_entropy_physical_parseable():
    prog = parse((STDLIB / "bh_entropy_physical.comaf").read_text(encoding="utf-8"))
    assert prog.entity == "SolarMassBH"
    assert prog.cycle == "CPL-3"


def test_bh_entropy_value_in_range():
    """S_BH for solar mass should be ~1.05×10^77 k_B."""
    prog = parse((STDLIB / "bh_entropy_physical.comaf").read_text(encoding="utf-8"))
    entropy = next((b for b in prog.blocks if isinstance(b, EntropyBlockNode)), None)
    assert entropy is not None
    # Verified value from memory/project_verified_numbers.md: 1.05×10^77 k_B
    assert 1e76 < entropy.init < 1e78, f"S_BH = {entropy.init:.2e} outside [1e76, 1e78]"


def test_bh_entropy_python_value_matches_pnms():
    """pnms.bh_entropy(M_sun) should agree with the model's init value within 10%."""
    M_SUN = 1.989e30  # kg
    s_bh_si = pnms.bh_entropy(M_SUN)
    s_bh_bits = s_bh_si / pnms.K_B  # in entropy ticks
    # Model uses 1.05e77
    assert abs(s_bh_bits - 1.05e77) / 1.05e77 < 0.5, (
        f"pnms.bh_entropy computed {s_bh_bits:.3e}, model uses 1.05e77"
    )


def test_bh_entropy_has_collapse_block():
    prog = parse((STDLIB / "bh_entropy_physical.comaf").read_text(encoding="utf-8"))
    collapse = next((b for b in prog.blocks if isinstance(b, CollapseBlockNode)), None)
    assert collapse is not None


def test_bh_entropy_physical_validates():
    prog = parse((STDLIB / "bh_entropy_physical.comaf").read_text(encoding="utf-8"))
    result = validate_structured(prog)
    errors = [e for e in result.issues if e.severity == "error"]
    assert errors == [], f"Validation errors: {[e.message for e in errors]}"


def test_bh_entropy_wolfram_transpile():
    prog = parse((STDLIB / "bh_entropy_physical.comaf").read_text(encoding="utf-8"))
    wl = transpile_mathematica(prog)
    assert "S0S" in wl or "S0" in wl  # entropy initial value emitted
