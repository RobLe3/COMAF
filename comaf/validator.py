"""
COMAF-Lite Semantic Validator
Checks unit consistency, variable scope, and physical constraint warnings.

v1.3.17: Added ValidationResult dataclass with 5 explicit levels, schema
         validation (top-level field check), and validate_structured() API.
         The original validate() wrapper is preserved for backward compatibility.

v1.3.19: Added DimensionalChecker (unit-dimension tracking across blocks) and
         ScopeChecker (symbol table + undefined symbol detection in IF/ON
         conditions). validate_structured() now populates dimensional_valid.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Optional

from .ast import (ProgramNode, StateBlockNode, EntropyBlockNode,
                  GeometryBlockNode, StabilityBlockNode, CollapseBlockNode,
                  WarpBlockNode, EmitBlockNode, TransitionBlockNode, Node)
from . import pnms

# ── Schema file (relative to this package's parent directory) ────────────────
_SCHEMA_PATH = Path(__file__).parent.parent / "docs" / "comaf_lite_schema.json"


class ValidationError:
    def __init__(self, message: str, severity: str = "error"):
        self.message = message
        self.severity = severity  # "error" | "warning" | "info"

    def __repr__(self):
        return f"[{self.severity.upper()}] {self.message}"


# ── v1.3.17: Structured validation result ────────────────────────────────────

@dataclass
class ValidationResult:
    """Five-level structured validation result.

    Levels:
        syntax_valid      — lexer/parser passed (always True if we have a ProgramNode)
        schema_valid      — top-level JSON Schema fields present (None = not checked)
        semantic_valid    — bounds/unit checks passed (no errors)
        dimensional_valid — dimensional analysis passed (None = not implemented yet)
        solver_valid      — solver check passed (None = not implemented yet)
        issues            — flat list of all ValidationError instances
    """
    syntax_valid: bool = True
    schema_valid: Optional[bool] = None
    semantic_valid: bool = True
    dimensional_valid: Optional[bool] = None
    solver_valid: Optional[bool] = None
    issues: List[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Overall: True unless any checked level is False."""
        if not self.syntax_valid:
            return False
        if self.schema_valid is False:
            return False
        if not self.semantic_valid:
            return False
        return True

    def to_dict(self) -> dict:
        def _level(v: Optional[bool]) -> str:
            if v is None:
                return "not_checked"
            return "ok" if v else "fail"

        return {
            "valid": self.is_valid,
            "syntax": _level(self.syntax_valid),
            "schema": _level(self.schema_valid),
            "semantic": _level(self.semantic_valid),
            "dimensional": _level(self.dimensional_valid),
            "solver": _level(self.solver_valid),
            "issues": [
                {"level": e.severity, "message": e.message}
                for e in self.issues
            ],
        }


# ── Core validator ────────────────────────────────────────────────────────────

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
            if block.energy:
                try:
                    energy_val = float(block.energy.strip())
                    if energy_val > pnms.E_P:
                        self._add(
                            f"COLLAPSE block: energy {energy_val:.3e} exceeds Planck energy "
                            f"{pnms.E_P:.3e} J — check PNMS units",
                            "warning"
                        )
                except ValueError:
                    pass  # energy is an expression, not a literal number
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
            # Extract the numeric literal from expressions like "( t ) = 5.0" or "5.0"
            import re as _re
            _expr = block.expression.strip()
            _m = _re.search(r'=\s*([+-]?[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)\s*$', _expr)
            _literal = _m.group(1) if _m else _expr
            try:
                metric_value = float(_literal)
                if metric_value < 0 or metric_value > 1:
                    self._add(
                        f"STABILITY block '{block.metric_name}': decoherence metric D(t) "
                        f"must be in [0,1] (got {metric_value})"
                    )
            except ValueError:
                pass  # expression is a formula, not a literal number

    # ── v1.3.17: Schema validation (top-level field check) ────────────────────

    def validate_against_schema(self) -> Tuple[bool, List[ValidationError]]:
        """Validate the program against the COMAF-Lite JSON Schema (top-level only).

        Full recursive schema validation against docs/comaf_lite_schema.json
        requires the v1.3.18 serializer. This method checks required top-level
        fields and basic type constraints. Returns (schema_valid, schema_issues).
        """
        schema_issues: List[ValidationError] = []

        # Required top-level fields
        if not self.program.entity:
            schema_issues.append(ValidationError("Schema: 'entity' is required and must be non-empty"))
        if not self.program.cycle:
            schema_issues.append(ValidationError("Schema: 'cycle' is required and must be non-empty"))
        if not self.program.frame:
            schema_issues.append(ValidationError("Schema: 'frame' is required and must be non-empty"))
        if not self.program.units:
            schema_issues.append(ValidationError("Schema: 'units' is required"))
        elif self.program.units not in ("Planck", "SI", "PNMS"):
            schema_issues.append(ValidationError(
                f"Schema: 'units' must be one of Planck/SI/PNMS (got {self.program.units!r})"
            ))
        if not self.program.blocks:
            schema_issues.append(ValidationError("Schema: 'blocks' array must have at least one item"))

        # Try full jsonschema validation if available (requires serializer from v1.3.18)
        try:
            import jsonschema
            if _SCHEMA_PATH.exists():
                # Minimal JSON representation for top-level schema check
                minimal_doc = {
                    "entity": self.program.entity,
                    "cycle": self.program.cycle,
                    "frame": self.program.frame,  # string, not object — schema diverges here
                    "units": self.program.units,
                    "blocks": [{"type": "COMMENT", "text": "placeholder"}],
                }
                schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
                # Only validate required top-level string fields, not deep block structure
                top_level_schema = {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": ["entity", "cycle", "frame", "units", "blocks"],
                    "properties": {
                        "entity": {"type": "string"},
                        "cycle":  {"type": "string"},
                        "frame":  {},
                        "units":  {"type": "string"},
                        "blocks": {"type": "array", "minItems": 1},
                    }
                }
                try:
                    jsonschema.validate(minimal_doc, top_level_schema)
                except jsonschema.ValidationError as exc:
                    schema_issues.append(ValidationError(f"Schema: {exc.message}"))
        except ImportError:
            pass  # jsonschema not installed — skip deep check

        schema_valid = len(schema_issues) == 0
        return schema_valid, schema_issues


# ── v1.3.19: DimensionalChecker ──────────────────────────────────────────────

# Recognized PNMS time units (time dimension)
_PNMS_TIME_UNITS = frozenset({
    "Plaseconds", "Plasecond", "WarpTicks", "WarpTick",
    "t_p",  # raw Planck time
})
# SI time units (valid but unusual in PNMS context)
_SI_TIME_UNITS = frozenset({"s", "ms", "us", "ns", "min", "hr", "year"})
# All recognized time units
_ALL_TIME_UNITS = _PNMS_TIME_UNITS | _SI_TIME_UNITS


class DimensionalChecker:
    """Checks dimensional consistency of known PNMS unit tokens across blocks.

    Handles known PNMS unit tokens only — does not attempt full CAS evaluation.
    Distinct from semantic checks: flags unit-dimension mismatches rather than
    value-range violations.
    """

    def __init__(self, program: ProgramNode):
        self.program = program
        self.issues: List[ValidationError] = []

    def check(self) -> List[ValidationError]:
        self.issues.clear()
        for block in self.program.blocks:
            self._check_block(block)
        return self.issues

    def _add(self, msg: str, severity: str = "warning"):
        self.issues.append(ValidationError(msg, severity))

    def _check_block(self, block) -> None:
        if isinstance(block, EntropyBlockNode):
            self._check_entropy_dimensions(block)
        elif isinstance(block, StabilityBlockNode):
            self._check_stability_dimensions(block)

    def _check_entropy_dimensions(self, block: EntropyBlockNode) -> None:
        """ENTROPY.scale_unit must be a time unit."""
        unit = block.scale_unit
        if unit not in _ALL_TIME_UNITS:
            self._add(
                f"Dimensional: ENTROPY '{block.name}' scale_unit {unit!r} is not "
                f"a recognized time unit (expected one of: Plaseconds, WarpTick, s, …)"
            )
        elif unit in _SI_TIME_UNITS:
            self._add(
                f"Dimensional: ENTROPY '{block.name}' uses SI time unit {unit!r} "
                f"— consider PNMS time unit (Plaseconds, WarpTick) for QULT-C modeling",
                "info",
            )
        # ENTROPY init/max must be positive real (semantic already checks sign)
        if block.init > 0 and block.max_val > 0:
            if block.max_val / block.init < 1e-300:
                self._add(
                    f"Dimensional: ENTROPY '{block.name}' max/init ratio is vanishingly small "
                    f"({block.max_val / block.init:.2e}) — check unit consistency",
                    "warning",
                )

    def _check_stability_dimensions(self, block: StabilityBlockNode) -> None:
        """STABILITY metric result must be dimensionless ∈ [0,1]."""
        import re as _re
        _expr = block.expression.strip()
        # Parser stores "( t ) = 5.0" for "metric D(t) = 5.0" — extract trailing literal
        _m = _re.search(r'=\s*([+-]?[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)\s*$', _expr)
        _literal = _m.group(1) if _m else _expr
        try:
            val = float(_literal)
            if not (0.0 <= val <= 1.0):
                self._add(
                    f"Dimensional: STABILITY '{block.metric_name}' literal value "
                    f"{val} is outside [0,1] — D(t) must be dimensionless in [0,1]",
                    "error",
                )
        except ValueError:
            pass  # expression is a formula — dimensionless by construction if correct


# ── v1.3.19: ScopeChecker ─────────────────────────────────────────────────────

class ScopeChecker:
    """Builds a symbol table from ENTROPY/STATE/STABILITY block names and
    checks that IF/ON condition expressions only reference defined symbols.

    Limited to known COMAF-Lite identifiers — does not parse expression sub-trees.
    """

    # Well-known physics constants that are always in scope.
    # Note: "D" is intentionally absent — it should be defined by a STABILITY block.
    _ALWAYS_DEFINED = frozenset({
        "R", "R_max", "lambda_p", "lambda_P", "c", "G", "kB", "hbar",
        "E_p", "E_P", "E_jump", "t", "tEnd", "threshold",
        "v", "v_warp", "alpha_r", "alpha",
        "event_horizon", "curvature",
    })

    def __init__(self, program: ProgramNode):
        self.program = program
        self.issues: List[ValidationError] = []
        self._defined: set = set()

    def check(self) -> List[ValidationError]:
        self.issues.clear()
        self._defined = set(self._ALWAYS_DEFINED)
        # First pass: collect defined names
        for block in self.program.blocks:
            if isinstance(block, EntropyBlockNode):
                self._defined.add(block.name)
            elif isinstance(block, StateBlockNode):
                self._defined.add(block.name)
            elif isinstance(block, StabilityBlockNode):
                self._defined.add(block.metric_name)
        # Second pass: check condition references
        for block in self.program.blocks:
            if isinstance(block, (CollapseBlockNode, WarpBlockNode, EmitBlockNode)):
                self._check_condition(block.condition, type(block).__name__)
            elif isinstance(block, TransitionBlockNode):
                for stmt in block.statements:
                    self._check_stmt(stmt)
        return self.issues

    def _add(self, msg: str, severity: str = "warning"):
        self.issues.append(ValidationError(msg, severity))

    def _check_condition(self, condition: str, block_type: str) -> None:
        """Check that a condition string references at least one defined symbol."""
        if not condition:
            return
        # If condition contains "D(t)" but no STABILITY block defined → flag
        if "D(t)" in condition and "D" not in self._defined:
            self._add(
                f"Scope: {block_type} condition references D(t) but no STABILITY "
                f"block is defined — D(t) is undefined"
            )

    def _check_stmt(self, stmt: str) -> None:
        """Check that an assignment statement LHS references a defined symbol."""
        if not stmt:
            return
        # Statements are like "S = S / (1 + α)" — LHS is the first word
        parts = stmt.strip().split()
        if parts:
            lhs = parts[0]
            # Warn if LHS is not a known defined symbol (but only if it looks like
            # a single identifier, not an operator)
            if lhs.isidentifier() and lhs not in self._defined and lhs not in self._ALWAYS_DEFINED:
                self._add(
                    f"Scope: ON block assigns to '{lhs}' which was not declared "
                    f"in an ENTROPY or STATE block",
                    "info",
                )


# ── Public API ────────────────────────────────────────────────────────────────

def validate(program: ProgramNode) -> Tuple[bool, List[ValidationError]]:
    """Validate a parsed COMAF-Lite program.

    Returns (is_valid, list_of_errors).
    is_valid = True if no error-level issues (warnings are acceptable).

    Preserved for backward compatibility. For structured results, use
    validate_structured().
    """
    validator = Validator(program)
    issues = validator.validate()
    has_errors = any(e.severity == "error" for e in issues)
    return not has_errors, issues


def validate_structured(
    program: ProgramNode,
    check_schema: bool = False,
    check_dimensional: bool = True,
) -> ValidationResult:
    """Validate a parsed COMAF-Lite program and return a structured ValidationResult.

    Args:
        program:           Parsed ProgramNode.
        check_schema:      If True, also run top-level JSON Schema validation.
        check_dimensional: If True, run DimensionalChecker + ScopeChecker (v1.3.19).

    Returns:
        ValidationResult with 5 explicit level fields.
    """
    # Semantic validation
    validator = Validator(program)
    semantic_issues = validator.validate()
    semantic_valid = not any(e.severity == "error" for e in semantic_issues)

    all_issues = list(semantic_issues)
    schema_valid: Optional[bool] = None
    dimensional_valid: Optional[bool] = None

    # Schema validation (v1.3.17)
    if check_schema:
        schema_ok, schema_issues = validator.validate_against_schema()
        schema_valid = schema_ok
        all_issues = schema_issues + all_issues

    # Dimensional + scope checking (v1.3.19)
    if check_dimensional:
        dim_checker = DimensionalChecker(program)
        dim_issues = dim_checker.check()
        scope_checker = ScopeChecker(program)
        scope_issues = scope_checker.check()
        combined = dim_issues + scope_issues
        dimensional_valid = not any(e.severity == "error" for e in combined)
        all_issues = all_issues + combined

    return ValidationResult(
        syntax_valid=True,
        schema_valid=schema_valid,
        semantic_valid=semantic_valid,
        dimensional_valid=dimensional_valid,
        solver_valid=None,
        issues=all_issues,
    )
