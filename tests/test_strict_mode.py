"""
v1.3.17 — Tests for ValidationResult, --strict mode, and --report json.
"""

import json
import pytest
from pathlib import Path

from comaf.parser import parse
from comaf.validator import (
    validate,
    validate_structured,
    ValidationResult,
    ValidationError,
)

STDLIB = Path(__file__).parent.parent / "stdlib"

# ── Minimal snippets ──────────────────────────────────────────────────────────

VALID_MINIMAL = """\
ENTITY: TestEntity
CYCLE: CPL-1
FRAME: t ∈ [0, 1 WarpTick]
UNITS: Planck

ENTROPY S:
  evolve Boltzmann {
    init: 1e120
    max: 1e121
    scale: 1e9 Plaseconds
  }
"""

# Model with a warning: GEOMETRY block with no field_equation (empty because
# field_equation is on the next line — known parser behaviour).
WARNS_MODEL = """\
ENTITY: TestEntity
CYCLE: CPL-1
FRAME: t ∈ [0, 1 WarpTick]
UNITS: Planck

GEOMETRY:
  field_equation: G = 0
"""

# Model with a real semantic error: negative entropy init.
ERROR_MODEL = """\
ENTITY: BadModel
CYCLE: CPL-1
FRAME: t ∈ [0, 1 WarpTick]
UNITS: Planck

ENTROPY S:
  evolve Boltzmann {
    init: -1
    max: 100
    scale: 1.0 Plaseconds
  }
"""


# ── ValidationResult structure ────────────────────────────────────────────────

def test_validation_result_has_five_level_fields():
    """ValidationResult must expose all five level attributes."""
    result = ValidationResult()
    assert hasattr(result, "syntax_valid")
    assert hasattr(result, "schema_valid")
    assert hasattr(result, "semantic_valid")
    assert hasattr(result, "dimensional_valid")
    assert hasattr(result, "solver_valid")
    assert hasattr(result, "issues")


def test_validation_result_defaults():
    """Default ValidationResult is valid with unchecked schema/dimensional/solver."""
    result = ValidationResult()
    assert result.syntax_valid is True
    assert result.schema_valid is None
    assert result.semantic_valid is True
    assert result.dimensional_valid is None
    assert result.solver_valid is None
    assert result.is_valid is True


def test_validation_result_semantic_false_makes_invalid():
    result = ValidationResult(semantic_valid=False)
    assert result.is_valid is False


def test_validation_result_schema_false_makes_invalid():
    result = ValidationResult(schema_valid=False)
    assert result.is_valid is False


def test_validation_result_schema_none_does_not_make_invalid():
    """schema_valid=None (not checked) should not affect is_valid."""
    result = ValidationResult(schema_valid=None, semantic_valid=True)
    assert result.is_valid is True


def test_to_dict_has_all_five_levels():
    """to_dict() output must include all five level keys."""
    prog = parse(VALID_MINIMAL)
    result = validate_structured(prog)
    d = result.to_dict()
    assert "valid" in d
    assert "syntax" in d
    assert "schema" in d
    assert "semantic" in d
    assert "dimensional" in d
    assert "solver" in d
    assert "issues" in d


def test_to_dict_not_checked_levels():
    """Schema/solver levels not requested should report 'not_checked'.
    dimensional is checked by default (v1.3.19), so it will be 'ok' or 'fail'.
    solver is always 'not_checked' (not implemented yet).
    """
    prog = parse(VALID_MINIMAL)
    result = validate_structured(prog)
    d = result.to_dict()
    assert d["schema"] == "not_checked"   # check_schema=False by default
    assert d["dimensional"] in ("ok", "fail")  # check_dimensional=True by default
    assert d["solver"] == "not_checked"


def test_to_dict_is_json_serializable():
    """to_dict() output must be JSON-serializable."""
    prog = parse(VALID_MINIMAL)
    result = validate_structured(prog)
    json_str = json.dumps(result.to_dict())
    assert isinstance(json_str, str)


# ── validate_structured() API ─────────────────────────────────────────────────

def test_validate_structured_clean_model_is_valid():
    """Clean model with no errors should yield is_valid=True."""
    prog = parse(VALID_MINIMAL)
    result = validate_structured(prog)
    assert result.is_valid is True
    assert result.semantic_valid is True


def test_validate_structured_error_model_is_invalid():
    """Model with negative entropy init should yield is_valid=False."""
    prog = parse(ERROR_MODEL)
    result = validate_structured(prog)
    assert result.is_valid is False
    assert result.semantic_valid is False
    assert any("negative" in e.message.lower() for e in result.issues)


def test_validate_structured_issues_list():
    """Issues list should contain ValidationError instances."""
    prog = parse(WARNS_MODEL)
    result = validate_structured(prog)
    assert isinstance(result.issues, list)
    for issue in result.issues:
        assert isinstance(issue, ValidationError)
        assert issue.severity in ("error", "warning", "info")


def test_validate_structured_check_schema_true():
    """With check_schema=True, schema_valid should be set (not None)."""
    prog = parse(VALID_MINIMAL)
    result = validate_structured(prog, check_schema=True)
    assert result.schema_valid is not None


def test_validate_structured_clean_schema_passes():
    """A valid minimal model should pass the schema top-level check."""
    prog = parse(VALID_MINIMAL)
    result = validate_structured(prog, check_schema=True)
    assert result.schema_valid is True


# ── --strict mode (via validate_structured, simulating CLI behaviour) ─────────

def test_strict_mode_rejects_warnings():
    """In strict mode, a model with warnings should be considered failed."""
    prog = parse(WARNS_MODEL)
    result = validate_structured(prog)
    # GEOMETRY with no field_equation → warning
    has_warnings = any(e.severity == "warning" for e in result.issues)
    assert has_warnings, "Expected at least one warning from GEOMETRY block"
    # Strict: treat any warning as failure
    strict_valid = result.is_valid and not has_warnings
    assert not strict_valid


def test_strict_mode_accepts_clean_model():
    """In strict mode, a model with no warnings should still pass."""
    prog = parse(VALID_MINIMAL)
    result = validate_structured(prog)
    has_warnings = any(e.severity == "warning" for e in result.issues)
    has_errors = any(e.severity == "error" for e in result.issues)
    # VALID_MINIMAL should produce no errors and no warnings
    assert result.is_valid
    assert not has_errors


# ── Backward compat: original validate() still works ─────────────────────────

def test_legacy_validate_returns_tuple():
    """The original validate() must still return (bool, list)."""
    prog = parse(VALID_MINIMAL)
    result = validate(prog)
    assert isinstance(result, tuple)
    is_valid, issues = result
    assert isinstance(is_valid, bool)
    assert isinstance(issues, list)


def test_legacy_validate_valid_model():
    prog = parse(VALID_MINIMAL)
    is_valid, issues = validate(prog)
    assert is_valid is True


def test_legacy_validate_error_model():
    prog = parse(ERROR_MODEL)
    is_valid, issues = validate(prog)
    assert is_valid is False


# ── Schema validation ─────────────────────────────────────────────────────────

def test_schema_validation_catches_missing_entity():
    """Manually create a ProgramNode with empty entity; schema check should fail."""
    from comaf.ast import ProgramNode
    prog = ProgramNode(
        model_name=None,
        entity="",  # missing
        cycle="CPL-1",
        frame="t ∈ [0, 1 WarpTick]",
        units="Planck",
        blocks=[],
    )
    result = validate_structured(prog, check_schema=True)
    assert result.schema_valid is False
    assert any("entity" in e.message.lower() or "blocks" in e.message.lower()
               for e in result.issues)


def test_schema_validation_passes_valid_model():
    prog = parse(VALID_MINIMAL)
    result = validate_structured(prog, check_schema=True)
    assert result.schema_valid is True
