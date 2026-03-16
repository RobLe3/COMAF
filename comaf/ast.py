"""
COMAF-Lite Abstract Syntax Tree node definitions.
Each node type corresponds to a block or construct in the COMAF-Lite DSL.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Node:
    """Base class for all AST nodes."""
    pass


@dataclass
class ProgramNode(Node):
    """Root node: entire COMAF-Lite program."""
    model_name: Optional[str]          # MODEL identifier
    entity: str
    cycle: str
    frame: str                         # raw string, e.g. "t ∈ [0, 1 WarpTick]"
    units: str                         # "Planck" | "SI" | "Custom"
    blocks: List[Node] = field(default_factory=list)


@dataclass
class StateBlockNode(Node):
    """STATE ψ: evolve Schrödinger { ... }"""
    name: str
    init: Any                          # string or list of state refs
    hamiltonian: str


@dataclass
class EntropyBlockNode(Node):
    """ENTROPY S: evolve Boltzmann { ... }"""
    name: str
    init: float
    max_val: float
    scale: float                       # in Plaseconds (numeric)
    scale_unit: str                    # "Plaseconds" etc.


@dataclass
class GeometryBlockNode(Node):
    """GEOMETRY: field_equation: ..."""
    field_equation: str
    extra_fields: dict = field(default_factory=dict)  # CURVATURE etc.


@dataclass
class StabilityBlockNode(Node):
    """STABILITY: metric D(t) = ..."""
    metric_name: str
    expression: str


@dataclass
class CollapseBlockNode(Node):
    """IF condition: collapse { ... }"""
    condition: str
    energy: Optional[str]
    resolution: Optional[str]
    decoherence: Optional[str]


@dataclass
class WarpBlockNode(Node):
    """IF condition: warp { ... }"""
    condition: str
    velocity: Optional[str]
    safety: Optional[str]
    target: Optional[str]


@dataclass
class EmitBlockNode(Node):
    """IF condition: emit { ... }"""
    condition: str
    energy: Optional[str]
    decay: Optional[str]


@dataclass
class TransitionBlockNode(Node):
    """ON event_name: statement+"""
    event_name: str
    statements: List[str] = field(default_factory=list)


@dataclass
class AssignmentNode(Node):
    """target = expr"""
    target: str
    operator: str   # "=", "+=", "-=", "·="
    expression: str


@dataclass
class CommentNode(Node):
    """# comment"""
    text: str


@dataclass
class PhysicsQuantityNode(Node):
    """COMAF × PNMS addendum block: FORCE | POWER | PRESSURE | CURVATURE |
    CHARGE | ENTROPY_UNIT | UNCERTAINTY

    Syntax:  KEYWORD name: expression [unit]
    """
    keyword: str   # "FORCE", "POWER", "PRESSURE", "CURVATURE", "CHARGE",
                   # "ENTROPY_UNIT", "UNCERTAINTY"
    name: str
    expression: str
    unit: str = ""
