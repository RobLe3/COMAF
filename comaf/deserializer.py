"""
COMAF-Lite AST Deserializer
Converts a serialized dict (from serializer.ast_to_dict) back to a ProgramNode.

v1.3.18: Initial implementation. Inverse of comaf.serializer.ast_to_dict().
"""

from typing import Any, Optional
from .ast import (
    ProgramNode, StateBlockNode, EntropyBlockNode, GeometryBlockNode,
    StabilityBlockNode, CollapseBlockNode, WarpBlockNode, EmitBlockNode,
    TransitionBlockNode, AssignmentNode, CommentNode, PhysicsQuantityNode, Node,
)


class DeserializationError(Exception):
    pass


def _dict_to_block(data: dict) -> Node:
    block_type = data.get("type")

    if block_type == "STATE":
        return StateBlockNode(
            name=data["name"],
            init=data["init"],
            hamiltonian=data["hamiltonian"],
        )
    elif block_type == "ENTROPY":
        return EntropyBlockNode(
            name=data["name"],
            init=float(data["init"]),
            max_val=float(data["max_val"]),
            scale=float(data["scale"]),
            scale_unit=data["scale_unit"],
        )
    elif block_type == "GEOMETRY":
        return GeometryBlockNode(
            field_equation=data.get("field_equation", ""),
            extra_fields=data.get("extra_fields", {}),
        )
    elif block_type == "STABILITY":
        return StabilityBlockNode(
            metric_name=data["metric_name"],
            expression=data["expression"],
        )
    elif block_type == "IF_COLLAPSE":
        return CollapseBlockNode(
            condition=data["condition"],
            energy=data.get("energy"),
            resolution=data.get("resolution"),
            decoherence=data.get("decoherence"),
        )
    elif block_type == "IF_WARP":
        return WarpBlockNode(
            condition=data["condition"],
            velocity=data.get("velocity"),
            safety=data.get("safety"),
            target=data.get("target"),
        )
    elif block_type == "IF_EMIT":
        return EmitBlockNode(
            condition=data["condition"],
            energy=data.get("energy"),
            decay=data.get("decay"),
        )
    elif block_type == "ON_TRANSITION":
        return TransitionBlockNode(
            event_name=data["event_name"],
            statements=list(data.get("statements", [])),
        )
    elif block_type == "ASSIGNMENT":
        return AssignmentNode(
            target=data["target"],
            operator=data["operator"],
            expression=data["expression"],
        )
    elif block_type == "COMMENT":
        return CommentNode(text=data["text"])
    elif block_type == "PHYSICS_QUANTITY":
        return PhysicsQuantityNode(
            keyword=data["keyword"],
            name=data["name"],
            expression=data["expression"],
            unit=data.get("unit", ""),
        )
    else:
        raise DeserializationError(f"Unknown block type: {block_type!r}")


def dict_to_ast(data: dict) -> ProgramNode:
    """Convert a serialized dict back to a ProgramNode AST.

    The input dict must be the output of comaf.serializer.ast_to_dict().
    Raises DeserializationError on invalid input.
    """
    for key in ("entity", "cycle", "frame", "units", "blocks"):
        if key not in data:
            raise DeserializationError(f"Missing required key: {key!r}")

    blocks = [_dict_to_block(b) for b in data["blocks"]]

    return ProgramNode(
        model_name=data.get("model_name"),
        entity=data["entity"],
        cycle=data["cycle"],
        frame=data["frame"],
        units=data["units"],
        blocks=blocks,
    )
