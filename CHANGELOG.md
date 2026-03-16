# CHANGELOG — COMAF-Lite

## v1.3.30 (2026-03-16) — Bug fixes: GEOMETRY parser + standalone Python output

### v1.3.30 — Two deferred gaps resolved

- **`comaf/parser.py`**: Added `skip_newlines()` in `parse_geometry_block()` before
  checking for the `field_equation` keyword. Previously, `field_equation:` on the line
  after `GEOMETRY:` was skipped (no newline skip → match failed), leaving the
  `GeometryBlockNode` empty and the field equation parsed as an orphan `AssignmentNode`.
  `--strict` mode now correctly accepts all 14 stdlib models, including those with
  GEOMETRY blocks.

- **`comaf/transpilers/python.py`**: Replaced `from comaf.pnms import ...` in the
  generated file header with inlined PNMS constants (`HBAR`, `C`, `LAMBDA_P`,
  `PLASECOND`, etc.) and the five helper functions (`l_eff`, `psi_factor`, `e_jump`,
  `decoherence_metric`, `f_collapse`). Transpiled `.py` files now run standalone with
  only `numpy` and `scipy` — the `comaf` package is not required.

- **`tests/fixtures/`**: Regenerated 6 structural snapshots for stdlib models with
  GEOMETRY blocks (previously captured empty `field_equation`; now correct).

- **`tests/test_strict_mode.py`**: Updated `WARNS_MODEL` to use a genuinely empty
  GEOMETRY block rather than the now-fixed newline-parsing behaviour.

---

## v1.3.29 (2026-03-16) — Numerical Calibration Tests + Phase 2 Sprint

**Summary:** Phase 2 sprint (v1.3.15–v1.3.29) brings repo to full paper-level feature parity.
Test count: 86 → 289. 14 new stdlib models. `comaf simulate` execution layer.

### v1.3.29 — Numerical calibration tests
- `tests/test_numerical_calibration.py` — 14 calibration assertions
- PNMS constants vs. CODATA 2018 (Plameter=1.616 m, Plasecond=5.39 s)
- DHO ring-down: S(1τ) analytical match, S(5τ) < 1% from S_max
- BH entropy: pnms.bh_entropy(M_sun) ≈ 1.05×10⁷⁷ k_B verified

### v1.3.28 — `comaf simulate` + runner
- `comaf/runner.py` — ODE simulation in Plaseconds; collapse detection
- `comaf simulate model.comaf --t-end N --steps N` CLI command
- `tests/test_simulate.py` — 9 tests

### v1.3.27 — QULT-C Hamiltonian stdlib model
- `stdlib/qultc_hamiltonian.comaf` — full Ĥ_QULT with STATE, ENTROPY, STABILITY

### v1.3.26 — Decoherence anisotropy (Fix 3c)
- `stdlib/decoherence_anisotropy.comaf` — V(t,θ) = V₀ exp(-(Γ₀+Γ_QULT·cos²θ)·t)

### v1.3.25 — F_collapse GRW normalization (Fix 2b) + BH entropy physical model
- `comaf/pnms.py`: `f_collapse_rate()` with (L₀/λp)⁻³ suppression; `grw_consistency_check()`
- `stdlib/bh_entropy_physical.comaf` — S_BH ≈ 1.05×10⁷⁷ k_B

### v1.3.23 — Addendum stdlib models
- `stdlib/neutron_star_curvature.comaf`, `stdlib/photon_emission.comaf`

### v1.3.22 — COMAF × PNMS addendum keywords
- `PhysicsQuantityNode` in AST: FORCE, POWER, PRESSURE, CURVATURE, CHARGE, ENTROPY_UNIT, UNCERTAINTY
- `stdlib/addendum_units_demo.comaf` — all 7 keywords demonstrated
- `tests/test_addendum_keywords.py` — 17 tests

### v1.3.21 — GitHub Actions CI
- `.github/workflows/ci.yml` — Python 3.10/3.11/3.12

### v1.3.20 — TC5/TC6 Python stubs + `comaf explain` + `comaf doctor`
- TC5: tau_A = 10.0 Plaseconds; TC6: D_min = 0.95 collapse threshold
- `comaf explain model.comaf` — per-block AST + transpiler mapping
- `comaf doctor` — repo health check

### v1.3.19 — Validator multi-level framework
- `DimensionalChecker` + `ScopeChecker` — dimensional and scope validation
- `validate_structured(check_schema, check_dimensional)` API

### v1.3.18 — Snapshot round-trip infrastructure
- `comaf/serializer.py` + `comaf/deserializer.py` — AST ↔ JSON round-trip
- `tests/test_roundtrip.py` — 49 parametrized tests
- 8 structural snapshots in `tests/fixtures/`

### v1.3.17 — `--strict` mode + ValidationResult + `--report json`
- `ValidationResult` with 5 levels; `comaf validate --report json`

### v1.3.16 — Parser Unicode regression + negative tests
- `tests/test_parser_regression.py` — 29 tests (Unicode, bra-ket, dotted events, negative)

### v1.3.15 — README alignment + TRACEABILITY.md
- README badge fixes; TRACEABILITY.md initial version

---

## v1.3.14 (2026-03-16) — P2 Substantive Fixes

- **validator.py**: Added physics range guard for STABILITY blocks — `D(t)` values parsed
  as literals outside `[0, 1]` now emit a validation error.
- **validator.py**: Added Planck-energy guard for COLLAPSE blocks — numeric energy values
  exceeding `E_p` emit a warning with PNMS unit suggestion.
- **transpilers/python.py**: Replaced placeholder `print("Simulation ready...")` stub in
  `_emit_main()` with a concrete `scipy.integrate.solve_ivp` scaffold wired to parsed
  entropy/stability constants. Generated scripts now run directly.
- **tests/test_end_to_end.py**: New — 11 integration tests covering stdlib parse/validate/
  transpile and a parametrized round-trip test for all `.comaf` models.
- **tests/test_validator.py**: New — 3 unit tests for validator physics guards.

## v1.3.13 (2026-03-16) — P0+P1 Quick Fixes

- **pyproject.toml** (P0): Added `[tool.hatch.build.targets.wheel] packages = ["comaf"]`
  stanza. Fixes `pip install .` failure caused by hatchling normalizing `comaf-lite` to
  `comaf_lite` and finding no matching package directory.
- **transpilers/mathematica.py** (P1): Prefixed `PNMS_HEADER` triple-quoted string with
  `r"""` and changed Wolfram escape sequences in f-strings to use `rf"..."` / `r"..."` to
  eliminate ~18 Python `SyntaxWarning: invalid escape sequence '\['` warnings.
- **parser.py** (P1): Removed unconditional `break` at the end of the outer loop in
  `parse_transition_block()`. Replaced with a proper line-by-line collection loop that
  exits only on top-level keywords (`ON`, `IF`, `STATE`, `ENTROPY`, `GEOMETRY`,
  `STABILITY`) or EOF. Multi-statement `ON` blocks (e.g., `bounce_cosmology.comaf`) now
  collect all statements correctly.

---

*Final version: v1.337lulz (March 2026). See TRACEABILITY.md for the full paper-to-repo mapping.*
