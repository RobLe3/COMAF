"""
COMAF-Lite AST Serializer
Converts a ProgramNode AST to a JSON-serializable dict.

v1.3.18: Initial implementation. Format is round-trippable via deserializer.py.
         Full comaf_lite_schema.json conformance requires v1.3.19+ improvements
         (geometry field_equation parsing fix, dimensional checker).
"""

from typing import Any
from .ast import (
    ProgramNode, StateBlockNode, EntropyBlockNode, GeometryBlockNode,
    StabilityBlockNode, CollapseBlockNode, WarpBlockNode, EmitBlockNode,
    TransitionBlockNode, AssignmentNode, CommentNode, PhysicsQuantityNode, Node,
)

_VERSION = "comaf-lite-1.337.0"


def _block_to_dict(block: Node) -> dict:
    if isinstance(block, StateBlockNode):
        return {
            "type": "STATE",
            "name": block.name,
            "init": block.init,
            "hamiltonian": block.hamiltonian,
        }
    elif isinstance(block, EntropyBlockNode):
        return {
            "type": "ENTROPY",
            "name": block.name,
            "init": block.init,
            "max_val": block.max_val,
            "scale": block.scale,
            "scale_unit": block.scale_unit,
        }
    elif isinstance(block, GeometryBlockNode):
        return {
            "type": "GEOMETRY",
            "field_equation": block.field_equation,
            "extra_fields": block.extra_fields,
        }
    elif isinstance(block, StabilityBlockNode):
        return {
            "type": "STABILITY",
            "metric_name": block.metric_name,
            "expression": block.expression,
        }
    elif isinstance(block, CollapseBlockNode):
        return {
            "type": "IF_COLLAPSE",
            "condition": block.condition,
            "energy": block.energy,
            "resolution": block.resolution,
            "decoherence": block.decoherence,
        }
    elif isinstance(block, WarpBlockNode):
        return {
            "type": "IF_WARP",
            "condition": block.condition,
            "velocity": block.velocity,
            "safety": block.safety,
            "target": block.target,
        }
    elif isinstance(block, EmitBlockNode):
        return {
            "type": "IF_EMIT",
            "condition": block.condition,
            "energy": block.energy,
            "decay": block.decay,
        }
    elif isinstance(block, TransitionBlockNode):
        return {
            "type": "ON_TRANSITION",
            "event_name": block.event_name,
            "statements": list(block.statements),
        }
    elif isinstance(block, AssignmentNode):
        return {
            "type": "ASSIGNMENT",
            "target": block.target,
            "operator": block.operator,
            "expression": block.expression,
        }
    elif isinstance(block, CommentNode):
        return {
            "type": "COMMENT",
            "text": block.text,
        }
    elif isinstance(block, PhysicsQuantityNode):
        return {
            "type": "PHYSICS_QUANTITY",
            "keyword": block.keyword,
            "name": block.name,
            "expression": block.expression,
            "unit": block.unit,
        }
    else:
        return {"type": "UNKNOWN", "repr": repr(block)}


def ast_to_dict(program: ProgramNode) -> dict:
    """Convert a ProgramNode AST to a JSON-serializable dict.

    The returned dict is round-trippable via comaf.deserializer.dict_to_ast().
    """
    return {
        "__version__": _VERSION,
        "model_name": program.model_name,
        "entity": program.entity,
        "cycle": program.cycle,
        "frame": program.frame,
        "units": program.units,
        "blocks": [_block_to_dict(b) for b in program.blocks],
    }
