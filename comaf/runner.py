"""
COMAF-Lite Model Runner
Executes a parsed model numerically using scipy.integrate.solve_ivp.

v1.3.28: Initial implementation. Handles ENTROPY + STABILITY blocks.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import math

from .ast import ProgramNode, EntropyBlockNode, StabilityBlockNode, CollapseBlockNode
from .pnms import PLASECOND, WARPTICK, LAMBDA_P


@dataclass
class SimulationResult:
    """Numerical output from running a COMAF-Lite model."""
    t: List[float] = field(default_factory=list)
    S: List[float] = field(default_factory=list)
    D: List[float] = field(default_factory=list)
    entity: str = ""
    cycle: str = ""
    steps: int = 0
    t_end: float = 0.0
    collapse_triggered: bool = False
    collapse_time: Optional[float] = None


def run_model(program: ProgramNode,
              t_end: float = 100.0,
              steps: int = 1000,
              alpha_d: float = 1e-9,
              grad_s: float = 1.0) -> SimulationResult:
    """
    Run a COMAF-Lite model numerically.

    Extracts ENTROPY and STABILITY blocks, sets up an ODE system:
      dS/dt = (S_max - S) / tau
      dD/dt = -alpha_d * grad_s * D

    Checks for COLLAPSE condition (D < threshold).

    Parameters
    ----------
    program   : parsed ProgramNode
    t_end     : simulation end time in Plaseconds
    steps     : number of output time steps
    alpha_d   : decoherence coupling (upper bound: 3e-9 from BEC data)
    grad_s    : entropy gradient magnitude (PNMS units)

    Returns
    -------
    SimulationResult with t, S, D arrays and metadata.
    """
    try:
        from scipy.integrate import solve_ivp
        import numpy as np
    except ImportError as e:
        raise ImportError("scipy and numpy required for simulation") from e

    # Extract parameters from AST
    entropy = next((b for b in program.blocks if isinstance(b, EntropyBlockNode)), None)
    collapse = next((b for b in program.blocks if isinstance(b, CollapseBlockNode)), None)

    if entropy is None:
        # No entropy block — run trivial simulation
        t_arr = np.linspace(0, t_end * PLASECOND, steps)
        return SimulationResult(
            t=t_arr.tolist(), S=[1.0] * steps, D=[1.0] * steps,
            entity=program.entity, cycle=program.cycle,
            steps=steps, t_end=t_end,
        )

    S_init = entropy.init
    S_max = entropy.max_val
    tau_ps = entropy.scale  # already in Plaseconds (from the scale field)

    # Run ODE in Plaseconds (dimensionless for this model)
    t_span_ps = (0.0, t_end)
    t_eval_ps = np.linspace(0, t_end, steps)

    def odes(t, y):
        S, D = y
        dS_dt = (S_max - S) / tau_ps if tau_ps > 0 else 0.0
        dD_dt = -alpha_d * grad_s * D
        return [dS_dt, dD_dt]

    sol = solve_ivp(
        odes, t_span_ps, [S_init, 1.0],
        t_eval=t_eval_ps, method="RK45", dense_output=False,
        rtol=1e-6, atol=1e-10,
    )

    t_plaseconds = sol.t.tolist()
    S_arr = sol.y[0].tolist()
    D_arr = sol.y[1].tolist()

    # Check collapse condition
    collapse_triggered = False
    collapse_time = None
    if collapse is not None:
        # Extract threshold from condition string (look for numeric literal)
        d_threshold = 0.01  # default
        import re
        m = re.search(r'<\s*([0-9.e+\-]+)', collapse.condition)
        if m:
            try:
                d_threshold = float(m.group(1))
            except ValueError:
                pass
        for i, d in enumerate(D_arr):
            if d < d_threshold:
                collapse_triggered = True
                collapse_time = t_plaseconds[i]
                break

    return SimulationResult(
        t=t_plaseconds,
        S=S_arr,
        D=D_arr,
        entity=program.entity,
        cycle=program.cycle,
        steps=len(t_plaseconds),
        t_end=t_end,
        collapse_triggered=collapse_triggered,
        collapse_time=collapse_time,
    )
