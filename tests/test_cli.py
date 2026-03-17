"""
CLI integration tests — exercises comaf.cli.main() via sys.argv patching.
Covers all six subcommands: validate, run, convert, explain, doctor, simulate.
"""

import json
import sys
import pytest
from pathlib import Path

from comaf.cli import main

STDLIB = Path(__file__).parent.parent / "stdlib"
DHO_A = str(STDLIB / "dho_model_a_entropy_damping.comaf")
BOUNCE = str(STDLIB / "bounce_cosmology.comaf")


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_cli(*argv, expect_exit=0):
    """Call main() with given argv; assert SystemExit code matches expect_exit."""
    sys.argv = ["comaf", *argv]
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == expect_exit, (
        f"Expected exit {expect_exit}, got {exc.value.code}"
    )


# ── validate ──────────────────────────────────────────────────────────────────

def test_cli_validate_valid_model(capsys):
    run_cli("validate", DHO_A)
    out = capsys.readouterr().out
    assert "valid" in out


def test_cli_validate_strict_passes_clean_model(capsys):
    run_cli("validate", "--strict", DHO_A)
    out = capsys.readouterr().out
    assert "valid" in out


def test_cli_validate_report_json(capsys):
    run_cli("validate", "--report", "json", DHO_A)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "valid" in data
    assert "syntax" in data


def test_cli_validate_missing_file(capsys):
    run_cli("validate", "nonexistent.comaf", expect_exit=1)


def test_cli_validate_parse_error_exits_1(tmp_path, capsys):
    bad = tmp_path / "bad.comaf"
    bad.write_text("ENTITY missing_headers_entirely\n")
    run_cli("validate", str(bad), expect_exit=1)


# ── run (transpile) ───────────────────────────────────────────────────────────

def test_cli_run_python_target(tmp_path, capsys):
    src = tmp_path / "dho.comaf"
    src.write_text(Path(DHO_A).read_text(encoding="utf-8"), encoding="utf-8")
    sys.argv = ["comaf", "run", str(src), "--target", "python"]
    main()
    out_py = tmp_path / "dho.py"
    assert out_py.exists()
    content = out_py.read_text()
    assert "solve_ivp" in content
    assert "PLASECOND" in content
    # No live import of comaf package — PNMS constants are inlined
    assert "from comaf.pnms import" not in content


def test_cli_run_mathematica_target(tmp_path, capsys):
    src = tmp_path / "dho.comaf"
    src.write_text(Path(DHO_A).read_text(encoding="utf-8"), encoding="utf-8")
    sys.argv = ["comaf", "run", str(src), "--target", "mathematica"]
    main()
    out_wl = tmp_path / "dho.wl"
    assert out_wl.exists()
    content = out_wl.read_text()
    # Wolfram transpiler uses S[t_] function definitions and Exp[]
    assert "S[t_]" in content or "Exp[" in content


def test_cli_run_missing_file(capsys):
    run_cli("run", "ghost.comaf", "--target", "python", expect_exit=1)


# ── convert ───────────────────────────────────────────────────────────────────

def test_cli_convert_meters(capsys):
    sys.argv = ["comaf", "convert", "--si-to-pnms", "1.0", "m"]
    main()
    out = capsys.readouterr().out
    assert "Plameters" in out
    assert "6.187" in out


def test_cli_convert_seconds(capsys):
    sys.argv = ["comaf", "convert", "--si-to-pnms", "1.0", "s"]
    main()
    out = capsys.readouterr().out
    assert "Plaseconds" in out
    assert "1.854" in out   # 1.854859e-01


def test_cli_convert_joules(capsys):
    sys.argv = ["comaf", "convert", "--si-to-pnms", "1.0", "j"]
    main()
    assert "Plajoules" in capsys.readouterr().out


def test_cli_convert_kilograms(capsys):
    sys.argv = ["comaf", "convert", "--si-to-pnms", "1.0", "kg"]
    main()
    assert "Plakilograms" in capsys.readouterr().out


def test_cli_convert_unknown_unit_exits_1(capsys):
    run_cli("convert", "--si-to-pnms", "1.0", "furlongs", expect_exit=1)


# ── explain ───────────────────────────────────────────────────────────────────

def test_cli_explain_outputs_blocks(capsys):
    sys.argv = ["comaf", "explain", DHO_A]
    main()
    out = capsys.readouterr().out
    assert "ENTROPY" in out
    assert "Source:" in out
    assert "Wolfram:" in out
    assert "Python:" in out


def test_cli_explain_bounce_has_geometry(capsys):
    sys.argv = ["comaf", "explain", BOUNCE]
    main()
    out = capsys.readouterr().out
    assert "GEOMETRY" in out


def test_cli_explain_missing_file(capsys):
    run_cli("explain", "no_such.comaf", expect_exit=1)


# ── doctor ────────────────────────────────────────────────────────────────────

def test_cli_doctor_runs(capsys):
    sys.argv = ["comaf", "doctor"]
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "stdlib" in out.lower() or "ebnf" in out.lower() or "schema" in out.lower()


def test_cli_doctor_shows_stdlib_count(capsys):
    sys.argv = ["comaf", "doctor"]
    with pytest.raises(SystemExit):
        main()
    out = capsys.readouterr().out
    assert "model" in out.lower()


# ── simulate ──────────────────────────────────────────────────────────────────

def test_cli_simulate_dho(capsys):
    sys.argv = ["comaf", "simulate", DHO_A, "--t-end", "10", "--steps", "5"]
    main()
    out = capsys.readouterr().out
    assert "Simulation" in out or "t (Ps)" in out


def test_cli_simulate_no_collapse(capsys):
    sys.argv = ["comaf", "simulate", DHO_A, "--t-end", "10", "--steps", "5"]
    main()
    out = capsys.readouterr().out
    assert "collapse" in out.lower()


def test_cli_simulate_missing_file(capsys):
    run_cli("simulate", "nowhere.comaf", expect_exit=1)


# ── version ───────────────────────────────────────────────────────────────────

def test_cli_version(capsys):
    run_cli("--version", expect_exit=0)
    # argparse prints to stdout; version string contains version number
    out = capsys.readouterr().out
    assert "1.337" in out
