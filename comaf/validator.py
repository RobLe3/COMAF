"""
COMAF-Lite Semantic Validator
Checks unit consistency, variable scope, and physical constraint warnings.
"""

from typing import List, Tuple
from .ast import (ProgramNode, StateBlockNode, EntropyBlockNode,
                  GeometryBlockNode, StabilityBlockNode, CollapseBlockNode,
                  WarpBlockNode, EmitBlockNode, TransitionBlockNode, Node)
from . import pnms


@dataclass_like = None  # avoid import issue — use plain class


class ValidationError:
    def __init__(self, message: str, severity: str = "error"):
        self.message = message
        self.severity = severity  # "error" | "warning" | "info"

    def __repr__(self):
        return f"[{self.severity.upper()}] {self.message}"


class Validator:
    def __init__(self, program: ProgramNode):
        self.program = program
        self.errors: List[ValidationError] = []
        self.defined_names: set = set()

    def validate(self) -> List[ValidationError]:
        self.errors.clear()
        self._check_units()
        self._check_header()
        for block in self.program.blocks:
            self._check_block(block)
        return self.errors

    def _add(self, msg: str, severity: str = "error"):
        self.errors.append(ValidationError(msg, severity))

    def _check_header(self):
        if not self.program.entity:
            self._add("ENTITY is required")
        if not self.program.cycle:
            self._add("CYCLE is required")
        if not self.program.frame:
            self._add("FRAME is required")
        if self.program.units not in ("Planck", "SI", "Custom"):
            self._add(f"UNITS must be Planck, SI, or Custom (got {self.program.units!r})", "warning")

    def _check_units(self):
        if self.program.units == "SI":
            self._add("SI units are supported but PNMS (Planck) units are recommended for QULT-C modeling", "warning")

    def _check_block(self, block: Node):
        if isinstance(block, StateBlockNode):
            self.defined_names.add(block.name)
            if not block.hamiltonian:
                self._add(f"STATE block '{block.name}' has no hamiltonian", "warning")

        elif isinstance(block, EntropyBlockNode):
            self.defined_names.add(block.name)
            if block.init < 0:
                self._add(f"ENTROPY block '{block.name}': init entropy cannot be negative")
            if block.max_val < block.init:
                self._add(f"ENTROPY block '{block.name}': max < init (entropy cannot decrease in isolation)", "warning")
            if block.scale <= 0:
                self._add(f"ENTROPY block '{block.name}': scale (timescale τ) must be positive")
            if block.scale_unit not in pnms.UNIT_SI_VALUES and block.scale_unit not in ("Plaseconds", "Plasecond", "WarpTicks", "WarpTick"):
                self._add(f"ENTROPY block: unrecognized time unit {block.scale_unit!r}", "warning")

        elif isinstance(block, CollapseBlockNode):
            if not block.condition:
                self._add("COLLAPSE block has no condition")
            if block.energy and "E_p" in block.condition:
                pass  # E_p reference is fine
            self._add(
                "COLLAPSE block detected: ensure D(t) check is included for physical validity",
                "info"
            )

        elif isinstance(block, WarpBlockNode):
            self._add(
                "WARP block detected: v_warp = c·exp(κR) can exceed c — ensure D(t) safety condition is set",
                "warning"
            )

        elif isinstance(block, GeometryBlockNode):
            if not block.field_equation:
                self._add("GEOMETRY block has no field_equation", "warning")

        elif isinstance(block, StabilityBlockNode):
            self.defined_names.add(block.metric_name)


def validate(program: ProgramNode) -> Tuple[bool, List[ValidationError]]:
    """
    Validate a parsed COMAF-Lite program.
    Returns (is_valid, list_of_errors).
    is_valid = True if no errors (warnings are acceptable).
    """
    validator = Validator(program)
    issues = validator.validate()
    has_errors = any(e.severity == "error" for e in issues)
    return not has_errors, issues
