# COMAF-Lite Interpreter

**COMAF-Lite** (Computational Ontology Modeling and Analysis Framework, Lite version) is a declarative domain-specific language (DSL) for writing and executing physical models within the QULT-C framework — a layered computational ontology for quantum cosmology.

This repository contains the reference Python implementation of the COMAF-Lite interpreter, including:
- A complete lexer, parser, and AST
- A semantic validator with physical unit consistency checking
- Transpilers to **Wolfram Language** (`.wl`) and **Python/NumPy** (`.py`)
- A stdlib of six canonical cosmological models
- Four Wolfram Cloud-verified simulation test cases (VFR-301–VFR-304)

**Paper:** [QULT-C: A Layered Computational Ontology for Quantum Cosmology](docs/QULT-C_v1.3.0-review.pdf) (v1.3.0-review, March 2026)

[![Version](https://img.shields.io/badge/version-1.3.0--review-blue)](docs/QULT-C_v1.3.0-review.pdf)
[![Tests](https://img.shields.io/badge/tests-36%20passed-brightgreen)]()
[![arXiv](https://img.shields.io/badge/arXiv-coming-lightgrey)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Installation

**Standard install:**

```bash
pip install .
```

**Editable install (for development):**

```bash
pip install -e .
pip install -e ".[dev]"   # includes pytest
```

**Requirements:** Python >= 3.10, NumPy >= 1.24, SciPy >= 1.10

---

## Quick Start

Write a minimal COMAF-Lite model (or use one from `stdlib/`):

```comaf
# my_model.comaf

ENTITY: BouncingUniverse
CYCLE: CPL-n
FRAME: t ∈ [0, 1 WarpTick]
UNITS: Planck

ENTROPY S:
  evolve Boltzmann {
    init: 1e120
    max: 1e121
    scale: 1e9 Plaseconds
  }

STATE ψ:
  evolve Schrödinger {
    init: superposition[|contracting⟩, |expanding⟩]
    hamiltonian: H = H_gravity + H_quantum
  }

GEOMETRY:
  field_equation: G + Λg = (8πG/c⁴) · <T_total>

STABILITY:
  metric D(t) = exp(-|∇S(t)| · t)

ON cycle.end:
  S = S / (1 + α)
  ψ ·= e^(iπ)
```

**Validate the model:**

```bash
comaf validate my_model.comaf
```

**Transpile to Wolfram Language:**

```bash
comaf run my_model.comaf --target mathematica
# Writes: my_model.wl
```

**Transpile to Python/NumPy:**

```bash
comaf run my_model.comaf --target python
# Writes: my_model.py
```

**Convert SI units to PNMS:**

```bash
comaf convert --si-to-pnms 1.0 m
# Output: 1.0 m = 6.187e-36 Plameters
```

---

## Running the Four Test Cases

The four canonical framework demonstration cases from the paper (Appendix E) are provided as standalone Wolfram Language scripts in `tests/wolfram/`. Each has been verified in Wolfram Cloud (March 2026).

| File | Test Case | VFR Tag | Description |
|------|-----------|---------|-------------|
| `tests/wolfram/tc1_bounce_cosmology.wl` | TC1 | VFR-301 | Entropy-Reversal Bounce Cosmology |
| `tests/wolfram/tc2_decoherence_expansion.wl` | TC2 | VFR-302 | Decoherence-Limited Quantum Expansion |
| `tests/wolfram/tc3_entropy_curvature_oscillation.wl` | TC3 | VFR-303 | Entropy-Curvature Feedback Oscillation |
| `tests/wolfram/tc4_black_hole_collapse.wl` | TC4 | VFR-304 | Black Hole Collapse with Entropy-Driven Trigger |

**Run in Wolfram Cloud:**

1. Open [Wolfram Cloud](https://www.wolframcloud.com/) or Wolfram Desktop.
2. Create a new notebook and paste the contents of the `.wl` file, or upload and evaluate directly.
3. Each script prints its verification output and a final `PASS` statement.

**Run with the open-source Wolfram Engine (CLI):**

```bash
wolframscript -file tests/wolfram/tc1_bounce_cosmology.wl
wolframscript -file tests/wolfram/tc2_decoherence_expansion.wl
wolframscript -file tests/wolfram/tc3_entropy_curvature_oscillation.wl
wolframscript -file tests/wolfram/tc4_black_hole_collapse.wl
```

**Run the Python test suite:**

```bash
pytest tests/
```

---

## COMAF-Lite Language Overview

COMAF-Lite models are structured as named entities with a set of typed blocks. Each block describes one physical aspect of the simulation.

| Block | Purpose |
|-------|---------|
| `ENTITY` / `CYCLE` / `FRAME` / `UNITS` | Model header: names the entity, conformal cycle, time domain, and unit system |
| `ENTROPY S:` | Declares entropy evolution (Boltzmann growth, max, timescale) |
| `STATE ψ:` | Declares quantum state evolution (Schrödinger equation, Hamiltonian, initial superposition) |
| `GEOMETRY:` | Specifies the spacetime field equation (Einstein + cosmological constant) |
| `STABILITY:` | Defines the decoherence fragility metric D(t) |
| `IF <condition>:` | Conditional physics block — triggers `collapse`, `warp`, or `emit` when the condition holds |
| `ON cycle.end:` | Hook executed at the end of each conformal cycle |

**Example — Black Hole Formation trigger:**

```comaf
ENTITY: StellarCollapse
CYCLE: CPL-3
FRAME: t ∈ [0.6, 0.9 WarpTick]
UNITS: Planck

STABILITY:
  metric D(t) = exp(-|∇S(t)| · t)

IF curvature R > R_max:
  collapse {
    energy: E_jump
    resolution: lambda_p
    decoherence: D(t)
  }

ON cycle.end:
  S = S / (1 + α)
```

Models are stored in `.comaf` files and processed by the interpreter pipeline:

```
.comaf source → Lexer → Parser → AST → Validator → Transpiler → .wl / .py
```

**Formal language specifications:**
- [`docs/comaf_lite.ebnf`](docs/comaf_lite.ebnf) — Complete EBNF grammar (ISO 14977, Appendix C of paper)
- [`docs/comaf_lite_schema.json`](docs/comaf_lite_schema.json) — JSON Schema Draft 2020-12 for AST serialization (Appendix D of paper)

---

## PNMS Units

COMAF-Lite uses the **Planck-Native Metric System (PNMS)** — a unit system built on Planck-scale quantities so that all physical values remain dimensionless multiples of fundamental constants.

### Core Planck Units (CODATA 2018)

| Quantity | Symbol | SI Value |
|----------|--------|----------|
| Planck Length | λ_p | 1.616 × 10^-35 m |
| Planck Time | t_p | 5.391 × 10^-44 s |
| Planck Mass | m_p | 2.176 × 10^-8 kg |
| Planck Energy | E_p | 1.956 × 10^9 J |

### PNMS Derived Units

| Unit | Definition | SI Equivalent |
|------|-----------|---------------|
| Plameter | 10^35 λ_p | ≈ 1 m |
| Plasecond | 10^44 t_p | ≈ 1 s |
| WarpTick | 10^61 t_p | ≈ 17.1 Gyr (one conformal Planck loop) |
| Quasiplanck | 10^61 λ_p | ≈ 1.616 × 10^26 m (observable universe radius) |

Additional derived units: `Plakilograms`, `Plajoules`, `RicciBits` (Planck curvature), `EntropyTicks` (= k_B).

The `comaf convert` command performs SI ↔ PNMS conversions at the command line.

---

## COMAF × PNMS: Full Definitions

COMAF-Lite DSL keywords and their PNMS/physics correspondence:

### Core Operators and Metrics (§4 of paper)

| COMAF-Lite Keyword/Symbol | Physics Name | PNMS Definition |
|--------------------------|--------------|-----------------|
| `D(t)` | Decoherence Fragility Metric | `exp(-|∇S(t)|·t·c/k_B)` — dimensionless |
| `H_QULT` | QULT-C Hamiltonian | `-ℏ²/2m ∇² + β|ψ|²R − γ ln S(t)` |
| `Ω̂` (cycle.end) | Cycle Transition Operator | `lim_{t→T_c⁻}(Ŝ(t)·Û·R̂⁻¹)` in SOT |
| `χ_CPL` | Causal Loop Stability Invariant | `∫_Σ (R − F_collapse) dA`, requires `R ∈ L¹(Σ)` |
| `F_collapse` | Collapse Function | `Θ(1 − L_eff/λ_p)·(E_jump/E_p)·exp(−ΛR)` |
| `L_eff(v)` | Effective Spatial Resolution | `λ_p·(c/v)^α_v`; α_v=1/2 recovers Lorentz contraction |

### Coupling Constants (unconstrained by experiment)

| Symbol | Name | SI Dimensions | PNMS Dimensions |
|--------|------|---------------|-----------------|
| `β` | Curvature-field coupling | [J·m⁵] | E_p·λ_p⁵ |
| `γ` | Entropy-energy coupling | [J] | E_p |
| `α_r` | Inter-aeonic entropy reset coefficient | dimensionless | dimensionless |
| `α_v` | Velocity-scaling exponent in L_eff | dimensionless | dimensionless |

### PNMS Terminology Mapping (physics ↔ COMAF)

| Physics Term | COMAF Term | First Use |
|--------------|-----------|-----------|
| Wavefunction decoherence / state reduction | Rendering collapse | §4.3 |
| Conformal aeon (Penrose CCC) | CPL (Conformal Planck Loop) | §3 |
| Entropic cost / Bekenstein bound | Rendering budget | §4.5 |
| Planck area / Bekenstein pixel | Rendering tile | §6 |
| Aeonic timescale (1 CPL duration) | WarpTick | §5 |
| Conformal boundary matching | Phase stitching | §4.2 |
| Decoherence rate (Zurek) | Decoherence fragility | §4.3 |
| Discrete spacetime substrate | Planck mesh | §3 L1 |
| Inter-aeon conformal boundary | Aeonic handoff | §4.2 |
| Planck-scale UV cutoff | Rendering resolution | §4.3 |

### COSI Stack Layer Map (§3 of paper)

| Layer | Name | Governing Equation | PNMS Unit |
|-------|------|--------------------|-----------|
| L1 | Quantum Substrate | Planck mesh, λ_p, t_p | Plameter, Plasecond |
| L2 | Wavefunction Evolution | H_QULT ψ = iℏ ∂_t ψ | Quasiplanck |
| L3 | Entropy Flow | S(t) Boltzmann growth, k_B | EntropyTick |
| L4 | Spacetime Geometry | G_μν + Λg_μν = 8πG/c⁴ T_μν | RicciBit |
| L5 | Rendering Control | F_collapse, L_eff(v) | Plameter |
| L6 | Causal Routing / Decoherence | D(t), χ_CPL | dimensionless |
| L7 | Cyclic Transition | Ω̂, CCC conformal boundary | WarpTick |

---

## Project Structure

```
comaf-interpreter/
├── comaf/
│   ├── __init__.py
│   ├── lexer.py               # Tokenizer for the COMAF-Lite DSL
│   ├── parser.py              # Recursive-descent parser → AST
│   ├── ast.py                 # AST node dataclasses
│   ├── validator.py           # Semantic validator / unit consistency checker
│   ├── pnms.py                # Planck-Native Metric System constants & functions
│   ├── cli.py                 # Command-line interface (comaf run / validate / convert)
│   └── transpilers/
│       ├── mathematica.py     # Wolfram Language (.wl) transpiler
│       └── python.py          # Python/NumPy (.py) transpiler
├── stdlib/
│   ├── bounce_cosmology.comaf
│   ├── black_hole_formation.comaf
│   ├── early_universe_inflation.comaf
│   ├── hawking_radiation.comaf
│   ├── heat_death_reboot.comaf
│   └── cmb_freezeout.comaf
├── tests/
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_pnms.py
│   ├── test_transpiler_calibration.py
│   └── wolfram/
│       ├── tc1_bounce_cosmology.wl        # VFR-301
│       ├── tc2_decoherence_expansion.wl   # VFR-302
│       ├── tc3_entropy_curvature_oscillation.wl  # VFR-303
│       └── tc4_black_hole_collapse.wl     # VFR-304
├── docs/
│   ├── QULT-C_v1.3.0-review.pdf  # Current version (75 pages)
│   ├── comaf_lite.ebnf            # EBNF grammar (Appendix C)
│   └── comaf_lite_schema.json     # JSON Schema Draft 2020-12 (Appendix D)
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## Bridge-Finder Vision

COMAF is intended to become a **bridge-finder for physics** — a bidirectional, falsifiable translation layer between formal ontological specifications and executable physical models.

The current COMAF-Lite implementation (this repository) is the first step: a stack-aware transpiler that converts `.comaf` models into Wolfram Language and Python code. Future versions aim to:

1. **Verify** — check whether a `.comaf` model is consistent with COSI Stack constraints (not just syntactically valid)
2. **Infer** — given a Wolfram or Python simulation, identify the COMAF-Lite block structure it corresponds to (reverse transpilation)
3. **Falsify** — expose COMAF-Lite models as machine-readable falsifiability targets, with concrete observational surrogates for each model parameter

The `bridge-finder` framing distinguishes COMAF from ordinary DSLs: the goal is bidirectionality between physics theory and executable specification, not one-way code generation.

---

## Citation

If you use this software or the QULT-C framework in your research, please cite:

```bibtex
@article{qultc2026,
  author    = {Mumin, Roble},
  title     = {{QULT-C}: A Layered Computational Ontology for Quantum Cosmology},
  year      = {2026},
  month     = {March},
  note      = {Preprint v1.3.0-review. Loop 5 converged (0C/0H, 488/522). 75 pages.},
  url       = {https://github.com/RobLe3/COMAF},
}
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

Copyright (c) 2026 Roble Mumin
