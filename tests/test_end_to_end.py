"""
End-to-end integration tests for COMAF-Lite.
Covers parsing, validation, and transpilation of stdlib models.
"""

import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
STDLIB_DIR = REPO_ROOT / "stdlib"

from comaf.parser import parse
from comaf.validator import validate
from comaf.transpilers.mathematica import transpile_mathematica
from comaf.transpilers.python import transpile_python

STDLIB_MODELS = sorted(STDLIB_DIR.glob("*.comaf"))

# ─────────────────────────────────────────────────────────────
# Bounce Cosmology
# ─────────────────────────────────────────────────────────────

def test_bounce_cosmology_parse():
    """Bounce cosmology model parses without exception."""
    src = (STDLIB_DIR / "bounce_cosmology.comaf").read_text()
    program = parse(src)
    assert program.entity


def test_bounce_cosmology_validate_zero_errors():
    """Bounce cosmology model validates with 0 errors (warnings ok)."""
    src = (STDLIB_DIR / "bounce_cosmology.comaf").read_text()
    program = parse(src)
    is_valid, issues = validate(program)
    errors = [i for i in issues if i.severity == "error"]
    assert is_valid, f"Unexpected errors: {errors}"
    assert len(errors) == 0


def test_bounce_cosmology_mathematica_has_whenEvent():
    """Mathematica transpile of bounce_cosmology contains WhenEvent."""
    src = (STDLIB_DIR / "bounce_cosmology.comaf").read_text()
    program = parse(src)
    wl_output = transpile_mathematica(program)
    assert "WhenEvent" in wl_output


# ─────────────────────────────────────────────────────────────
# Black Hole Formation
# ─────────────────────────────────────────────────────────────

def test_black_hole_parse():
    """Black hole formation model parses without exception."""
    src = (STDLIB_DIR / "black_hole_formation.comaf").read_text()
    program = parse(src)
    assert program.entity


def test_black_hole_validate():
    """Black hole formation model validates with 0 errors."""
    src = (STDLIB_DIR / "black_hole_formation.comaf").read_text()
    program = parse(src)
    is_valid, issues = validate(program)
    errors = [i for i in issues if i.severity == "error"]
    assert is_valid, f"Unexpected errors: {errors}"


# ─────────────────────────────────────────────────────────────
# Parser regression: multi-statement ON block (Fix 3)
# ─────────────────────────────────────────────────────────────

_MULTI_STMT_SOURCE = """\
ENTITY: TestEntity
CYCLE: test-cycle
FRAME: t0
UNITS: Planck

ENTROPY S:
  evolve Boltzmann {
    init: 0
    max: 1e77
    scale: 1 Plaseconds
  }

ON cycle.end:
  stmt_one = first_value
  stmt_two = second_value
"""


def test_multi_statement_transition_both_collected():
    """ON block with 2 statements collects both (regression for parser break bug)."""
    program = parse(_MULTI_STMT_SOURCE)
    from comaf.ast import TransitionBlockNode
    transitions = [b for b in program.blocks if isinstance(b, TransitionBlockNode)]
    assert len(transitions) == 1, f"Expected 1 transition block, got {len(transitions)}"
    trans = transitions[0]
    assert len(trans.statements) == 2, (
        f"Expected 2 statements, got {len(trans.statements)}: {trans.statements}"
    )


# ─────────────────────────────────────────────────────────────
# Python transpiler: solve_ivp scaffold (Fix 5)
# ─────────────────────────────────────────────────────────────

def test_python_transpiler_produces_solve_ivp():
    """Python transpile of bounce_cosmology contains solve_ivp."""
    src = (STDLIB_DIR / "bounce_cosmology.comaf").read_text()
    program = parse(src)
    py_output = transpile_python(program)
    assert "solve_ivp" in py_output


def test_bounce_cosmology_python_transpile_non_empty():
    """Python transpile produces a non-trivial script."""
    src = (STDLIB_DIR / "bounce_cosmology.comaf").read_text()
    program = parse(src)
    py_output = transpile_python(program)
    assert len(py_output) > 200
    assert "import numpy" in py_output


# ─────────────────────────────────────────────────────────────
# Validator: decoherence metric range (Fix 4)
# ─────────────────────────────────────────────────────────────

_STABILITY_OOR_SOURCE = """\
ENTITY: TestEntity
CYCLE: test-cycle
FRAME: t0
UNITS: Planck

STABILITY:
  metric D = 1.5
"""


def test_validator_decoherence_out_of_range():
    """Stability block with metric value 1.5 produces a validation error."""
    program = parse(_STABILITY_OOR_SOURCE)
    is_valid, issues = validate(program)
    errors = [i for i in issues if i.severity == "error"]
    assert not is_valid, "Expected validation to fail for D > 1"
    assert any("0,1" in e.message or "[0,1]" in e.message for e in errors), (
        f"Expected D(t) range error, got: {[e.message for e in errors]}"
    )


# ─────────────────────────────────────────────────────────────
# Round-trip: all stdlib models parse + transpile to Mathematica
# Reviewer suggestion: parametrized round-trip catches regressions
# ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("comaf_path", STDLIB_MODELS, ids=[p.name for p in STDLIB_MODELS])
def test_stdlib_mathematica_roundtrip(comaf_path):
    """Every stdlib model parses and transpiles to non-empty Mathematica output."""
    src = comaf_path.read_text()
    program = parse(src)
    wl_output = transpile_mathematica(program)
    assert wl_output, f"Empty Mathematica output for {comaf_path.name}"
    assert "PNMS Constants" in wl_output, (
        f"Missing PNMS header in Mathematica output for {comaf_path.name}"
    )
