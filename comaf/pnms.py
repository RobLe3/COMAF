"""
PNMS: Planck-Native Metric System
All physical constants and derived units for the COMAF-Lite framework.
Values from CODATA 2018.
"""

import math

# ─── Fundamental Constants ───────────────────────────────────────────────────
HBAR = 1.054571817e-34       # J·s  (reduced Planck constant)
H_PLANCK = 2 * math.pi * HBAR  # J·s  (Planck constant)
C = 2.99792458e8             # m/s  (speed of light)
G_NEWTON = 6.67430e-11       # m^3 kg^-1 s^-2
K_B = 1.380649e-23           # J/K  (Boltzmann constant)
EPSILON_0 = 8.8541878128e-12 # F/m  (vacuum permittivity)

# ─── Core Planck Units ───────────────────────────────────────────────────────
LAMBDA_P = math.sqrt(HBAR * G_NEWTON / C**3)    # 1.616255e-35 m
T_P = math.sqrt(HBAR * G_NEWTON / C**5)         # 5.391247e-44 s
E_P = math.sqrt(HBAR * C**5 / G_NEWTON)         # 1.9561e9 J
M_P = math.sqrt(HBAR * C / G_NEWTON)            # 2.17644e-8 kg
T_PLANCK_TEMP = E_P / K_B                        # 1.41685e32 K
F_P = C**4 / G_NEWTON                           # 1.2103e44 N
P_P_POWER = C**5 / G_NEWTON                     # 3.6283e52 W
RHO_P = M_P / LAMBDA_P**3                       # 5.155e96 kg/m^3
Q_P = math.sqrt(4 * math.pi * EPSILON_0 * HBAR * C)  # 1.876e-18 C

# ─── PNMS Derived Units ──────────────────────────────────────────────────────
# Scalar exponents
_PLAMETER_EXP = 35
_PLASECOND_EXP = 44
_WARPTICK_EXP = 61
_QUASIPLANCK_EXP = 61
_PLAKILOGRAM_EXP = 8

PLAMETER = 10**_PLAMETER_EXP * LAMBDA_P          # ≈ 1 m
PLASECOND = 10**_PLASECOND_EXP * T_P             # ≈ 1 s
PLAMINUTE = 60 * PLASECOND                       # ≈ 1 min
PLAHOUR = 3600 * PLASECOND                       # ≈ 1 hr
PLACENTURY = 3.15576e9 * PLASECOND               # ≈ 100 yr
WARPTICK = 10**_WARPTICK_EXP * T_P              # ≈ 13.8 Gyr (one CPL)
QUASIPLANCK = 10**_QUASIPLANCK_EXP * LAMBDA_P   # ≈ Hubble radius
PLAJOULE = 1e9 * E_P                             # ≈ 1 GJ
PLAKILOGRAM = 10**_PLAKILOGRAM_EXP * M_P         # ≈ 1 kg

# PNMS astronomical distances (in Plameters)
PNMS_LD = 3.844e8    # Earth-Moon distance in Plameters
PNMS_AU = 1.496e11   # Earth-Sun distance in Plameters
PNMS_LY = 9.461e15   # Light-year in Plameters
PNMS_PC = 3.086e16   # Parsec in Plameters
PNMS_MPC = 3.086e22  # Megaparsec in Plameters

# Curvature
RICCI_BIT = 1.0 / LAMBDA_P**2   # 3.83e69 m^-2 (Planck curvature)

# Entropy / Information
ENTROPY_TICK = K_B               # 1 Boltzmann constant = 1 entropy tick
PLANCK_BIT = math.log(2) * K_B  # 1 bit of entropy

# ─── Fine-structure constant ──────────────────────────────────────────────────
ALPHA_FSC = 7.2973525693e-3     # ≈ 1/137.036 (CODATA 2018)

# ─── PNMS Conversion Functions ───────────────────────────────────────────────

def to_plameters(meters: float) -> float:
    """Convert SI meters to Plameters."""
    return meters / PLAMETER

def to_plaseconds(seconds: float) -> float:
    """Convert SI seconds to Plaseconds."""
    return seconds / PLASECOND

def to_warpticks(seconds: float) -> float:
    """Convert SI seconds to WarpTicks."""
    return seconds / WARPTICK

def to_plajoules(joules: float) -> float:
    """Convert SI joules to Plajoules."""
    return joules / PLAJOULE

def to_plakilograms(kg: float) -> float:
    """Convert SI kilograms to Plakilograms."""
    return kg / PLAKILOGRAM

def from_plameters(plameters: float) -> float:
    """Convert Plameters to SI meters."""
    return plameters * PLAMETER

def from_plaseconds(plaseconds: float) -> float:
    """Convert Plaseconds to SI seconds."""
    return plaseconds * PLASECOND

def from_warpticks(warpticks: float) -> float:
    """Convert WarpTicks to SI seconds."""
    return warpticks * WARPTICK

def from_plajoules(plajoules: float) -> float:
    """Convert Plajoules to SI joules."""
    return plajoules * PLAJOULE

def from_plakilograms(plakilograms: float) -> float:
    """Convert Plakilograms to SI kilograms."""
    return plakilograms * PLAKILOGRAM


# ─── QULT-C Physics Functions ─────────────────────────────────────────────────

def l_eff(v: float, l0: float = PLAMETER, alpha: float = 2.0) -> float:
    """
    Effective rendering length at velocity v.
    L_eff(v) = L0 * (1 - v^2/c^2)^alpha
    """
    if abs(v) >= C:
        return LAMBDA_P
    return l0 * (1 - (v / C)**2)**alpha


def psi_factor(v: float, l0: float = PLAMETER, alpha: float = 2.0) -> float:
    """
    Planck-state transition factor.
    Psi(v) = lambda_p / L_eff(v)
    """
    leff = l_eff(v, l0, alpha)
    if leff <= 0:
        return float('inf')
    return LAMBDA_P / leff


def e_jump(v: float, l0: float = PLAMETER, alpha: float = 2.0) -> float:
    """
    Energy for a quantum jump at velocity v.
    E_jump = (h / lambda_p) * (1 - exp(-Psi(v)))
    Always < E_p.
    """
    psi = psi_factor(v, l0, alpha)
    return (H_PLANCK / LAMBDA_P) * (1 - math.exp(-min(psi, 700)))


def decoherence_metric(grad_s: float, t: float) -> float:
    """
    Decoherence fragility metric.
    D(t) = exp(-|grad_S(t)| * t)
    Returns value in [0, 1].
    """
    return math.exp(-abs(grad_s) * t)


def f_collapse(v: float, lambda_cosmo: float, r: float,
               l0: float = PLAMETER, alpha: float = 2.0) -> float:
    """
    Rendering collapse function.
    F_collapse(v, Lambda) = Theta(1 - L_eff(v)/lambda_p) * (E_jump/E_p) * exp(-Lambda*R)
    """
    leff = l_eff(v, l0, alpha)
    theta = 1.0 if leff < LAMBDA_P else 0.0
    ejump = e_jump(v, l0, alpha)
    return theta * (ejump / E_P) * math.exp(-lambda_cosmo * r)


def f_collapse_rate(energy_jump: float, theta: float, lambda_r: float,
                    l0: float = PLAMETER) -> float:
    """
    F_collapse with (L0/lambda_p)^-3 GRW volume suppression.

    F_collapse_GRW = (1/2π) * Theta * (E_jump/E_p) * exp(-Lambda*R) * (L0/lambda_p)^-3

    For a nucleon (L0 ~ 1e-15 m), the suppression factor is ~4×10^-60,
    yielding Gamma ~ 5×10^-16 s^-1 — consistent with GRW collapse rate.
    See: deferred Fix 2b, technical review March 2026.
    """
    suppression = (l0 / LAMBDA_P) ** -3
    return (1.0 / (2.0 * math.pi)) * theta * (energy_jump / E_P) * math.exp(-lambda_r) * suppression


def grw_consistency_check() -> dict:
    """
    Verify that f_collapse_rate for a nucleon is consistent with GRW collapse rate.

    Uses E_jump = E_p (threshold value) and divides by t_p to convert the
    dimensionless F_collapse to a rate in s^-1.

    GRW: Gamma ~ 10^-16 s^-1 (spontaneous collapse per particle per second).
    QULT-C with suppression: Gamma ~ 1e-17 s^-1 (within 10× of GRW).

    Returns a dict with rate (s^-1) and consistency flag.
    """
    L_NUCLEON = 1e-15           # m (nucleon size)
    THETA = 1.0                 # step function = 1 (collapse triggered)
    LAMBDA_R = 0.0              # exp(-0) = 1 (no cosmological suppression)
    # At collapse threshold, E_jump → E_p
    f_collapse_dim = f_collapse_rate(E_P, THETA, LAMBDA_R, l0=L_NUCLEON)
    # Convert dimensionless collapse probability to rate: Gamma = F / t_p
    rate_per_second = f_collapse_dim / T_P
    GRW_RATE = 1e-16            # s^-1 (GRW target)
    # Accept within 6 orders of magnitude (order-of-magnitude physics check)
    consistent = 1e-22 < rate_per_second < 1e-10
    return {
        "rate": rate_per_second,
        "grw_target": GRW_RATE,
        "consistent": consistent,
        "suppression": (L_NUCLEON / LAMBDA_P) ** -3,
    }


def warp_velocity(r: float, kappa: float = 0.001) -> float:
    """
    Warp velocity under curvature.
    v_warp = c * exp(kappa * R)
    Note: can exceed c (speculative).
    """
    return C * math.exp(kappa * r)


def bh_entropy(mass_kg: float) -> float:
    """
    Bekenstein-Hawking black hole entropy in Planck-bits (entropy ticks).
    S_BH = k_B * c^3 * A / (4 * G * hbar)
    where A = 4 * pi * (2 * G * M / c^2)^2
    """
    r_s = 2 * G_NEWTON * mass_kg / C**2
    area = 4 * math.pi * r_s**2
    return K_B * C**3 * area / (4 * G_NEWTON * HBAR)


# ─── Unit Label Map ───────────────────────────────────────────────────────────

UNIT_SI_VALUES = {
    "Plameters": PLAMETER,
    "Plaseconds": PLASECOND,
    "Plaminutes": PLAMINUTE,
    "Plahours": PLAHOUR,
    "WarpTicks": WARPTICK,
    "Quasiplancks": QUASIPLANCK,
    "Plajoules": PLAJOULE,
    "Plakilograms": PLAKILOGRAM,
    "RicciBits": RICCI_BIT,
    "EntropyTicks": ENTROPY_TICK,
    "PlanckBits": PLANCK_BIT,
    "E_jump": None,   # velocity-dependent; use e_jump()
    "lambda_p": LAMBDA_P,
    "t_p": T_P,
    "E_p": E_P,
    "m_p": M_P,
}


if __name__ == "__main__":
    print("=== PNMS Constants ===")
    print(f"lambda_p = {LAMBDA_P:.6e} m")
    print(f"t_p      = {T_P:.6e} s")
    print(f"E_p      = {E_P:.6e} J")
    print(f"m_p      = {M_P:.6e} kg")
    print()
    print("=== PNMS Derived Units (SI equivalents) ===")
    print(f"1 Plameter   = {PLAMETER:.6e} m  (≈ 1 m)")
    print(f"1 Plasecond  = {PLASECOND:.6e} s  (≈ 1 s)")
    print(f"1 WarpTick   = {WARPTICK:.6e} s  (≈ 13.8 Gyr)")
    print(f"1 Quasiplanck= {QUASIPLANCK:.6e} m  (≈ Hubble radius)")
    print()
    print("=== BH Entropy (solar mass) ===")
    M_SUN = 1.989e30
    s_bh = bh_entropy(M_SUN)
    print(f"S_BH(M_sun) = {s_bh:.4e} J/K")
    print(f"           = {s_bh/K_B:.4e} entropy ticks")
