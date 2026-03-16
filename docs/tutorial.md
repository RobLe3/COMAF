# COMAF-Lite Tutorial

A beginner-friendly guide to writing and running COMAF-Lite physics models.

---

## What is COMAF-Lite?

**COMAF-Lite** is a small declarative language for writing *physical models* — descriptions of how a physical system evolves over time.

Instead of writing Python or differential equations from scratch, you describe your system in named blocks:

```
ENTROPY ...      ← how entropy evolves
STATE ...        ← quantum state and its Hamiltonian
STABILITY ...    ← when does the system decohere?
IF D(t) < 0.1:  ← what happens at a threshold?
  collapse { ... }
```

COMAF-Lite is compiled (transpiled) to:
- **Wolfram Language** (`.wl`) for symbolic computation
- **Python/NumPy** (`.py`) for numerical simulation

It is the reference language for the QULT-C framework — a layered computational ontology for quantum cosmology. But you do not need to know the theory to use it.

---

## Installation

```bash
pip install -e .          # standard install from source
pip install -e ".[dev]"   # also installs pytest for running tests
```

**Requirements:** Python ≥ 3.10, NumPy ≥ 1.24, SciPy ≥ 1.10

Verify:

```bash
comaf --version
# → comaf 1.337.0
```

---

## Your First Model

Create a file called `my_first.comaf`:

```comaf
# my_first.comaf — minimal working model

ENTITY: SimplePendulum
CYCLE: CPL-1
FRAME: t in [0, 100 Plaseconds]
UNITS: Planck

ENTROPY S:
  evolve Boltzmann {
    init: 1.0
    max: 10.0
    scale: 10.0 Plaseconds
  }

STABILITY:
  metric D(t) = exp(-0.1 * t)

IF D(t) < 0.01:
  collapse {
    energy: E_p
    resolution: lambda_p
  }
```

**Validate it:**

```bash
comaf validate my_first.comaf
# → ✓ my_first.comaf: valid
```

**Simulate it:**

```bash
comaf simulate my_first.comaf --t-end 50 --steps 10
```

Output:
```
=== Simulation: my_first.comaf ===
Entity: SimplePendulum  Cycle: CPL-1
t_end: 50.0 Plaseconds  steps: 10

   t (Ps)               S            D
------------------------------------------
       0.000    1.000000e+00    1.000000
       5.556    4.260756e+00    0.573274
      11.111    6.608432e+00    0.328655
      ...
      50.000    9.933737e+00    0.006738

✗ Collapse triggered at t = 46.052 Plaseconds
✓ Simulation complete: 10 steps
```

**Transpile to Python:**

```bash
comaf run my_first.comaf --target python
# → Writes my_first.py
```

**Transpile to Wolfram:**

```bash
comaf run my_first.comaf --target mathematica
# → Writes my_first.wl
```

---

## The Model Header

Every COMAF-Lite model starts with four required header fields:

```comaf
ENTITY: <name>        # The physical entity being modeled
CYCLE: CPL-<n>        # Conformal Planck Loop (e.g. CPL-1, CPL-3)
FRAME: t in [<start>, <end> <unit>]
UNITS: Planck         # or SI or PNMS
```

- `ENTITY` is just a label — any identifier works.
- `CYCLE` uses the CPL-n format from the paper. Use CPL-1 for a simple one-cycle model.
- `FRAME` describes the time range. Units: `Plaseconds`, `WarpTick`, `s`.
- `UNITS` sets the default unit system. Use `Planck` for most models.

**Example:**
```comaf
ENTITY: BouncingUniverse
CYCLE: CPL-4
FRAME: t in [0, 1 WarpTick]
UNITS: Planck
```

---

## Block Reference

### ENTROPY

Describes how the entropy of the system evolves toward a maximum via Boltzmann relaxation.

```comaf
ENTROPY S:
  evolve Boltzmann {
    init: 1e120        # initial entropy (in units of k_B)
    max: 1e121         # maximum attainable entropy
    scale: 1e9 Plaseconds   # characteristic relaxation time τ
  }
```

The ODE used by the simulator is:
```
dS/dt = (S_max - S) / τ
```

After one time constant τ, S reaches `S_init + (1 - 1/e) × (S_max - S_init)` ≈ 63% of the way to S_max.

**Key fields:**
| Field | Type | Description |
|-------|------|-------------|
| `init` | number | Initial entropy value |
| `max` | number | Maximum entropy value (must be ≥ init) |
| `scale` | number + unit | Time constant τ (must use a time unit) |

---

### STATE

Describes the quantum state of the system and its Hamiltonian.

```comaf
STATE psi:
  evolve Schrodinger {
    init: superposition[|contracting>, |expanding>]
    hamiltonian: H_QULT(R, S)
  }
```

Or with a custom Hamiltonian:

```comaf
STATE psi:
  evolve Schrodinger {
    init: |ground>
    hamiltonian: -hbar^2/(2*m) * nabla^2(psi) + beta*|psi|^2*R - gamma*ln(S(t))
  }
```

**Key fields:**
| Field | Type | Description |
|-------|------|-------------|
| `init` | quantum state or number | Initial state: `\|name>`, `superposition[...]`, or a scalar |
| `hamiltonian` | expression | The system's Hamiltonian (string expression) |

---

### GEOMETRY

Specifies the spacetime field equation. Usually Einstein's equations.

```comaf
GEOMETRY:
  field_equation: G + Lambda*g = (8*pi*G/c^4) * <T>
```

This block is transpiled as a symbolic comment in Wolfram and Python output — it does not affect the numerical simulation. Its purpose is to document the geometric structure of the model.

---

### STABILITY

Defines the decoherence fragility metric D(t) — a dimensionless value in [0, 1] where:
- D = 1 → fully coherent
- D → 0 → fully decohered

```comaf
STABILITY:
  metric D(t) = exp(-alpha_D * |gradS| * t)
```

In the simulator, this is evolved as:
```
dD/dt = -alpha_d × grad_s × D
```

The STABILITY metric feeds into IF condition blocks.

---

### IF (Collapse / Warp / Emit)

Conditional blocks that trigger when a condition is met. Three action types are supported:

**Collapse** — system transitions to a decohered state:
```comaf
IF D(t) < 0.1:
  collapse {
    energy: E_p
    resolution: lambda_p
    decoherence: D(t)
  }
```

**Warp** — system enters a warp-state (speculative propulsion, quarantined from core physics):
```comaf
IF D(t) > 0.99:
  warp {
    velocity: 0.5 c
    safety: D(t) > 0.9
    target: sector::Alpha::Centauri->star::A
  }
```

**Emit** — system emits radiation (e.g., Hawking radiation):
```comaf
IF D(t) < 0.05:
  emit {
    energy: E_hawking
    decay: |evaporated>
  }
```

---

### ON (Transition)

Hook executed at the end of each conformal cycle:

```comaf
ON cycle.end:
  S = S / (1 + alpha_r)
  psi *= e^(i * pi)
```

Statements are assignments and state transformations applied at the cycle boundary.

---

### COMAF × PNMS Addendum Blocks (Advanced)

Seven additional block types from the COMAF × PNMS addendum (v1.3.22) cover extended physics:

```comaf
FORCE F_grav: G * M * m / r^2  PlaNewtons
POWER P_hawking: hbar * c^6 / (15360 * pi * G^2 * M^2)  PlaWatts
PRESSURE p_degeneracy: hbar^2 / (5 * m_e) * (3 * pi^2 * n)^(5/3)  PlaPascals
CURVATURE R_surface: 2 * G * M / (c^2 * R_ns^3)  Ricci-Bits
CHARGE q_planck: sqrt(4 * pi * epsilon_0 * hbar * c)  PlaCoulombs
ENTROPY_UNIT S_boltzmann: k_B * ln(Omega)
UNCERTAINTY delta_x: hbar / (2 * delta_p)
```

Each of these transpiles to a named function in both Python and Wolfram.

---

## The CLI Commands

### `comaf validate`

Checks a model for syntax, schema, semantic, and dimensional errors.

```bash
comaf validate model.comaf              # standard check
comaf validate model.comaf --strict     # warnings become errors
comaf validate model.comaf --report json  # machine-readable output
```

Example JSON output:
```json
{
  "valid": true,
  "syntax": "ok",
  "schema": "ok",
  "semantic": "ok",
  "dimensional": "ok",
  "solver": null,
  "issues": []
}
```

### `comaf run`

Transpiles to Wolfram or Python:

```bash
comaf run model.comaf --target mathematica  # writes model.wl
comaf run model.comaf --target python       # writes model.py
```

### `comaf simulate`

Runs the model numerically using SciPy's ODE solver:

```bash
comaf simulate model.comaf                   # 100 Ps, 100 steps (default)
comaf simulate model.comaf --t-end 500 --steps 200
```

Time is in **Plaseconds** (1 Plasecond ≈ 5.391 s in SI).

### `comaf explain`

Shows the per-block AST structure and transpiler mapping:

```bash
comaf explain model.comaf
```

Output:
```
=== COMAF-Lite Model: bounce_cosmology.comaf ===
Entity: BouncingUniverse  |  Cycle: CPL-n  |  Units: Planck
Frame:  t in [0, 1 WarpTick]

Block 1: EntropyBlockNode
  Source:  ENTROPY S (init=1.000e+120, max=1.000e+121, scale=1000000000.0 Plaseconds)
  Wolfram: S0S = 1.0e+120;
  Python:  def entropy_S(t):

Block 2: StateBlockNode
  Source:  STATE psi (init='superposition[|contracting>, |expanding>]')
  Wolfram: psi[t_] := {Sqrt[1/2]|contracting>, Sqrt[1/2]|expanding>};
  Python:  (STATE blocks not directly transpiled to Python functions)
...
```

### `comaf doctor`

Repo health check — verifies all spec files, stdlib models, and PNMS constants:

```bash
comaf doctor
```

Output:
```
=== COMAF-Lite Health Check ===

Spec files:
  ✓ EBNF grammar: docs/comaf_lite.ebnf
  ✓ JSON Schema: docs/comaf_lite_schema.json
  ✓ TRACEABILITY.md present

Stdlib models:
  ✓ Stdlib count: 14 models found
  ✓ All 14 stdlib models parse and validate

Wolfram test cases:
  ✓ Wolfram TC files: 6/6 found
  ...

PNMS constants (CODATA 2018):
  ✓ λ_p = 1.6163e-35 m (expected ~1.616×10⁻³⁵ m)
  ✓ t_p = 5.3912e-44 s (expected ~5.391×10⁻⁴⁴ s)
  ✓ E_p = 1.9561e+09 J (expected ~1.956×10⁹ J)

Result: all checks passed
```

### `comaf convert`

Convert SI values to PNMS units:

```bash
comaf convert --si-to-pnms 1.0 m
# → 1.0 m = 6.187e-36 Plameters

comaf convert --si-to-pnms 1.0 s
# → 1.0 s = 1.855e-44 Plaseconds
```

---

## PNMS Units: What They Mean

COMAF-Lite uses the **Planck-Native Metric System (PNMS)** — all quantities are dimensionless multiples of Planck-scale constants.

**Key conversion values (CODATA 2018):**

| PNMS Unit | Definition | SI Value |
|-----------|-----------|----------|
| Plameter | 10³⁵ × λ_p | **1.616 m** (not 1 m) |
| Plasecond | 10⁴⁴ × t_p | **5.391 s** (not 1 s) |
| WarpTick | 10⁶¹ × t_p | ~17.1 Gyr |
| EntropyTick | = k_B | 1.381 × 10⁻²³ J/K |

> **Common mistake:** Plameter ≈ 1.616 m and Plasecond ≈ 5.391 s. They are NOT equal to 1 m / 1 s. The factor comes from the precise CODATA 2018 value of the Planck length.

**Checking constants in Python:**
```python
import comaf.pnms as pnms

print(pnms.PLAMETER)    # 1.616255e+00 m
print(pnms.PLASECOND)   # 5.391247e+00 s
print(pnms.LAMBDA_P)    # 1.616255e-35 m  (Planck length)
print(pnms.T_P)         # 5.391247e-44 s  (Planck time)
print(pnms.E_P)         # 1.956082e+09 J  (Planck energy)
```

---

## Walking Through a Stdlib Model

Let's look at `stdlib/bounce_cosmology.comaf` — the primary demo model for TC1.

```bash
cat stdlib/bounce_cosmology.comaf
```

Key structure:
1. **ENTITY / CYCLE / FRAME / UNITS** — "BouncingUniverse, CPL-n, 0 to 1 WarpTick, Planck units"
2. **ENTROPY** — entropy grows from 1e120 toward 1e121 over 1 billion Plaseconds
3. **STATE** — quantum state in superposition of `|contracting>` and `|expanding>`
4. **GEOMETRY** — Einstein field equation annotated with QULT-C stress-energy
5. **STABILITY** — decoherence metric D(t) = exp(-|∇S| · t)
6. **ON cycle.end** — entropy reset + state transformation at cycle boundary

Try:
```bash
comaf validate stdlib/bounce_cosmology.comaf
comaf explain stdlib/bounce_cosmology.comaf
comaf run stdlib/bounce_cosmology.comaf --target python
comaf simulate stdlib/bounce_cosmology.comaf --t-end 1000
```

---

## Running the Test Suite

```bash
pytest tests/              # run all 289 tests
pytest tests/ -v           # verbose output
pytest tests/test_numerical_calibration.py -v  # just calibration tests
```

The test suite verifies:
- Lexer and parser correctness
- Round-trip AST serialization
- PNMS constant values (CODATA 2018)
- Simulator convergence and collapse detection
- All 14 stdlib models parse and validate

---

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Parse error: unexpected token` | Missing colon after block keyword | Check `ENTROPY S:`, `STATE psi:`, etc. |
| `Schema: 'cycle' must match CPL-n` | Cycle ID not matching `CPL-<n>` pattern | Use `CPL-1`, `CPL-3`, etc. |
| `Entropy init must be >= 0` | Negative entropy value | Use a positive init value |
| `D(t) literal out of [0,1] range` | Literal stability value > 1 | Use a formula, not a literal > 1 |
| Simulation shows S stuck at init | τ too large for t_end | Increase `--t-end` or decrease `scale:` |

---

## Next Steps

- Browse the stdlib models in `stdlib/` for more examples
- See [`TRACEABILITY.md`](../TRACEABILITY.md) for the paper section → repo file mapping
- See [`docs/comaf_lite.ebnf`](comaf_lite.ebnf) for the complete grammar
- See [`docs/comaf_lite_schema.json`](comaf_lite_schema.json) for the JSON Schema
