"""Tests for COMAF-Lite parser."""
import pytest
from comaf.parser import parse, ParseError
from comaf.ast import ProgramNode, EntropyBlockNode, StateBlockNode


ENTROPY_MODEL = """
ENTITY: TestUniverse
CYCLE: CPL-1
FRAME: t ∈ [0, 1 WarpTick]
UNITS: Planck

ENTROPY S:
  evolve Boltzmann {
    init: 1e88
    max: 1e123
    scale: 1e10 Plaseconds
  }
"""

def test_parse_header():
    prog = parse(ENTROPY_MODEL)
    assert isinstance(prog, ProgramNode)
    assert prog.entity == "TestUniverse"
    assert prog.cycle == "CPL-1"
    assert prog.units == "Planck"

def test_parse_entropy_block():
    prog = parse(ENTROPY_MODEL)
    entropy_blocks = [b for b in prog.blocks if isinstance(b, EntropyBlockNode)]
    assert len(entropy_blocks) == 1
    b = entropy_blocks[0]
    assert b.name == "S"
    assert b.init == 1e88
    assert b.max_val == 1e123
    assert b.scale == 1e10
