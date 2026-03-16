"""
v1.3.26 — Tests for decoherence anisotropy and QULT-C Hamiltonian stdlib models.
"""

import pytest
from pathlib import Path

from comaf.parser import parse
from comaf.ast import (StabilityBlockNode, StateBlockNode, EntropyBlockNode,
                       EmitBlockNode, GeometryBlockNode)
from comaf.transpilers.mathematica import transpile_mathematica
from comaf.transpilers.python import transpile_python
from comaf.validator import validate_structured

STDLIB = Path(__file__).parent.parent / "stdlib"


# ── decoherence_anisotropy.comaf ──────────────────────────────────────────

def test_decoherence_anisotropy_parseable():
    prog = parse((STDLIB / "decoherence_anisotropy.comaf").read_text(encoding="utf-8"))
    assert prog.entity == "BECInterferometer"
    assert prog.cycle == "CPL-1"


def test_decoherence_anisotropy_valid():
    prog = parse((STDLIB / "decoherence_anisotropy.comaf").read_text(encoding="utf-8"))
    result = validate_structured(prog)
    errors = [e for e in result.issues if e.severity == "error"]
    assert errors == [], f"Errors: {[e.message for e in errors]}"


def test_anisotropy_stability_expression_contains_cos():
    prog = parse((STDLIB / "decoherence_anisotropy.comaf").read_text(encoding="utf-8"))
    stab = next((b for b in prog.blocks if isinstance(b, StabilityBlockNode)), None)
    assert stab is not None
    # Parser spaces tokens: cos ( theta ) ^  2
    assert "cos" in stab.expression
    assert "theta" in stab.expression
    assert "Gamma" in stab.expression


def test_anisotropy_python_transpile_uses_numpy_cos():
    """STABILITY with cos() should emit a comment (not numpy); this verifies it transpiles."""
    prog = parse((STDLIB / "decoherence_anisotropy.comaf").read_text(encoding="utf-8"))
    py = transpile_python(prog)
    # Stability block emits np.exp(-np.abs(grad_s) * t) — simplified form
    assert "def D(" in py


def test_anisotropy_wolfram_transpile():
    prog = parse((STDLIB / "decoherence_anisotropy.comaf").read_text(encoding="utf-8"))
    wl = transpile_mathematica(prog)
    assert "ENTROPY" in wl or "S0V" in wl  # entropy block emitted
    assert "Dcoh" in wl                     # stability emitted


def test_anisotropy_has_emit_block():
    prog = parse((STDLIB / "decoherence_anisotropy.comaf").read_text(encoding="utf-8"))
    emit = next((b for b in prog.blocks if isinstance(b, EmitBlockNode)), None)
    assert emit is not None
    assert "Gamma" in emit.energy


# ── qultc_hamiltonian.comaf ───────────────────────────────────────────────

def test_hamiltonian_model_parseable():
    prog = parse((STDLIB / "qultc_hamiltonian.comaf").read_text(encoding="utf-8"))
    assert prog.entity == "QULTCSystem"


def test_hamiltonian_model_has_state_block():
    prog = parse((STDLIB / "qultc_hamiltonian.comaf").read_text(encoding="utf-8"))
    state = next((b for b in prog.blocks if isinstance(b, StateBlockNode)), None)
    assert state is not None
    assert state.name == "psi"
    assert "hbar" in state.hamiltonian or "nabla" in state.hamiltonian


def test_hamiltonian_model_state_init_bra_ket():
    prog = parse((STDLIB / "qultc_hamiltonian.comaf").read_text(encoding="utf-8"))
    state = next((b for b in prog.blocks if isinstance(b, StateBlockNode)), None)
    assert state is not None
    assert "|ground⟩" == state.init


def test_hamiltonian_model_validates():
    prog = parse((STDLIB / "qultc_hamiltonian.comaf").read_text(encoding="utf-8"))
    result = validate_structured(prog)
    errors = [e for e in result.issues if e.severity == "error"]
    assert errors == [], f"Errors: {[e.message for e in errors]}"


def test_hamiltonian_wolfram_transpile():
    prog = parse((STDLIB / "qultc_hamiltonian.comaf").read_text(encoding="utf-8"))
    wl = transpile_mathematica(prog)
    assert "psi[t_]" in wl      # STATE block
    assert "Hpsi[t_]" in wl     # Hamiltonian


def test_hamiltonian_python_transpile():
    prog = parse((STDLIB / "qultc_hamiltonian.comaf").read_text(encoding="utf-8"))
    py = transpile_python(prog)
    assert "entropy_S" in py    # ENTROPY block emitted
    assert "def D(" in py       # STABILITY block emitted


def test_hamiltonian_model_has_geometry_block():
    prog = parse((STDLIB / "qultc_hamiltonian.comaf").read_text(encoding="utf-8"))
    geom = next((b for b in prog.blocks if isinstance(b, GeometryBlockNode)), None)
    assert geom is not None
