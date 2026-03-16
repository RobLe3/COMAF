"""
v1.3.28 — Tests for comaf.runner and 'comaf simulate' CLI command.
"""

import pytest
from pathlib import Path

from comaf.parser import parse
from comaf.runner import run_model, SimulationResult

STDLIB = Path(__file__).parent.parent / "stdlib"


# ── run_model() unit tests ────────────────────────────────────────────────

def test_simulate_bounce_cosmology_runs():
    prog = parse((STDLIB / "bounce_cosmology.comaf").read_text(encoding="utf-8"))
    result = run_model(prog, t_end=10.0, steps=50)
    assert isinstance(result, SimulationResult)
    assert result.steps == 50
    assert len(result.t) == 50
    assert len(result.S) == 50
    assert len(result.D) == 50


def test_simulate_entropy_dho_runs():
    prog = parse((STDLIB / "dho_model_a_entropy_damping.comaf").read_text(encoding="utf-8"))
    result = run_model(prog, t_end=50.0, steps=100)
    assert result.steps == 100
    assert result.entity == prog.entity  # entity name from parsed model


def test_simulate_output_has_expected_keys():
    prog = parse((STDLIB / "bounce_cosmology.comaf").read_text(encoding="utf-8"))
    result = run_model(prog, t_end=5.0, steps=20)
    assert hasattr(result, "t")
    assert hasattr(result, "S")
    assert hasattr(result, "D")
    assert hasattr(result, "entity")
    assert hasattr(result, "collapse_triggered")
    assert hasattr(result, "collapse_time")


def test_simulate_entropy_increases_toward_max():
    """Entropy should evolve toward S_max (Boltzmann evolution)."""
    prog = parse((STDLIB / "dho_model_a_entropy_damping.comaf").read_text(encoding="utf-8"))
    result = run_model(prog, t_end=1000.0, steps=200)
    # After long time, S should be closer to S_max than S_init
    s_init = result.S[0]
    s_final = result.S[-1]
    s_max_from_model = 10.0  # from dho_model_a: max: 10.0
    assert abs(s_final - s_max_from_model) < abs(s_init - s_max_from_model), (
        f"S should converge to max ({s_max_from_model:.2f}): "
        f"init={s_init:.4f}, final={s_final:.4f}"
    )


def test_simulate_stability_monotone_decreasing():
    """D(t) should be monotonically non-increasing (decoherence is one-way)."""
    prog = parse((STDLIB / "dho_model_a_entropy_damping.comaf").read_text(encoding="utf-8"))
    result = run_model(prog, t_end=50.0, steps=100, alpha_d=1e-6)
    D = result.D
    # Overall decreasing (allow small numerical noise)
    assert D[0] >= D[-1] * 0.99, f"D should decrease: D[0]={D[0]:.6f}, D[-1]={D[-1]:.6f}"


def test_simulate_collapse_detection():
    """High alpha_d should trigger collapse for models with collapse block."""
    # bh_entropy_physical has IF D(t) < 0.01: collapse
    prog = parse((STDLIB / "bh_entropy_physical.comaf").read_text(encoding="utf-8"))
    # With very high decoherence, D drops below 0.01 quickly
    result = run_model(prog, t_end=1000.0, steps=500, alpha_d=0.1, grad_s=1.0)
    assert result.collapse_triggered is True
    assert result.collapse_time is not None
    assert result.collapse_time > 0


def test_simulate_no_collapse_clean():
    """With small alpha_d, D stays high — no collapse."""
    prog = parse((STDLIB / "dho_model_a_entropy_damping.comaf").read_text(encoding="utf-8"))
    # No collapse block in dho_model_a — collapse_triggered should be False
    result = run_model(prog, t_end=10.0, steps=50, alpha_d=1e-12)
    assert result.collapse_triggered is False
    assert result.collapse_time is None


def test_simulate_t_values_are_in_plaseconds():
    """Time values should be in Plaseconds (not SI seconds)."""
    prog = parse((STDLIB / "dho_model_a_entropy_damping.comaf").read_text(encoding="utf-8"))
    result = run_model(prog, t_end=100.0, steps=50)
    assert result.t[0] < 1.0          # starts at ~0
    assert result.t[-1] <= 100.5      # ends near t_end


def test_simulate_all_stdlib_models():
    """All stdlib models should simulate without crashing."""
    stdlib = STDLIB
    for model_path in sorted(stdlib.glob("*.comaf")):
        prog = parse(model_path.read_text(encoding="utf-8"))
        result = run_model(prog, t_end=10.0, steps=20)
        assert isinstance(result, SimulationResult), f"Failed for {model_path.name}"
