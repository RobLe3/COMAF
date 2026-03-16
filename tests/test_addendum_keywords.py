"""
v1.3.22 — Tests for COMAF × PNMS addendum keywords:
  FORCE, POWER, PRESSURE, CURVATURE, CHARGE, ENTROPY_UNIT, UNCERTAINTY
"""

import pytest
from pathlib import Path

from comaf.parser import parse, ParseError
from comaf.ast import PhysicsQuantityNode, EntropyBlockNode, StabilityBlockNode
from comaf.transpilers.mathematica import transpile_mathematica
from comaf.transpilers.python import transpile_python
from comaf.validator import validate_structured

STDLIB = Path(__file__).parent.parent / "stdlib"

HEADER = """\
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


def _first_qty(prog, keyword):
    return next(
        (b for b in prog.blocks
         if isinstance(b, PhysicsQuantityNode) and b.keyword == keyword),
        None,
    )


# ── Individual keyword parsing ─────────────────────────────────────────────

def test_force_block_parses():
    src = HEADER + "FORCE F_grav: beta * R PlaNewtons\n"
    prog = parse(src)
    node = _first_qty(prog, "FORCE")
    assert node is not None
    assert node.name == "F_grav"
    assert "beta" in node.expression
    assert node.unit == "PlaNewtons"


def test_power_block_parses():
    src = HEADER + "POWER P_emit: hbar * c^6 PlaWatts\n"
    prog = parse(src)
    node = _first_qty(prog, "POWER")
    assert node is not None
    assert node.name == "P_emit"
    assert node.unit == "PlaWatts"


def test_pressure_block_parses():
    src = HEADER + "PRESSURE P_vac: hbar * c PlaPascals\n"
    prog = parse(src)
    node = _first_qty(prog, "PRESSURE")
    assert node is not None
    assert node.unit == "PlaPascals"


def test_curvature_block_parses():
    src = HEADER + "CURVATURE R_ns: 4.2e42 RicciBits\n"
    prog = parse(src)
    node = _first_qty(prog, "CURVATURE")
    assert node is not None
    assert node.name == "R_ns"
    assert "4.2" in node.expression
    assert node.unit == "RicciBits"


def test_charge_block_parses():
    src = HEADER + "CHARGE q_eff: alpha * e_p\n"
    prog = parse(src)
    node = _first_qty(prog, "CHARGE")
    assert node is not None
    assert node.name == "q_eff"


def test_entropy_unit_block_parses():
    src = HEADER + "ENTROPY_UNIT S_tick: k_B\n"
    prog = parse(src)
    node = _first_qty(prog, "ENTROPY_UNIT")
    assert node is not None
    assert node.name == "S_tick"


def test_uncertainty_block_parses():
    src = HEADER + "UNCERTAINTY delta_E: hbar / 2\n"
    prog = parse(src)
    node = _first_qty(prog, "UNCERTAINTY")
    assert node is not None
    assert node.name == "delta_E"
    assert "hbar" in node.expression


# ── All addendum types in one model ────────────────────────────────────────

def test_all_addendum_in_one_model():
    prog = parse((STDLIB / "addendum_units_demo.comaf").read_text(encoding="utf-8"))
    qty_blocks = [b for b in prog.blocks if isinstance(b, PhysicsQuantityNode)]
    keywords_found = {b.keyword for b in qty_blocks}
    expected = {"FORCE", "POWER", "PRESSURE", "CURVATURE", "CHARGE", "ENTROPY_UNIT", "UNCERTAINTY"}
    assert expected == keywords_found, f"Missing addendum keywords: {expected - keywords_found}"


def test_addendum_demo_block_count():
    prog = parse((STDLIB / "addendum_units_demo.comaf").read_text(encoding="utf-8"))
    qty_blocks = [b for b in prog.blocks if isinstance(b, PhysicsQuantityNode)]
    assert len(qty_blocks) == 7


# ── Transpiler coverage ───────────────────────────────────────────────────

def test_addendum_wolfram_transpile():
    prog = parse((STDLIB / "addendum_units_demo.comaf").read_text(encoding="utf-8"))
    wl = transpile_mathematica(prog)
    assert "FORCE" in wl
    assert "POWER" in wl
    assert "CURVATURE" in wl
    assert "F_grav[t_]" in wl
    assert "P_emit[t_]" in wl


def test_addendum_python_transpile():
    prog = parse((STDLIB / "addendum_units_demo.comaf").read_text(encoding="utf-8"))
    py = transpile_python(prog)
    assert "def force_F_grav" in py
    assert "def power_P_emit" in py
    assert "def curvature_R_ns" in py
    assert "def entropy_unit_S_tick" in py


def test_addendum_python_transpile_numpy_cos():
    """cos(...) in expression should become np.cos(...) in Python output."""
    src = HEADER + "UNCERTAINTY delta_E: hbar * cos(theta) / 2\n"
    prog = parse(src)
    py = transpile_python(prog)
    assert "np.cos(" in py


def test_addendum_python_transpile_caret_to_power():
    """^ in expression should become ** in Python output."""
    src = HEADER + "FORCE F_test: R^2 * beta PlaNewtons\n"
    prog = parse(src)
    py = transpile_python(prog)
    assert "**" in py


# ── Serializer round-trip ─────────────────────────────────────────────────

def test_addendum_serializer_roundtrip():
    from comaf.serializer import ast_to_dict
    from comaf.deserializer import dict_to_ast

    prog = parse((STDLIB / "addendum_units_demo.comaf").read_text(encoding="utf-8"))
    d = ast_to_dict(prog)
    prog2 = dict_to_ast(d)

    qty1 = [b for b in prog.blocks if isinstance(b, PhysicsQuantityNode)]
    qty2 = [b for b in prog2.blocks if isinstance(b, PhysicsQuantityNode)]
    assert len(qty1) == len(qty2)
    for b1, b2 in zip(qty1, qty2):
        assert b1.keyword == b2.keyword
        assert b1.name == b2.name
        assert b1.expression == b2.expression


def test_addendum_dict_has_physics_quantity_type():
    from comaf.serializer import ast_to_dict

    prog = parse((STDLIB / "addendum_units_demo.comaf").read_text(encoding="utf-8"))
    d = ast_to_dict(prog)
    types = {b["type"] for b in d["blocks"]}
    assert "PHYSICS_QUANTITY" in types


# ── Validator ─────────────────────────────────────────────────────────────

def test_addendum_demo_validates():
    prog = parse((STDLIB / "addendum_units_demo.comaf").read_text(encoding="utf-8"))
    result = validate_structured(prog)
    errors = [e for e in result.issues if e.severity == "error"]
    assert len(errors) == 0, f"Unexpected errors: {[e.message for e in errors]}"


# ── Negative test ─────────────────────────────────────────────────────────

def test_addendum_keyword_not_silently_skipped():
    """FORCE block must appear as PhysicsQuantityNode, not be silently dropped."""
    src = HEADER + "FORCE F_test: R * beta\n"
    prog = parse(src)
    pq_blocks = [b for b in prog.blocks if isinstance(b, PhysicsQuantityNode)]
    assert len(pq_blocks) == 1
    assert pq_blocks[0].keyword == "FORCE"
