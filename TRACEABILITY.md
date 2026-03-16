# COMAF-Lite Traceability Matrix

Maps every claim in the QULT-C paper (v1.337lulz) to its implementation in this repo.

**Legend:**
- ✓ — implemented and verified
- ⚠ — partially implemented (see notes)
- ✗ — intentionally absent or deferred

---

## Paper Sections → Repo Files

| Paper Section | Claim | Repo File(s) | Status | Notes |
|---------------|-------|--------------|--------|-------|
| §3 COSI Stack | 7-layer architecture (L1–L7) | `comaf/ast.py` | ✓ | 8 block types cover all 7 layers |
| §3 COSI Stack | Block-structured DSL syntax | `docs/comaf_lite.ebnf` | ✓ | ISO 14977 EBNF, aligned with paper |
| §3 COSI Stack | COMAF × PNMS addendum (FORCE/POWER/PRESSURE/CURVATURE/CHARGE/ENTROPY_UNIT/UNCERTAINTY) | `comaf/lexer.py`, `comaf/ast.py`, `comaf/parser.py` | ✓ | v1.3.22 — all 7 addendum keywords implemented |
| §4 QULT-C Math | PNMS unit system (Plameter, Plasecond, etc.) | `comaf/pnms.py` | ✓ | CODATA 2018 constants throughout |
| §4 QULT-C Math | Physics functions (L_eff, D(t), F_collapse, E_jump) | `comaf/pnms.py` | ✓ | All functions implemented |
| §4 QULT-C Math | F_collapse GRW normalization ((L₀/λp)⁻³ suppression) | `comaf/pnms.py` (`f_collapse_rate`) | ✓ | v1.3.25 — Fix 2b from technical review |
| §4 QULT-C Math | QULT-C Hamiltonian H_QULT = -ℏ²/2m ∇² + β\|ψ\|²R - γ ln(S) | `stdlib/qultc_hamiltonian.comaf` | ✓ | v1.3.27 — full model with STATE + ENTROPY + STABILITY |
| §4 QULT-C Math | Cycle transition operator Ω̂ | `comaf/ast.py` (TransitionBlockNode) | ⚠ | Structural placeholder; not symbolically evaluated |
| §7 COMAF-Lite | EBNF grammar (Appendix C) | `docs/comaf_lite.ebnf` | ✓ | Identical to paper Appendix C |
| §7 COMAF-Lite | JSON Schema for AST (Appendix D) | `docs/comaf_lite_schema.json` | ✓ | Draft 2020-12, aligned with AST dataclasses |
| §7 COMAF-Lite | Lexer — 41 token types, Unicode, bra-ket | `comaf/lexer.py` | ✓ | 164 lines |
| §7 COMAF-Lite | Parser — recursive descent → AST | `comaf/parser.py` | ✓ | 373+ lines; all block types including addendum |
| §7 COMAF-Lite | Semantic validator (5-level) | `comaf/validator.py` | ✓ | v1.3.19 — syntax + schema + semantic + dimensional + solver levels |
| §7 COMAF-Lite | Wolfram transpiler | `comaf/transpilers/mathematica.py` | ✓ | All block types covered including addendum |
| §7 COMAF-Lite | Python transpiler | `comaf/transpilers/python.py` | ✓ | ODE scaffold with solve_ivp; addendum keywords supported |
| §7 COMAF-Lite | AST serializer/deserializer | `comaf/serializer.py`, `comaf/deserializer.py` | ✓ | v1.3.18 — round-trip verified |
| §7 COMAF-Lite | `comaf simulate` execution | `comaf/runner.py` | ✓ | v1.3.28 — numerical ODE simulation |
| §8 Demo Cases | TC1 — Entropy-Reversal Bounce Cosmology | `tests/wolfram/tc1_bounce_cosmology.wl` | ✓ VFR-301 | Wolfram Cloud verified March 2026 |
| §8 Demo Cases | TC2 — Decoherence-Limited Expansion | `tests/wolfram/tc2_decoherence_expansion.wl` | ✓ VFR-302 | Wolfram Cloud verified March 2026 |
| §8 Demo Cases | TC3 — Entropy-Curvature Oscillation | `tests/wolfram/tc3_entropy_curvature_oscillation.wl` | ✓ VFR-303 | Wolfram Cloud verified March 2026 |
| §8 Demo Cases | TC4 — BH Collapse with Entropy Trigger | `tests/wolfram/tc4_black_hole_collapse.wl` | ✓ VFR-304 | Wolfram Cloud verified March 2026 |
| §8 Demo Cases | TC5 — DHO Model A (entropy damping, τ=10 Ps) | `tests/wolfram/tc5_dho_entropy_damping.wl`, `tests/test_transpiler_calibration.py` | ✓ | Python test stubs added v1.3.20 |
| §8 Demo Cases | TC6 — DHO Model B (rendering damping) | `tests/wolfram/tc6_dho_rendering_damping.wl`, `tests/test_transpiler_calibration.py` | ✓ | Python test stubs added v1.3.20 |
| §6.5 BH Entropy | S_BH ≈ 1.05×10⁷⁷ k_B (solar-mass BH) | `stdlib/bh_entropy_physical.comaf`, `tests/test_physics_fcollapse.py` | ✓ | v1.3.25 — physical parameter model |
| §10 Falsifiability | Decoherence anisotropy V(t,θ) = V₀ exp(-(Γ₀+Γ_QULT·cos²θ)·t) | `stdlib/decoherence_anisotropy.comaf`, `tests/test_physics_anisotropy.py` | ✓ | v1.3.26 — Fix 3c scaffold |
| §9 Propulsion | Speculative propulsion concepts | — | ✓ intentional | Quarantined from core per paper §9 framing |
| Appendix C | EBNF | `docs/comaf_lite.ebnf` | ✓ | 209 lines |
| Appendix D | JSON Schema | `docs/comaf_lite_schema.json` | ✓ | 229 lines |
| Appendix E | Wolfram source (TC1–TC6) | `tests/wolfram/` | ✓ | 6 files |

---

## Stdlib Model Classification

| Model File | Type | Paper Link |
|------------|------|------------|
| `bounce_cosmology.comaf` | transpiler demo | §8 TC1 source |
| `black_hole_formation.comaf` | transpiler demo | §8 TC4 source |
| `early_universe_inflation.comaf` | syntax demo | §7 example |
| `hawking_radiation.comaf` | syntax demo | §7 example |
| `heat_death_reboot.comaf` | syntax demo | §7 example |
| `cmb_freezeout.comaf` | syntax demo | §7 example |
| `dho_model_a_entropy_damping.comaf` | numerically verified (TC5) | §10 falsifiability |
| `dho_model_b_rendering_damping.comaf` | numerically verified (TC6) | §10 falsifiability |
| `addendum_units_demo.comaf` | syntax demo — addendum keywords | §3 COMAF × PNMS addendum |
| `neutron_star_curvature.comaf` | syntax demo — CURVATURE + ENTROPY | §3 addendum, §4 math |
| `photon_emission.comaf` | syntax demo — CHARGE + POWER | §3 addendum, §6.5 BH |
| `bh_entropy_physical.comaf` | physical parameter model | §6.5 BH entropy, Fix 2b |
| `decoherence_anisotropy.comaf` | prediction scaffold | §10.3 falsifiability, Fix 3c |
| `qultc_hamiltonian.comaf` | Hamiltonian demo | §4.2 QULT-C Hamiltonian |

---

## Validator Coverage

The validator (`comaf/validator.py`) currently checks:

| Check Type | Level | Status |
|------------|-------|--------|
| Header completeness (ENTITY/CYCLE/FRAME/UNITS) | semantic | ✓ |
| Unit system (SI vs. PNMS) | semantic | ✓ warning |
| ENTROPY: init ≥ 0, max ≥ init, scale > 0 | semantic | ✓ |
| ENTROPY: time unit recognition | dimensional | ✓ |
| STABILITY: D(t) ∈ [0, 1] literal check | dimensional | ✓ |
| COLLAPSE: energy ≤ E_p | semantic | ✓ warning |
| STATE: Hamiltonian presence | semantic | ✓ info |
| Dimensional consistency (DimensionalChecker) | dimensional | ✓ v1.3.19 |
| Scope checking (ScopeChecker) | semantic | ✓ v1.3.19 |
| JSON Schema conformance | schema | ✓ v1.3.17 (top-level fields) |
| Full CAS symbolic evaluation | dimensional | ⚠ deferred (sympy, v1.3.32) |

---

## Known Gaps (Explicitly Deferred)

| Gap | Rationale | Target |
|-----|-----------|--------|
| IR layer between AST and transpilers | Large refactor; not required for paper claims | Phase 4 / v1.3.31 |
| Full CAS symbolic evaluation (sympy) | Requires sympy; paper claims "partial" only | Phase 4 / v1.3.32 |
| wolframscript automated runner for TC files | Requires Wolfram license in CI | Out of scope |
| Denotational semantics / transpiler soundness proof | Research task, companion paper | Research |
| Ω̂ symbolic evaluation | Pure interpretive machinery; stored as string | Research |
