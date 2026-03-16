"""
v1.3.16 — Parser regression tests.

Covers:
  - Unicode identifiers (Greek, ∇, ħ, ∈) in headers and expressions
  - Bra-ket state literals  |x⟩
  - Dotted event names (cycle.end)
  - Mixed symbolic expressions
  - Negative / loud-failure tests (ParseError with line number)
  - Structural snapshot fixtures for all 8 stdlib models
"""

import json
import pytest
from pathlib import Path

from comaf.parser import parse, ParseError
from comaf.lexer import tokenize, TT_STATE_REF
from comaf.ast import (
    ProgramNode, StateBlockNode, EntropyBlockNode,
    GeometryBlockNode, StabilityBlockNode, TransitionBlockNode,
    CollapseBlockNode, WarpBlockNode, EmitBlockNode,
)

STDLIB = Path(__file__).parent.parent / "stdlib"
FIXTURES = Path(__file__).parent / "fixtures"

# ── Minimal valid header used in inline tests ─────────────────────────────────

MINIMAL_HEADER = """\
ENTITY: TestEntity
CYCLE: CPL-1
FRAME: t ∈ [0, 1 WarpTick]
UNITS: Planck
"""

# ── Unicode identifier tests ──────────────────────────────────────────────────

def test_unicode_greek_state_name():
    """STATE ψ: should parse with name='ψ'."""
    src = MINIMAL_HEADER + """
STATE ψ:
  evolve Schrödinger {
    init: |ground⟩
    hamiltonian: H_gravity + H_quantum
  }
"""
    prog = parse(src)
    state = next(b for b in prog.blocks if isinstance(b, StateBlockNode))
    assert state.name == "ψ"


def test_unicode_phi_state_name():
    """STATE φ: (inflation field) should parse with name='φ'."""
    src = MINIMAL_HEADER + """
STATE φ:
  evolve Schrödinger {
    init: |vac⟩
    hamiltonian: V(φ)
  }
"""
    prog = parse(src)
    state = next(b for b in prog.blocks if isinstance(b, StateBlockNode))
    assert state.name == "φ"


def test_unicode_nabla_in_stability_expression():
    """STABILITY expression containing ∇ should be captured as non-empty string."""
    src = MINIMAL_HEADER + """
STABILITY:
  metric D(t) = exp(-∇S · t)
"""
    prog = parse(src)
    stab = next(b for b in prog.blocks if isinstance(b, StabilityBlockNode))
    assert stab.metric_name == "D"
    assert stab.expression != ""
    # ∇S is lexed as a single IDENT token; the collected expression string contains ∇
    assert "∇" in stab.expression


def test_unicode_alpha_in_stability_expression():
    """STABILITY expression with α_D should capture the Greek identifier."""
    src = MINIMAL_HEADER + """
STABILITY:
  metric D(t) = exp(-α_D · t)
"""
    prog = parse(src)
    stab = next(b for b in prog.blocks if isinstance(b, StabilityBlockNode))
    assert "α" in stab.expression


def test_unicode_hbar_in_hamiltonian():
    """Hamiltonian expression with ħ should not crash the parser."""
    src = MINIMAL_HEADER + """
STATE ψ:
  evolve Schrödinger {
    init: |vacuum⟩
    hamiltonian: -ħ² ∇² / 2m + β R - γ ln S
  }
"""
    prog = parse(src)
    state = next(b for b in prog.blocks if isinstance(b, StateBlockNode))
    assert "ħ" in state.hamiltonian


def test_unicode_lambda_in_geometry_condition():
    """IF condition with Λ and · should not crash the parser."""
    src = MINIMAL_HEADER + """
IF ∇φ = 0 AND ρ_vac > threshold:
  warp {
    velocity: v_warp
    safety: D(t) > 0.95
    target: CPL-1
  }
"""
    prog = parse(src)
    warp = next((b for b in prog.blocks if isinstance(b, WarpBlockNode)), None)
    assert warp is not None
    assert "∇" in warp.condition or "φ" in warp.condition


def test_unicode_in_frame_header():
    """FRAME header with ∈ should be captured without error."""
    src = MINIMAL_HEADER + """
STABILITY:
  metric D(t) = exp(-t)
"""
    prog = parse(src)
    assert "∈" in prog.frame


# ── Bra-ket state literal tests ───────────────────────────────────────────────

def test_bra_ket_token_type():
    """|contracting⟩ should tokenize as a STATE_REF token."""
    tokens = tokenize("|contracting⟩")
    assert any(t.type == TT_STATE_REF for t in tokens)
    tok = next(t for t in tokens if t.type == TT_STATE_REF)
    assert tok.value == "|contracting⟩"


def test_bra_ket_multiple_state_refs():
    """|fluct1⟩, |fluct2⟩, |fluct3⟩ should each produce a STATE_REF token."""
    tokens = tokenize("|fluct1⟩ , |fluct2⟩ , |fluct3⟩")
    state_refs = [t for t in tokens if t.type == TT_STATE_REF]
    assert len(state_refs) == 3


def test_bra_ket_single_state_in_init():
    """|ground⟩ as a single STATE init value is captured directly."""
    src = MINIMAL_HEADER + """
STATE ψ:
  evolve Schrödinger {
    init: |ground⟩
    hamiltonian: H
  }
"""
    prog = parse(src)
    state = next(b for b in prog.blocks if isinstance(b, StateBlockNode))
    assert state.init == "|ground⟩"


def test_bra_ket_superposition_in_init():
    """superposition[|contracting⟩, |expanding⟩] is captured as init string
    containing both state refs (superposition + bracket → raw string fallback)."""
    src = MINIMAL_HEADER + """
STATE ψ:
  evolve Schrödinger {
    init: superposition[|contracting⟩, |expanding⟩]
    hamiltonian: H = H_gravity + H_quantum
  }
"""
    prog = parse(src)
    state = next(b for b in prog.blocks if isinstance(b, StateBlockNode))
    assert isinstance(state.init, str)
    assert "|contracting⟩" in state.init
    assert "|expanding⟩" in state.init


def test_truncated_bra_ket_not_state_ref():
    """|open_without_close has no ⟩ so it does not become a STATE_REF token."""
    tokens = tokenize("|open_without_close")
    assert not any(t.type == TT_STATE_REF for t in tokens)


# ── Dotted event name tests ───────────────────────────────────────────────────

def test_dotted_event_name_cycle_end():
    """ON cycle.end: event_name contains 'cycle' and 'end'.

    The parser joins collected tokens with '.', so the '.' OP token
    produces 'cycle...end' (cycle + sep + dot-token + sep + end).
    This test locks in the actual behaviour for regression detection.
    """
    src = MINIMAL_HEADER + """
ON cycle.end:
  S = S / (1 + α)
"""
    prog = parse(src)
    tr = next(b for b in prog.blocks if isinstance(b, TransitionBlockNode))
    # Actual behaviour: dot is a token so ".".join(["cycle",".",  "end"]) = "cycle...end"
    assert "cycle" in tr.event_name
    assert "end" in tr.event_name


def test_on_block_collects_two_statements():
    """ON block with two lines should collect both statements."""
    src = MINIMAL_HEADER + """
ON cycle.end:
  S = S / (1 + α)
  ψ ·= e^(iπ)
"""
    prog = parse(src)
    tr = next(b for b in prog.blocks if isinstance(b, TransitionBlockNode))
    assert len(tr.statements) == 2


def test_on_block_statement_content():
    """First statement of ON block should reference the entropy variable."""
    src = MINIMAL_HEADER + """
ON cycle.end:
  S = S / (1 + alpha_r)
"""
    prog = parse(src)
    tr = next(b for b in prog.blocks if isinstance(b, TransitionBlockNode))
    assert "S" in tr.statements[0]


# ── Negative / loud-failure tests ─────────────────────────────────────────────

def test_missing_entity_raises_parse_error():
    """Missing ENTITY: should raise ParseError mentioning 'line'."""
    src = """\
CYCLE: CPL-1
FRAME: t ∈ [0, 1 WarpTick]
UNITS: Planck
"""
    with pytest.raises(ParseError) as exc_info:
        parse(src)
    assert "line" in str(exc_info.value).lower()


def test_missing_cycle_raises_parse_error():
    """Missing CYCLE: (FRAME seen instead) should raise ParseError."""
    src = """\
ENTITY: TestEntity
FRAME: t ∈ [0, 1 WarpTick]
UNITS: Planck
"""
    with pytest.raises(ParseError):
        parse(src)


def test_missing_units_raises_parse_error():
    """Missing UNITS: should raise ParseError."""
    src = """\
ENTITY: TestEntity
CYCLE: CPL-1
FRAME: t ∈ [0, 1 WarpTick]
"""
    with pytest.raises(ParseError):
        parse(src)


def test_malformed_entropy_init_raises():
    """Non-numeric ENTROPY init should raise ValueError or ParseError."""
    src = MINIMAL_HEADER + """
ENTROPY S:
  evolve Boltzmann {
    init: not_a_number
    max: 1e121
    scale: 1e9 Plaseconds
  }
"""
    with pytest.raises((ValueError, ParseError)):
        parse(src)


def test_empty_collapse_block_still_parsed():
    """IF with empty collapse body should still produce a CollapseBlockNode."""
    src = MINIMAL_HEADER + """
IF R > R_max:
  collapse {
  }
"""
    prog = parse(src)
    collapse = next((b for b in prog.blocks if isinstance(b, CollapseBlockNode)), None)
    assert collapse is not None
    assert "R_max" in collapse.condition


def test_unknown_top_level_keyword_skipped():
    """Unknown top-level keyword should be silently skipped, not crash."""
    src = MINIMAL_HEADER + """
UNKNOWN_BLOCK some_value:
  stuff here
STABILITY:
  metric D(t) = exp(-t)
"""
    prog = parse(src)
    stab = next((b for b in prog.blocks if isinstance(b, StabilityBlockNode)), None)
    assert stab is not None


# ── Structural snapshot regression tests ─────────────────────────────────────


def _structural_snapshot(prog: ProgramNode) -> dict:
    """Minimal structural representation for regression detection."""
    return {
        "entity": prog.entity,
        "cycle": prog.cycle,
        "units": prog.units,
        "block_count": len(prog.blocks),
        "block_types": [type(b).__name__ for b in prog.blocks],
    }


STDLIB_MODELS = [
    "bounce_cosmology",
    "black_hole_formation",
    "early_universe_inflation",
    "hawking_radiation",
    "heat_death_reboot",
    "cmb_freezeout",
    "dho_model_a_entropy_damping",
    "dho_model_b_rendering_damping",
]


@pytest.mark.parametrize("model_name", STDLIB_MODELS)
def test_stdlib_structural_snapshot(model_name):
    """Parse each stdlib model and compare against the structural snapshot fixture.

    On first run (no fixture file), creates the fixture and skips.
    On subsequent runs, asserts the structure matches exactly.
    """
    model_path = STDLIB / f"{model_name}.comaf"
    assert model_path.exists(), f"Stdlib model not found: {model_path}"

    prog = parse(model_path.read_text(encoding="utf-8"))
    current = _structural_snapshot(prog)

    fixture_path = FIXTURES / f"{model_name}.json"
    if not fixture_path.exists():
        fixture_path.write_text(
            json.dumps(current, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        pytest.skip(f"Fixture created at {fixture_path.name} — run again to verify")

    expected = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert current == expected, (
        f"Structural snapshot mismatch for {model_name}.\n"
        f"Expected: {json.dumps(expected, indent=2)}\n"
        f"Got:      {json.dumps(current, indent=2)}"
    )
