"""Tests for COMAF-Lite lexer."""
import pytest
from comaf.lexer import tokenize, LexerError, TT_KEYWORD, TT_IDENT, TT_NUMBER, TT_STATE_REF


SIMPLE_HEADER = """
ENTITY: Universe
CYCLE: CPL-8
FRAME: t ∈ [0, 1 WarpTick]
UNITS: Planck
"""

def test_keywords_recognized():
    tokens = [t for t in tokenize(SIMPLE_HEADER) if t.type == TT_KEYWORD]
    values = [t.value for t in tokens]
    assert "ENTITY" in values
    assert "CYCLE" in values
    assert "FRAME" in values
    assert "UNITS" in values
    assert "Planck" in values

def test_state_ref_tokenized():
    source = "init: superposition[|0⟩, |1⟩]"
    tokens = tokenize(source)
    state_refs = [t.value for t in tokens if t.type == TT_STATE_REF]
    assert "|0⟩" in state_refs
    assert "|1⟩" in state_refs

def test_number_tokenized():
    source = "init: 1e88"
    tokens = tokenize(source)
    nums = [t.value for t in tokens if t.type == TT_NUMBER]
    assert "1e88" in nums

def test_ident_recognized():
    source = "STATE ψ:"
    tokens = tokenize(source)
    assert any(t.type == TT_KEYWORD and t.value == "STATE" for t in tokens)
