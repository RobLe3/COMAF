"""
Unit tests for COMAF-Lite semantic validator physics guards.
Tests physics constraints independently of the parser.
"""

import pytest
from comaf.ast import ProgramNode, EntropyBlockNode, StabilityBlockNode
from comaf.validator import validate


def _minimal_program(*blocks):
    """Helper: minimal valid ProgramNode with the given blocks."""
    return ProgramNode(
        model_name=None,
        entity="TestEntity",
        cycle="test-cycle",
        frame="t0",
        units="Planck",
        blocks=list(blocks),
    )


# ─────────────────────────────────────────────────────────────
# Entropy block
# ─────────────────────────────────────────────────────────────

def test_entropy_negative_init_is_error():
    """ENTROPY block with init < 0 must produce an error."""
    block = EntropyBlockNode(
        name="S", init=-1.0, max_val=100.0, scale=1.0, scale_unit="Plaseconds"
    )
    program = _minimal_program(block)
    is_valid, issues = validate(program)
    errors = [i for i in issues if i.severity == "error"]
    assert not is_valid
    assert any("negative" in e.message.lower() or "init" in e.message.lower()
               for e in errors), f"Expected init-negative error, got: {[e.message for e in errors]}"


def test_entropy_max_less_than_init_is_warning():
    """ENTROPY block with max < init must produce a warning (not error)."""
    block = EntropyBlockNode(
        name="S", init=100.0, max_val=0.0, scale=1.0, scale_unit="Plaseconds"
    )
    program = _minimal_program(block)
    is_valid, issues = validate(program)
    warnings = [i for i in issues if i.severity == "warning"]
    # Should be valid (warning only), and have the max<init warning
    assert any("max" in w.message.lower() or "init" in w.message.lower()
               for w in warnings), f"Expected max<init warning, got: {[w.message for w in warnings]}"


# ─────────────────────────────────────────────────────────────
# Header validation
# ─────────────────────────────────────────────────────────────

def test_missing_entity_is_error():
    """ProgramNode with empty entity must produce an ENTITY-required error."""
    program = ProgramNode(
        model_name=None,
        entity="",           # empty → missing
        cycle="test-cycle",
        frame="t0",
        units="Planck",
        blocks=[],
    )
    is_valid, issues = validate(program)
    errors = [i for i in issues if i.severity == "error"]
    assert not is_valid
    assert any("ENTITY" in e.message for e in errors), (
        f"Expected ENTITY error, got: {[e.message for e in errors]}"
    )
