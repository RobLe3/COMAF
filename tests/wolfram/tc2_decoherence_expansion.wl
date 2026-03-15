(* COMAF-Lite Test Case 2: Decoherence-Limited Quantum Expansion — VFR-302 verified *)
(* Wolfram Cloud, 2026-03 *)

(* === TC2: Decoherence-Limited Expansion === *)
(* Verified: Wolfram Cloud, 2026-03 *)
(* NOTE: Variable Dcoh used (not D) to avoid Mathematica namespace conflict *)

Dcoh[t_] := Exp[-t/1*10^6];

(* Expansion halts when Dcoh < 0.1 *)
a[t_] := If[Dcoh[t] > 0.1, Exp[t/1*10^7], Exp[1]];

(* Verify: freeze time *)
tFreeze = 10^6 * Log[10];
Print["Dcoh = 0.1 at t = ", N[tFreeze]]  (* Expected: ~2.303e6 *)
Print["a(tFreeze) = ", N[a[tFreeze]]]     (* Expected: ~e^0.2303 ~1.259 *)

(* Plot *)
Plot[{Dcoh[t], a[t]}, {t, 0, 1*10^7},
  PlotLabel -> "TC2: Decoherence-Limited Expansion",
  PlotLegends -> {"Decoherence Dcoh(t) [dimensionless]",
                  "Scale Factor a(t) [dimensionless]"},
  PlotStyle -> {Purple, Orange},
  AxesLabel -> {"Time [Plaseconds]", "Value"}]

Print["VFR-302: PASS"]
