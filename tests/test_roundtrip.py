"""
v1.3.18 — AST round-trip and transpiler determinism tests.

For each stdlib model:
  1. Parse .comaf → ProgramNode
  2. Serialize AST → dict (ast_to_dict)
  3. Deserialize dict → ProgramNode (dict_to_ast)
  4. Re-serialize → dict
  5. Assert both dicts are equal (round-trip fidelity)
  6. Transpile original AST → .wl
  7. Transpile deserialized AST → .wl
  8. Assert both .wl outputs are identical (transpiler determinism)
"""

import json
import pytest
from pathlib import Path

from comaf.parser import parse
from comaf.serializer import ast_to_dict
from comaf.deserializer import dict_to_ast, DeserializationError
from comaf.transpilers.mathematica import transpile_mathematica
from comaf.transpilers.python import transpile_python

STDLIB = Path(__file__).parent.parent / "stdlib"

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


@pytest.fixture(params=STDLIB_MODELS)
def stdlib_program(request):
    model_name = request.param
    path = STDLIB / f"{model_name}.comaf"
    return parse(path.read_text(encoding="utf-8"))


# ── Serializer unit tests ──────────────────────────────────────────────────────

def test_ast_to_dict_has_required_keys():
    """ast_to_dict output must include all required top-level keys."""
    path = STDLIB / "bounce_cosmology.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    d = ast_to_dict(prog)
    for key in ("__version__", "entity", "cycle", "frame", "units", "blocks"):
        assert key in d, f"Missing key: {key}"


def test_ast_to_dict_preserves_header():
    """Serialized dict must preserve entity/cycle/frame/units verbatim."""
    path = STDLIB / "bounce_cosmology.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    d = ast_to_dict(prog)
    assert d["entity"] == "BouncingUniverse"
    assert d["cycle"] == "CPL-n"
    assert d["units"] == "Planck"


def test_ast_to_dict_blocks_have_type():
    """Every serialized block must have a 'type' key."""
    path = STDLIB / "bounce_cosmology.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    d = ast_to_dict(prog)
    for block in d["blocks"]:
        assert "type" in block, f"Block missing 'type': {block}"


def test_ast_to_dict_is_json_serializable():
    """ast_to_dict output must be JSON-serializable without error."""
    path = STDLIB / "bounce_cosmology.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    d = ast_to_dict(prog)
    json_str = json.dumps(d, ensure_ascii=False)
    assert isinstance(json_str, str)
    assert len(json_str) > 0


# ── Deserializer unit tests ───────────────────────────────────────────────────

def test_dict_to_ast_produces_program_node():
    """dict_to_ast must return a ProgramNode."""
    from comaf.ast import ProgramNode
    path = STDLIB / "bounce_cosmology.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    d = ast_to_dict(prog)
    prog2 = dict_to_ast(d)
    assert isinstance(prog2, ProgramNode)


def test_dict_to_ast_preserves_header():
    """Deserialized ProgramNode must have the same header fields."""
    path = STDLIB / "bounce_cosmology.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    prog2 = dict_to_ast(ast_to_dict(prog))
    assert prog2.entity == prog.entity
    assert prog2.cycle == prog.cycle
    assert prog2.frame == prog.frame
    assert prog2.units == prog.units


def test_dict_to_ast_missing_entity_raises():
    """dict_to_ast must raise DeserializationError if 'entity' is missing."""
    data = {"cycle": "CPL-1", "frame": "t", "units": "Planck", "blocks": []}
    with pytest.raises(DeserializationError, match="entity"):
        dict_to_ast(data)


def test_dict_to_ast_unknown_block_type_raises():
    """dict_to_ast must raise DeserializationError for unknown block type."""
    data = {
        "entity": "E", "cycle": "CPL-1", "frame": "t", "units": "Planck",
        "blocks": [{"type": "UNKNOWN_BLOCK_TYPE"}],
    }
    with pytest.raises(DeserializationError, match="Unknown block type"):
        dict_to_ast(data)


# ── Round-trip fidelity tests ─────────────────────────────────────────────────

@pytest.mark.parametrize("model_name", STDLIB_MODELS)
def test_ast_json_roundtrip(model_name):
    """Parse → serialize → deserialize → re-serialize must produce identical dicts."""
    path = STDLIB / f"{model_name}.comaf"
    prog = parse(path.read_text(encoding="utf-8"))

    dict1 = ast_to_dict(prog)
    prog2 = dict_to_ast(dict1)
    dict2 = ast_to_dict(prog2)

    # Remove __version__ for comparison (it's an artefact, not AST content)
    dict1.pop("__version__", None)
    dict2.pop("__version__", None)

    assert dict1 == dict2, (
        f"Round-trip mismatch for {model_name}.\n"
        f"dict1: {json.dumps(dict1, indent=2, ensure_ascii=False)}\n"
        f"dict2: {json.dumps(dict2, indent=2, ensure_ascii=False)}"
    )


@pytest.mark.parametrize("model_name", STDLIB_MODELS)
def test_transpiler_mathematica_deterministic(model_name):
    """Transpile original and deserialized AST → .wl must give identical output."""
    path = STDLIB / f"{model_name}.comaf"
    prog = parse(path.read_text(encoding="utf-8"))

    wl1 = transpile_mathematica(prog)
    prog2 = dict_to_ast(ast_to_dict(prog))
    wl2 = transpile_mathematica(prog2)

    assert wl1 == wl2, (
        f"Mathematica transpiler is not deterministic for {model_name}.\n"
        f"Output 1 (len={len(wl1)}):\n{wl1[:500]}\n\n"
        f"Output 2 (len={len(wl2)}):\n{wl2[:500]}"
    )


@pytest.mark.parametrize("model_name", STDLIB_MODELS)
def test_transpiler_python_deterministic(model_name):
    """Transpile original and deserialized AST → .py must give identical output."""
    path = STDLIB / f"{model_name}.comaf"
    prog = parse(path.read_text(encoding="utf-8"))

    py1 = transpile_python(prog)
    prog2 = dict_to_ast(ast_to_dict(prog))
    py2 = transpile_python(prog2)

    assert py1 == py2, (
        f"Python transpiler is not deterministic for {model_name}."
    )


# ── Block count preservation ───────────────────────────────────────────────────

@pytest.mark.parametrize("model_name", STDLIB_MODELS)
def test_roundtrip_preserves_block_count(model_name):
    """Round-trip must preserve the number of blocks."""
    path = STDLIB / f"{model_name}.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    prog2 = dict_to_ast(ast_to_dict(prog))
    assert len(prog2.blocks) == len(prog.blocks)


# ── Schema conformance (top-level) ────────────────────────────────────────────

def test_schema_conformance_bounce():
    """bounce_cosmology round-tripped dict should pass top-level schema check."""
    from comaf.validator import validate_structured
    path = STDLIB / "bounce_cosmology.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    result = validate_structured(prog, check_schema=True)
    assert result.schema_valid is True


@pytest.mark.parametrize("model_name", STDLIB_MODELS)
def test_schema_conformance_all_stdlib(model_name):
    """All stdlib models should pass the top-level schema check."""
    from comaf.validator import validate_structured
    path = STDLIB / f"{model_name}.comaf"
    prog = parse(path.read_text(encoding="utf-8"))
    result = validate_structured(prog, check_schema=True)
    assert result.schema_valid is True, (
        f"{model_name} failed top-level schema check: "
        f"{[e.message for e in result.issues if 'Schema' in e.message]}"
    )
