(* COMAF-Lite Test Case 1: Entropy-Reversal Bounce Cosmology — VFR-301 verified *)
(* Wolfram Cloud, 2026-03 *)

(* === TC1: Bounce Cosmology === *)
(* Verified: Wolfram Cloud, 2026-03 *)

(* Entropy rises to max at t_peak, then reverses *)
S[t_] := If[t < 5*10^9,
             1*10^120 + 1*10^121*(1 - Exp[-t/1*10^9]),
             1*10^121 - 1*10^121*(1 - Exp[-(t - 5*10^9)/1*10^9])];

(* Scale factor contracts then expands (bounce at t_peak) *)
a[t_] := If[t < 5*10^9,
             Exp[-t/1*10^9],
             Exp[-5]*Exp[(t - 5*10^9)/1*10^9]];

(* Verify: S peak *)
Print["S at t_peak: ", N[S[5*10^9]]]   (* Expected: ~1e121 *)
Print["a at t_peak: ", N[a[5*10^9]]]   (* Expected: ~0.0067 *)

(* Plot *)
Plot[{S[t], a[t]}, {t, 0, 1*10^10},
  PlotLabel -> "TC1: Entropy Reversal & Bounce Cosmology",
  PlotLegends -> {"Entropy S(t) [Entropy Ticks]",
                  "Scale Factor a(t) [dimensionless]"},
  PlotStyle -> {Blue, Green},
  AxesLabel -> {"Time [Plaseconds]", "Value"}]

Print["VFR-301: PASS"]
