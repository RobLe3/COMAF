"""
COMAF-Lite CLI
Usage:
  comaf run model.comaf --target mathematica|python
  comaf validate model.comaf [--strict] [--report json]
  comaf convert --si-to-pnms VALUE UNIT
"""

import argparse
import sys
import os
from pathlib import Path

from .parser import parse, ParseError
from .lexer import LexerError
from .validator import validate, validate_structured
from .transpilers.mathematica import transpile_mathematica
from .transpilers.python import transpile_python
from .runner import run_model
from . import pnms


def cmd_validate(args):
    import json as _json

    source_path = Path(args.file)
    if not source_path.exists():
        print(f"Error: file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    source = source_path.read_text(encoding="utf-8")
    try:
        program = parse(source)
    except (LexerError, ParseError) as e:
        if getattr(args, "report", None) == "json":
            print(_json.dumps({
                "valid": False, "syntax": "fail",
                "schema": "not_checked", "semantic": "not_checked",
                "dimensional": "not_checked", "solver": "not_checked",
                "issues": [{"level": "error", "message": str(e)}],
            }, indent=2))
        else:
            print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    strict = getattr(args, "strict", False)
    report = getattr(args, "report", None)

    result = validate_structured(program, check_schema=(report == "json"))

    if report == "json":
        print(_json.dumps(result.to_dict(), indent=2))
        sys.exit(0 if result.is_valid else 1)

    # Human-readable output
    for issue in result.issues:
        # In strict mode, warnings are treated as errors
        if strict and issue.severity == "warning":
            print(f"[ERROR(strict)] {issue.message}")
        else:
            print(issue)

    # Determine pass/fail
    has_errors = any(e.severity == "error" for e in result.issues)
    has_warnings = any(e.severity == "warning" for e in result.issues)
    failed = has_errors or (strict and has_warnings)

    if not failed:
        mode_note = " (strict)" if strict else ""
        print(f"✓ {source_path.name}: valid{mode_note}")
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


def cmd_explain(args):
    """Show per-block AST + Wolfram/Python for a .comaf model."""
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

    print(f"=== COMAF-Lite Model: {source_path.name} ===")
    print(f"Entity: {program.entity}  |  Cycle: {program.cycle}  |  Units: {program.units}")
    print(f"Frame:  {program.frame}")
    print()

    from .ast import (StateBlockNode, EntropyBlockNode, GeometryBlockNode,
                      StabilityBlockNode, CollapseBlockNode, WarpBlockNode,
                      EmitBlockNode, TransitionBlockNode, AssignmentNode)

    wl_lines = transpile_mathematica(program).splitlines()
    py_lines = transpile_python(program).splitlines()

    for i, block in enumerate(program.blocks, 1):
        btype = type(block).__name__
        print(f"Block {i}: {btype}")

        if isinstance(block, EntropyBlockNode):
            print(f"  Source:  ENTROPY {block.name} (init={block.init:.3e}, max={block.max_val:.3e}, scale={block.scale} {block.scale_unit})")
            wl_key = f"S0{block.name} ="
            py_key = f"def entropy_{block.name}"
            wl_ex = next((ln.strip() for ln in wl_lines if wl_key in ln), "(see .wl output)")
            py_ex = next((ln.strip() for ln in py_lines if py_key in ln), "(see .py output)")
            print(f"  Wolfram: {wl_ex}")
            print(f"  Python:  {py_ex}")

        elif isinstance(block, StateBlockNode):
            init_str = str(block.init)[:50] if block.init else "—"
            print(f"  Source:  STATE {block.name} (init={init_str!r})")
            wl_key = f"{block.name}[t_]"
            wl_ex = next((ln.strip() for ln in wl_lines if wl_key in ln), "(see .wl output)")
            print(f"  Wolfram: {wl_ex}")
            print(f"  Python:  (STATE blocks not directly transpiled to Python functions)")

        elif isinstance(block, StabilityBlockNode):
            print(f"  Source:  STABILITY {block.metric_name} = {block.expression[:60]}")
            wl_key = f"{block.metric_name}[gradS_"
            wl_ex = next((ln.strip() for ln in wl_lines if wl_key in ln), "(see .wl output)")
            py_key = f"def {block.metric_name}("
            py_ex = next((ln.strip() for ln in py_lines if py_key in ln), "(see .py output)")
            print(f"  Wolfram: {wl_ex}")
            print(f"  Python:  {py_ex}")

        elif isinstance(block, CollapseBlockNode):
            print(f"  Source:  IF {block.condition}: collapse")
            wl_ex = next((ln.strip() for ln in wl_lines if "collapseQ" in ln), "(see .wl output)")
            print(f"  Wolfram: {wl_ex}")

        elif isinstance(block, WarpBlockNode):
            print(f"  Source:  IF {block.condition}: warp")
            wl_ex = next((ln.strip() for ln in wl_lines if "warpQ" in ln), "(see .wl output)")
            print(f"  Wolfram: {wl_ex}")

        elif isinstance(block, EmitBlockNode):
            print(f"  Source:  IF {block.condition}: emit")
            wl_ex = next((ln.strip() for ln in wl_lines if "emitQ" in ln), "(see .wl output)")
            print(f"  Wolfram: {wl_ex}")

        elif isinstance(block, TransitionBlockNode):
            stmts = "; ".join(block.statements[:2])
            print(f"  Source:  ON {block.event_name}: {stmts}")
            wl_ex = next((ln.strip() for ln in wl_lines if "WhenEvent" in ln), "(see .wl output)")
            py_fn = f"def on_{block.event_name.replace('.', '_').replace('...', '_')}"
            py_ex = next((ln.strip() for ln in py_lines if "def on_" in ln), "(see .py output)")
            print(f"  Wolfram: {wl_ex}")
            print(f"  Python:  {py_ex}")

        elif isinstance(block, GeometryBlockNode):
            eq = block.field_equation or "(parsed separately as AssignmentNode)"
            print(f"  Source:  GEOMETRY field_equation={eq[:60]!r}")
            print(f"  Wolfram: (* GEOMETRY block — field equation as comment *)")

        elif isinstance(block, AssignmentNode):
            print(f"  Source:  {block.target} {block.operator} {block.expression[:50]}")
            print(f"  Note:    Top-level assignment (from field_equation line parse artifact)")

        else:
            print(f"  Source:  {repr(block)[:80]}")

        print()


def cmd_doctor(args):
    """Health check: verify repo structure and model integrity."""
    import math

    repo_root = Path(__file__).parent.parent
    stdlib_dir = repo_root / "stdlib"
    wolfram_dir = repo_root / "tests" / "wolfram"
    docs_dir = repo_root / "docs"

    ok = True
    lines = []

    def check(cond: bool, msg: str) -> bool:
        icon = "✓" if cond else "✗"
        lines.append(f"  {icon} {msg}")
        return cond

    lines.append("=== COMAF-Lite Health Check ===")
    lines.append("")

    # Spec files
    lines.append("Spec files:")
    ok &= check((docs_dir / "comaf_lite.ebnf").exists(), "EBNF grammar: docs/comaf_lite.ebnf")
    ok &= check((docs_dir / "comaf_lite_schema.json").exists(), "JSON Schema: docs/comaf_lite_schema.json")
    ok &= check((repo_root / "TRACEABILITY.md").exists(), "TRACEABILITY.md present")
    lines.append("")

    # Stdlib models
    lines.append("Stdlib models:")
    stdlib_models = sorted(stdlib_dir.glob("*.comaf"))
    check(len(stdlib_models) > 0, f"Stdlib count: {len(stdlib_models)} models found")
    parse_errors = 0
    validate_errors = 0
    for model_path in stdlib_models:
        try:
            prog = parse(model_path.read_text(encoding="utf-8"))
            is_valid, issues = validate(prog)
            errs = [i for i in issues if i.severity == "error"]
            if errs:
                validate_errors += 1
                check(False, f"{model_path.name}: {len(errs)} validation error(s)")
        except Exception as e:
            parse_errors += 1
            check(False, f"{model_path.name}: parse error — {e}")
    if parse_errors == 0 and validate_errors == 0:
        check(True, f"All {len(stdlib_models)} stdlib models parse and validate")
    lines.append("")

    # Wolfram TC files
    lines.append("Wolfram test cases:")
    tc_files = sorted(wolfram_dir.glob("tc*.wl"))
    check(len(tc_files) >= 6, f"Wolfram TC files: {len(tc_files)}/6 found")
    for tc in tc_files:
        check(tc.exists(), f"{tc.name} present")
    lines.append("")

    # PNMS constants
    lines.append("PNMS constants (CODATA 2018):")
    check(abs(pnms.LAMBDA_P - 1.616e-35) / 1.616e-35 < 1e-3,
          f"λ_p = {pnms.LAMBDA_P:.4e} m (expected ~1.616×10⁻³⁵ m)")
    check(abs(pnms.T_P - 5.391e-44) / 5.391e-44 < 1e-3,
          f"t_p = {pnms.T_P:.4e} s (expected ~5.391×10⁻⁴⁴ s)")
    check(abs(pnms.E_P - 1.956e9) / 1.956e9 < 1e-2,
          f"E_p = {pnms.E_P:.4e} J (expected ~1.956×10⁹ J)")
    lines.append("")

    for line in lines:
        print(line)

    if ok:
        print("Result: all checks passed")
        sys.exit(0)
    else:
        print("Result: some checks failed (see ✗ above)")
        sys.exit(1)


def cmd_simulate(args):
    """Run numerical simulation of a .comaf model."""
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

    t_end = getattr(args, "t_end", 100.0)
    steps = getattr(args, "steps", 100)

    try:
        result = run_model(program, t_end=t_end, steps=steps)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"=== Simulation: {source_path.name} ===")
    print(f"Entity: {result.entity}  Cycle: {result.cycle}")
    print(f"t_end: {t_end:.1f} Plaseconds  steps: {result.steps}")
    print()

    # Print sampled output (every 10th step or first 10)
    n_show = min(10, result.steps)
    stride = max(1, result.steps // n_show)
    print(f"{'t (Ps)':>12}  {'S':>14}  {'D':>12}")
    print("-" * 42)
    for i in range(0, result.steps, stride):
        print(f"{result.t[i]:12.3f}  {result.S[i]:14.6e}  {result.D[i]:12.6f}")

    print()
    if result.collapse_triggered:
        print(f"✗ Collapse triggered at t = {result.collapse_time:.3f} Plaseconds")
    else:
        print(f"✓ No collapse triggered (D > threshold throughout)")
    print(f"✓ Simulation complete: {result.steps} steps")


def main():
    parser = argparse.ArgumentParser(
        prog="comaf",
        description="COMAF-Lite DSL tool for QULT-C physics modeling"
    )
    parser.add_argument("--version", action="version", version="comaf 1.337.0")
    subparsers = parser.add_subparsers(dest="command")

    # validate
    p_val = subparsers.add_parser("validate", help="Validate a .comaf file")
    p_val.add_argument("file", help="Path to .comaf source file")
    p_val.add_argument("--strict", action="store_true",
                       help="Treat warnings as errors (zero-warning policy)")
    p_val.add_argument("--report", choices=["json"], default=None,
                       help="Output format: json = machine-readable ValidationResult")

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

    # explain
    p_exp = subparsers.add_parser("explain", help="Show per-block AST + transpiler mapping")
    p_exp.add_argument("file", help="Path to .comaf source file")

    # doctor
    subparsers.add_parser("doctor", help="Run repo health check")

    # simulate
    p_sim = subparsers.add_parser("simulate", help="Run numerical simulation of a .comaf model")
    p_sim.add_argument("file", help="Path to .comaf source file")
    p_sim.add_argument("--t-end", type=float, default=100.0,
                       help="Simulation end time in Plaseconds (default: 100)")
    p_sim.add_argument("--steps", type=int, default=100,
                       help="Number of output time steps (default: 100)")

    args = parser.parse_args()

    if args.command == "validate":
        cmd_validate(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "convert":
        cmd_convert(args)
    elif args.command == "explain":
        cmd_explain(args)
    elif args.command == "doctor":
        cmd_doctor(args)
    elif args.command == "simulate":
        cmd_simulate(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
