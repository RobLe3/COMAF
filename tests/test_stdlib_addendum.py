"""
v1.3.23 — Tests for addendum stdlib models:
  - neutron_star_curvature.comaf (CURVATURE + ENTROPY)
  - photon_emission.comaf (CHARGE + POWER + EMIT)
"""

import pytest
from pathlib import Path

from comaf.parser import parse
from comaf.ast import PhysicsQuantityNode, EntropyBlockNode, EmitBlockNode
from comaf.transpilers.mathematica import transpile_mathematica
from comaf.transpilers.python import transpile_python
from comaf.validator import validate_structured

STDLIB = Path(__file__).parent.parent / "stdlib"


# ── neutron_star_curvature.comaf ───────────────────────────────────────────

def test_neutron_star_parseable():
    prog = parse((STDLIB / "neutron_star_curvature.comaf").read_text(encoding="utf-8"))
    assert prog.entity == "NeutronStar"


def test_neutron_star_has_curvature_block():
    prog = parse((STDLIB / "neutron_star_curvature.comaf").read_text(encoding="utf-8"))
    curv = next(
        (b for b in prog.blocks
         if isinstance(b, PhysicsQuantityNode) and b.keyword == "CURVATURE"),
        None,
    )
    assert curv is not None
    assert curv.name == "R_ns"
    assert "4.2" in curv.expression
    assert curv.unit == "RicciBits"


def test_neutron_star_validates():
    prog = parse((STDLIB / "neutron_star_curvature.comaf").read_text(encoding="utf-8"))
    result = validate_structured(prog)
    errors = [e for e in result.issues if e.severity == "error"]
    assert errors == [], f"Unexpected errors: {[e.message for e in errors]}"


def test_neutron_star_wolfram_transpile():
    prog = parse((STDLIB / "neutron_star_curvature.comaf").read_text(encoding="utf-8"))
    wl = transpile_mathematica(prog)
    assert "CURVATURE" in wl
    assert "R_ns[t_]" in wl


def test_neutron_star_python_transpile():
    prog = parse((STDLIB / "neutron_star_curvature.comaf").read_text(encoding="utf-8"))
    py = transpile_python(prog)
    assert "def curvature_R_ns" in py


# ── photon_emission.comaf ─────────────────────────────────────────────────

def test_photon_emission_parseable():
    prog = parse((STDLIB / "photon_emission.comaf").read_text(encoding="utf-8"))
    assert prog.entity == "HawkingEmitter"
    assert prog.cycle == "CPL-7"


def test_photon_emission_has_charge_and_power():
    prog = parse((STDLIB / "photon_emission.comaf").read_text(encoding="utf-8"))
    qty_blocks = [b for b in prog.blocks if isinstance(b, PhysicsQuantityNode)]
    keywords = {b.keyword for b in qty_blocks}
    assert "CHARGE" in keywords
    assert "POWER" in keywords


def test_photon_emission_has_emit_block():
    prog = parse((STDLIB / "photon_emission.comaf").read_text(encoding="utf-8"))
    emit = next((b for b in prog.blocks if isinstance(b, EmitBlockNode)), None)
    assert emit is not None
    assert "D" in emit.condition and "t" in emit.condition  # parser spaces: "D ( t ) < 0.01"


def test_photon_emission_entropy_init():
    prog = parse((STDLIB / "photon_emission.comaf").read_text(encoding="utf-8"))
    entropy = next((b for b in prog.blocks if isinstance(b, EntropyBlockNode)), None)
    assert entropy is not None
    # S_BH ≈ 10^77 k_B (solar-mass BH Bekenstein-Hawking entropy)
    assert 1e76 < entropy.init < 1e78


def test_photon_emission_validates():
    prog = parse((STDLIB / "photon_emission.comaf").read_text(encoding="utf-8"))
    result = validate_structured(prog)
    errors = [e for e in result.issues if e.severity == "error"]
    assert errors == [], f"Unexpected errors: {[e.message for e in errors]}"


def test_photon_emission_wolfram_transpile():
    prog = parse((STDLIB / "photon_emission.comaf").read_text(encoding="utf-8"))
    wl = transpile_mathematica(prog)
    assert "CHARGE" in wl
    assert "POWER" in wl
    assert "emitQ" in wl


def test_photon_emission_python_transpile():
    prog = parse((STDLIB / "photon_emission.comaf").read_text(encoding="utf-8"))
    py = transpile_python(prog)
    assert "def charge_q_eff" in py
    assert "def power_P_hawking" in py
