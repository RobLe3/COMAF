"""
v1.3.19 — Tests for DimensionalChecker and ScopeChecker.
"""

import pytest
from comaf.parser import parse
from comaf.validator import (
    DimensionalChecker,
    ScopeChecker,
    validate_structured,
    ValidationResult,
)
from comaf.ast import ProgramNode

MINIMAL_HEADER = """\
ENTITY: TestEntity
CYCLE: CPL-1
FRAME: t ∈ [0, 1 WarpTick]
UNITS: Planck
"""


# ── DimensionalChecker ────────────────────────────────────────────────────────

def test_dimensional_check_entropy_plaseconds_ok():
    """ENTROPY with Plaseconds scale_unit should produce no dimensional errors."""
    src = MINIMAL_HEADER + """
ENTROPY S:
  evolve Boltzmann {
    init: 1e120
    max: 1e121
    scale: 1e9 Plaseconds
  }
"""
    prog = parse(src)
    checker = DimensionalChecker(prog)
    issues = checker.check()
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


def test_dimensional_check_entropy_warptick_ok():
    """ENTROPY with WarpTick scale_unit should be fine."""
    src = MINIMAL_HEADER + """
ENTROPY S:
  evolve Boltzmann {
    init: 1e120
    max: 1e121
    scale: 1.0 WarpTick
  }
"""
    prog = parse(src)
    checker = DimensionalChecker(prog)
    issues = checker.check()
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


def test_dimensional_check_entropy_wrong_unit_warns():
    """ENTROPY with unrecognized unit should produce a dimensional warning."""
    # The parser stores scale_unit from the UNIT token after the number.
    # We test indirectly via validate_structured with a model that has a
    # known-bad unit. We'll manipulate the AST directly.
    from comaf.ast import EntropyBlockNode, ProgramNode
    prog = ProgramNode(
        model_name=None,
        entity="Test", cycle="CPL-1", frame="t", units="Planck",
        blocks=[
            EntropyBlockNode(
                name="S", init=1e10, max_val=1e20, scale=1.0,
                scale_unit="meters",  # wrong dimension
            )
        ],
    )
    checker = DimensionalChecker(prog)
    issues = checker.check()
    assert len(issues) > 0
    assert any("meters" in i.message for i in issues)


def test_dimensional_check_stability_out_of_range_literal():
    """STABILITY literal value outside [0,1] should be a dimensional error."""
    from comaf.ast import StabilityBlockNode, ProgramNode
    prog = ProgramNode(
        model_name=None,
        entity="Test", cycle="CPL-1", frame="t", units="Planck",
        blocks=[
            StabilityBlockNode(metric_name="D", expression="2.5"),
        ],
    )
    checker = DimensionalChecker(prog)
    issues = checker.check()
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) > 0
    assert any("2.5" in i.message for i in errors)


def test_dimensional_check_stability_formula_ok():
    """STABILITY with a formula expression should not produce dimensional errors."""
    from comaf.ast import StabilityBlockNode, ProgramNode
    prog = ProgramNode(
        model_name=None,
        entity="Test", cycle="CPL-1", frame="t", units="Planck",
        blocks=[
            StabilityBlockNode(metric_name="D", expression="exp(-|∇S(t)| · t)"),
        ],
    )
    checker = DimensionalChecker(prog)
    issues = checker.check()
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


def test_dimensional_check_passes_clean_stdlib_model():
    """A standard stdlib model should pass dimensional checks with no errors."""
    from pathlib import Path
    path = Path(__file__).parent.parent / "stdlib" / "bounce_cosmology.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    checker = DimensionalChecker(prog)
    issues = checker.check()
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


# ── ScopeChecker ─────────────────────────────────────────────────────────────

def test_scope_check_defined_variable_in_if():
    """IF condition referencing a defined ENTROPY variable should be clean."""
    from comaf.ast import EntropyBlockNode, CollapseBlockNode, ProgramNode
    prog = ProgramNode(
        model_name=None,
        entity="Test", cycle="CPL-1", frame="t", units="Planck",
        blocks=[
            EntropyBlockNode(name="S", init=1e10, max_val=1e20, scale=1.0, scale_unit="Plaseconds"),
            CollapseBlockNode(condition="R > R_max", energy="E_jump", resolution=None, decoherence=None),
        ],
    )
    checker = ScopeChecker(prog)
    issues = checker.check()
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


def test_scope_check_d_t_without_stability_warns():
    """IF condition with D(t) but no STABILITY block should produce a warning."""
    from comaf.ast import CollapseBlockNode, ProgramNode
    prog = ProgramNode(
        model_name=None,
        entity="Test", cycle="CPL-1", frame="t", units="Planck",
        blocks=[
            CollapseBlockNode(
                condition="D(t) < 0.01",
                energy="E_jump", resolution=None, decoherence=None,
            ),
        ],
    )
    checker = ScopeChecker(prog)
    issues = checker.check()
    # D is not in _defined (no STABILITY block) — should warn
    assert len(issues) > 0
    assert any("D(t)" in i.message for i in issues)


def test_scope_check_d_t_with_stability_ok():
    """IF condition with D(t) and a STABILITY block should be clean."""
    from comaf.ast import StabilityBlockNode, CollapseBlockNode, ProgramNode
    prog = ProgramNode(
        model_name=None,
        entity="Test", cycle="CPL-1", frame="t", units="Planck",
        blocks=[
            StabilityBlockNode(metric_name="D", expression="exp(-t)"),
            CollapseBlockNode(
                condition="D(t) < 0.01",
                energy="E_jump", resolution=None, decoherence=None,
            ),
        ],
    )
    checker = ScopeChecker(prog)
    issues = checker.check()
    assert not any("D(t)" in i.message for i in issues)


# ── validate_structured integration with dimensional level ────────────────────

def test_validation_result_dimensional_level_set():
    """validate_structured with check_dimensional=True sets dimensional_valid."""
    from pathlib import Path
    path = Path(__file__).parent.parent / "stdlib" / "bounce_cosmology.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    result = validate_structured(prog, check_dimensional=True)
    # dimensional_valid should be set (not None)
    assert result.dimensional_valid is not None


def test_validation_result_dimensional_off_gives_none():
    """validate_structured with check_dimensional=False leaves dimensional_valid=None."""
    from pathlib import Path
    path = Path(__file__).parent.parent / "stdlib" / "bounce_cosmology.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    result = validate_structured(prog, check_dimensional=False)
    assert result.dimensional_valid is None


def test_validation_result_has_all_five_levels_with_dimensional():
    """With both checks enabled, to_dict shows 5 levels, dimensional is set."""
    from pathlib import Path
    path = Path(__file__).parent.parent / "stdlib" / "bounce_cosmology.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    result = validate_structured(prog, check_schema=True, check_dimensional=True)
    d = result.to_dict()
    assert d["syntax"] in ("ok", "fail")
    assert d["schema"] in ("ok", "fail", "not_checked")
    assert d["semantic"] in ("ok", "fail")
    assert d["dimensional"] in ("ok", "fail")
    assert d["solver"] == "not_checked"


def test_dimensional_check_clean_stdlib_all_pass():
    """All stdlib models should have dimensional_valid=True."""
    from pathlib import Path
    stdlib = Path(__file__).parent.parent / "stdlib"
    models = [p.name.replace(".comaf", "") for p in stdlib.glob("*.comaf")]
    for model_name in models:
        prog = parse((stdlib / f"{model_name}.comaf").read_text(encoding="utf-8"))
        result = validate_structured(prog, check_dimensional=True)
        assert result.dimensional_valid is True, (
            f"{model_name} failed dimensional check: "
            f"{[e.message for e in result.issues if e.severity == 'error']}"
        )
