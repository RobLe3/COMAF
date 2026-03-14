"""
COMAF-Lite CLI
Usage:
  comaf run model.comaf --target mathematica|python
  comaf validate model.comaf
  comaf convert --si-to-pnms VALUE UNIT
"""

import argparse
import sys
import os
from pathlib import Path

from .parser import parse, ParseError
from .lexer import LexerError
from .validator import validate
from .transpilers.mathematica import transpile_mathematica
from .transpilers.python import transpile_python
from . import pnms


def cmd_validate(args):
    source_path = Path(args.file)
    if not source_path.exists():
        print(f"Error: file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    source = source_path.read_text(encoding="utf-8")
    try:
        program = parse(source)
    except (LexerError, ParseError) as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    is_valid, issues = validate(program)
    for issue in issues:
        print(issue)

    if is_valid:
        print(f"✓ {source_path.name}: valid")
        sys.exit(0)
    else:
        print(f"✗ {source_path.name}: validation failed")
        sys.exit(1)


def cmd_run(args):
    source_path = Path(args.file)
    if not source_path.exists():
        print(f"Error: file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    source = source_path.read_text(encoding="utf-8")
    try:
        program = parse(source)
    except (LexerError, ParseError) as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    target = getattr(args, "target", "mathematica")
    if target == "mathematica":
        output = transpile_mathematica(program)
        out_path = source_path.with_suffix(".wl")
    elif target == "python":
        output = transpile_python(program)
        out_path = source_path.with_suffix(".py")
    else:
        print(f"Unknown target: {target}", file=sys.stderr)
        sys.exit(1)

    out_path.write_text(output, encoding="utf-8")
    print(f"✓ Transpiled to {out_path}")


def cmd_convert(args):
    """Convert SI value to PNMS."""
    value = float(args.value)
    unit = args.unit.lower()

    conversions = {
        "m": ("Plameters", pnms.to_plameters),
        "meters": ("Plameters", pnms.to_plameters),
        "s": ("Plaseconds", pnms.to_plaseconds),
        "seconds": ("Plaseconds", pnms.to_plaseconds),
        "j": ("Plajoules", pnms.to_plajoules),
        "joules": ("Plajoules", pnms.to_plajoules),
        "kg": ("Plakilograms", pnms.to_plakilograms),
        "kilograms": ("Plakilograms", pnms.to_plakilograms),
    }

    if unit not in conversions:
        print(f"Unknown unit: {unit}. Supported: {list(conversions.keys())}", file=sys.stderr)
        sys.exit(1)

    pnms_unit, converter = conversions[unit]
    result = converter(value)
    print(f"{value} {unit} = {result:.6e} {pnms_unit}")


def main():
    parser = argparse.ArgumentParser(
        prog="comaf",
        description="COMAF-Lite DSL tool for QULT-C physics modeling"
    )
    subparsers = parser.add_subparsers(dest="command")

    # validate
    p_val = subparsers.add_parser("validate", help="Validate a .comaf file")
    p_val.add_argument("file", help="Path to .comaf source file")

    # run
    p_run = subparsers.add_parser("run", help="Transpile a .comaf file")
    p_run.add_argument("file", help="Path to .comaf source file")
    p_run.add_argument("--target", choices=["mathematica", "python"],
                       default="mathematica", help="Output target")

    # convert
    p_conv = subparsers.add_parser("convert", help="Convert SI unit to PNMS")
    p_conv.add_argument("--si-to-pnms", action="store_true")
    p_conv.add_argument("value", type=float)
    p_conv.add_argument("unit", help="SI unit (m, s, J, kg)")

    args = parser.parse_args()

    if args.command == "validate":
        cmd_validate(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "convert":
        cmd_convert(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
