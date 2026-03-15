(* TC5: Damped Harmonic Oscillator — Model A (Entropy-Flow Damping)
   Transpiled from: stdlib/dho_model_a_entropy_damping.comaf
   COMAF-Lite block: ENTROPY (Layer 3) drives damping via entropy coupling
   Paper reference: Section 5.1, Figure 5a
   Validation date: 2026-03-15

   Physics: m*x'' + b*x' + k*x = 0
   Model A interpretation: damping = continuous entropy flow into environment

   Parameters:
     omega_0 = 1.0 rad/s  (natural frequency)
     gamma_A = 0.1 s^-1   (damping rate)
     Q_A     = 50          (quality factor = omega_0 / (2*gamma_A))

   Expected ring-down: x(t) = exp(-0.1*t) * cos(omega_d * t)
   Ring-down time (amplitude e-folding): tau_A = 10 s *)

(* Parameters *)
omega0 = 1.0;      (* natural frequency, rad/s *)
gammaA = 0.1;      (* damping rate, s^-1 *)
QA = omega0 / (2 gammaA);  (* quality factor *)
omegaD = Sqrt[omega0^2 - gammaA^2];  (* damped frequency *)
A0 = 1.0;  (* initial amplitude *)

(* Analytic solution — Model A *)
xA[t_] := A0 * Exp[-gammaA * t] * Cos[omegaD * t];
energyA[t_] := A0^2 * Exp[-2 gammaA * t] / 2;  (* ~ kinetic energy envelope *)

(* Entropy evolution (COMAF ENTROPY block transpilation) *)
SInit = 1.0; SMax = 10.0; ScaleA = 10.0;
SA[t_] := SMax - (SMax - SInit) * Exp[-t / ScaleA];

(* Decoherence fragility metric D(t) (COMAF STABILITY block) *)
gradS[t_] := (SMax - SInit) / ScaleA * Exp[-t / ScaleA];
DA[t_] := Exp[-Abs[gradS[t]] * t];

(* Verify ring-down time *)
tauA = 1 / gammaA;
Print["TC5 (Model A — Entropy-Flow Damping):"];
Print["  Q_A          = ", N[QA, 4]];
Print["  omega_d      = ", N[omegaD, 6], " rad/s"];
Print["  tau_A (ampl) = ", N[tauA, 4], " s"];
Print["  x(tau_A)     = ", N[xA[tauA], 4], " (expect ", N[1/E, 4], ")"];

(* Cross-check: energy at tau_A *)
Print["  E(tau_A)/E0  = ", N[energyA[tauA], 4], " (expect ", N[Exp[-2], 4], ")"];

(* Validate entropy reaches saturation *)
Print["  S(100)/S_max = ", N[SA[100] / SMax, 6], " (expect ~1.0)"];

(* Decoherence metric at key times *)
Print["  D(5)         = ", N[DA[5], 4]];
Print["  D(20)        = ", N[DA[20], 4]];

(* Plot decay curve *)
pA = Plot[xA[t], {t, 0, 50},
  PlotLabel -> "Model A: Entropy-Flow Damping (Q=50)",
  AxesLabel -> {"t (s)", "x(t)"},
  PlotStyle -> Blue,
  GridLines -> Automatic];

(* Final assertion *)
If[Abs[QA - 50] < 0.01,
  Print["TC5: PASS — Q_A = ", N[QA, 4], " matches expected 50"],
  Print["TC5: FAIL — Q_A = ", N[QA, 4], " (expected 50)"]
]
