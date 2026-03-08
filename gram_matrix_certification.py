import argparse
import math
from typing import Dict, List, Sequence, Tuple

import mpmath
import numpy as np
from scipy.interpolate import BSpline
from scipy.special import digamma

# 0. Paramètres par défaut
DEFAULT_N = 10
DEFAULT_J = 3
DEFAULT_L = 2.3
DEFAULT_PREC = 50


# 1. Construction de la base B-spline cubique sur [-L, L]
def build_bspline_basis(L: float, J: int) -> Tuple[List[BSpline], np.ndarray, float]:
    """
    Retourne N_{0,3}, …, N_{M-1,3} sur [-L, L] avec nœuds multiples aux bords.

    Nombre de fonctions : M = 2^J + 3 (degré 3, knots multiples d'ordre 4 aux bornes).
    """
    num_intervals = 2**J
    h = 2.0 * L / num_intervals

    inner_knots = [-L + i * h for i in range(1, num_intervals)]
    knots = np.array([-L] * 4 + inner_knots + [L] * 4, dtype=float)

    degree = 3
    n_basis = len(knots) - degree - 1

    basis_funcs: List[BSpline] = []
    for i in range(n_basis):
        c = np.zeros(n_basis)
        c[i] = 1.0
        basis_funcs.append(BSpline(knots, c, degree, extrapolate=False))

    return basis_funcs, knots, h


# 2. Transformée de Fourier des B-splines
def bspline_fourier(
    b: BSpline,
    t_grid: np.ndarray,
    L: float,
    n_pts: int = 2048,
) -> np.ndarray:
    """Calcule ê_α(t) = ∫ e_α(x)e^{-ixt} dx par quadrature trapézoïdale."""
    x = np.linspace(-L, L, n_pts)
    vals = np.nan_to_num(b(x), nan=0.0)

    # vectorisé: exp(-i x t) avec broadcasting
    phase = np.exp(-1j * np.outer(x, t_grid))
    integrand = vals[:, None] * phase
    return np.trapezoid(integrand, x, axis=0)


# 3. Noyau archimédien

def Omega(t: float) -> float:
    """Ω(t) = −log π + Re ψ(1/4 + it/2)."""
    z = 0.25 + 0.5j * t
    return -math.log(math.pi) + float(np.real(digamma(z)))


def Omega_vec(t_arr: np.ndarray) -> np.ndarray:
    return np.array([Omega(float(t)) for t in t_arr], dtype=float)


# 4. Partie archimédienne

def archimedean_term(
    basis: Sequence[BSpline],
    L: float,
    T_cut: float = 50.0,
    n_freq: int = 1024,
    n_pts_x: int = 2048,
) -> np.ndarray:
    """A_{αβ} = (1/2π) ∫_{-T}^{T} ê_α(t) conj(ê_β(t)) Ω(t) dt."""
    M = len(basis)
    t_grid = np.linspace(-T_cut, T_cut, n_freq)
    omega = Omega_vec(t_grid)

    F = [bspline_fourier(b, t_grid, L, n_pts=n_pts_x) for b in basis]

    A = np.zeros((M, M), dtype=float)
    for alpha in range(M):
        for beta in range(alpha, M):
            integrand = F[alpha] * np.conj(F[beta]) * omega
            val = np.trapezoid(integrand.real, t_grid) / (2.0 * math.pi)
            A[alpha, beta] = val
            A[beta, alpha] = val
    return A


# 5. Convolution B-spline

def K_numeric(
    b_alpha: BSpline,
    b_beta: BSpline,
    u: float,
    L: float,
    n_pts: int = 1500,
) -> float:
    """K_{αβ}(u) = ∫ e_α(x)e_β(x-u)dx."""
    if abs(u) > 2.0 * L + 1e-12:
        return 0.0

    x = np.linspace(-L, L, n_pts)
    vals_alpha = np.nan_to_num(b_alpha(x), nan=0.0)
    xu = x - u
    vals_beta = np.where((xu >= -L) & (xu <= L), np.nan_to_num(b_beta(xu), nan=0.0), 0.0)
    return float(np.trapezoid(vals_alpha * vals_beta, x))


# 6. Puissances de premiers

def prime_powers_simple(N2: int) -> List[Tuple[int, int, float]]:
    """Crible d'Ératosthène + génération p^m <= N2."""
    if N2 < 2:
        return []

    sieve = [True] * (N2 + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(N2**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, N2 + 1, i):
                sieve[j] = False
    primes = [i for i in range(2, N2 + 1) if sieve[i]]

    result: List[Tuple[int, int, float]] = []
    for p in primes:
        m = 1
        val = p
        while val <= N2:
            result.append((p, m, math.log(p)))
            if val > N2 // p:
                break
            val *= p
            m += 1
    return result


# 7. Partie ultramétrique

def ultrametric_term(
    basis: Sequence[BSpline],
    L: float,
    n: int,
    n_pts_conv: int = 1500,
) -> np.ndarray:
    """U_{αβ} = Σ_{p^m ≤ n²} log(p) [K(u)+p^{-m}K(-u)]."""
    M = len(basis)
    U = np.zeros((M, M), dtype=float)
    pp = prime_powers_simple(n * n)
    print(f"  → {len(pp)} puissances de premiers ≤ {n}² = {n*n}")

    # cache pour éviter les recalculs des mêmes u
    cache: Dict[Tuple[int, int, float], float] = {}

    for (p, m, logp) in pp:
        u_pos = m * logp
        u_neg = -u_pos
        weight_neg = p ** (-m)

        for alpha in range(M):
            for beta in range(alpha, M):
                key_pos = (alpha, beta, round(u_pos, 12))
                key_neg = (alpha, beta, round(u_neg, 12))
                if key_pos not in cache:
                    cache[key_pos] = K_numeric(basis[alpha], basis[beta], u_pos, L, n_pts=n_pts_conv)
                if key_neg not in cache:
                    cache[key_neg] = K_numeric(basis[alpha], basis[beta], u_neg, L, n_pts=n_pts_conv)

                val = logp * (cache[key_pos] + weight_neg * cache[key_neg])
                U[alpha, beta] += val
                if alpha != beta:
                    U[beta, alpha] += val

    return U


# 8. Terme c0 = log π

def log_pi_term(basis: Sequence[BSpline], L: float, n_pts_conv: int = 1500) -> np.ndarray:
    """C_{αβ} = log(π)·K_{αβ}(0)."""
    M = len(basis)
    C = np.zeros((M, M), dtype=float)
    c0 = math.log(math.pi)

    for alpha in range(M):
        for beta in range(alpha, M):
            k0 = K_numeric(basis[alpha], basis[beta], 0.0, L, n_pts=n_pts_conv)
            val = c0 * k0
            C[alpha, beta] = val
            C[beta, alpha] = val

    return C


# 9. Assemblage complet

def build_gram_matrix(
    n: int,
    J: int,
    L: float,
    T_cut: float = 40.0,
    n_freq: int = 512,
    n_pts_x: int = 2048,
    n_pts_conv: int = 1500,
):
    """Retourne G^(n,J) et ses composantes."""
    print(f"\n{'='*60}")
    print(f"  Construction de G^(n={n}, J={J})  [L={L:.3f}]")
    print(f"{'='*60}")

    basis, knots, h = build_bspline_basis(L, J)
    M = len(basis)
    print(f"  Base B-spline : M = {M} fonctions (2^{J}+3={2**J+3}), h = {h:.4f}")

    print("  [1/3] Partie archimédienne …")
    A = archimedean_term(basis, L, T_cut=T_cut, n_freq=n_freq, n_pts_x=n_pts_x)

    print("  [2/3] Partie ultramétrique …")
    U = ultrametric_term(basis, L, n, n_pts_conv=n_pts_conv)

    print("  [3/3] Terme log π …")
    C = log_pi_term(basis, L, n_pts_conv=n_pts_conv)

    G = A + U + C
    return G, A, U, C, basis, knots


# 10. Certification des valeurs propres

def certify_eigenvalues(G: np.ndarray, prec: int = 50) -> dict:
    """Diagonalise G (numpy), puis raffine en haute précision (mpmath)."""
    eigvals_np = np.linalg.eigvalsh(G)
    print("\n  Valeurs propres (float64) :")
    print(f"    min = {eigvals_np.min():.6e}")
    print(f"    max = {eigvals_np.max():.6e}")
    print(f"    toutes ≥ 0 ? {bool(eigvals_np.min() >= 0)}")

    mpmath.mp.dps = prec
    M = G.shape[0]
    Gmp = mpmath.matrix([[mpmath.mpf(G[i, j]) for j in range(M)] for i in range(M)])
    eigvals_mp = mpmath.eigsy(Gmp)[0]
    eigvals_mp_sorted = sorted(float(v) for v in eigvals_mp)

    print(f"\n  Valeurs propres (mpmath, {prec} décimales) :")
    for i, lam in enumerate(eigvals_mp_sorted):
        print(f"    λ_{i} = {lam:.8e}")

    lam_min = eigvals_mp_sorted[0]
    lam_max = eigvals_mp_sorted[-1]
    is_psd = lam_min >= -10 ** (-(prec // 3))

    print(f"\n  → λ_min = {lam_min:.6e}  |  certifié PSD = {is_psd}")
    return {
        "eigvals": eigvals_mp_sorted,
        "lam_min": lam_min,
        "lam_max": lam_max,
        "is_psd": is_psd,
    }


# 11. Rapport

def print_report(n: int, J: int, L: float, G: np.ndarray, cert: dict, A: np.ndarray, U: np.ndarray, C: np.ndarray) -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print(" RAPPORT — Matrice de Gram G^(n,J)")
    print(sep)
    print(f"  Paramètres  : n={n},  J={J},  L={L:.4f}")
    print(f"  Taille      : {G.shape[0]}×{G.shape[1]}")
    print(
        f"  Frobenius   : ‖A‖={np.linalg.norm(A):.4e}  "
        f"‖U‖={np.linalg.norm(U):.4e}  ‖C‖={np.linalg.norm(C):.4e}"
    )
    print(f"  λ_min       : {cert['lam_min']:.6e}")
    print(f"  λ_max       : {cert['lam_max']:.6e}")
    print(f"  Condition   : κ = {cert['lam_max']/max(abs(cert['lam_min']), 1e-300):.3e}")
    print(f"  PSD certifié: {cert['is_psd']}")
    print(sep)
    if cert["is_psd"]:
        print("  ✓ Conjecture 1’ VÉRIFIÉE pour ces paramètres.")
    else:
        print("  ✗ Violation détectée — inspecter les directions négatives.")
    print(sep)


# 12. Point d'entrée

def main():
    parser = argparse.ArgumentParser(
        description="Calcule et certifie la matrice de Gram G^(n,J) (Conjecture 1’)"
    )
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--J", type=int, default=DEFAULT_J)
    parser.add_argument("--L", type=float, default=DEFAULT_L)
    parser.add_argument("--prec", type=int, default=DEFAULT_PREC, help="Précision mpmath (décimales)")
    parser.add_argument("--T_cut", type=float, default=40.0, help="Troncature fréquentielle pour ∫Ω")
    parser.add_argument("--n_freq", type=int, default=512, help="Points de quadrature archimédiens")
    parser.add_argument("--n_pts_x", type=int, default=2048, help="Points de quadrature en x pour Fourier")
    parser.add_argument("--n_pts_conv", type=int, default=1500, help="Points de quadrature pour K")
    parser.add_argument("--no_certify", action="store_true", help="Sauter la certification mpmath (plus rapide)")
    args = parser.parse_args()

    G, A, U, C, _, _ = build_gram_matrix(
        n=args.n,
        J=args.J,
        L=args.L,
        T_cut=args.T_cut,
        n_freq=args.n_freq,
        n_pts_x=args.n_pts_x,
        n_pts_conv=args.n_pts_conv,
    )

    if not args.no_certify:
        cert = certify_eigenvalues(G, prec=args.prec)
    else:
        eigvals = sorted(np.linalg.eigvalsh(G).tolist())
        cert = {
            "eigvals": eigvals,
            "lam_min": eigvals[0],
            "lam_max": eigvals[-1],
            "is_psd": eigvals[0] >= 0,
        }

    print_report(args.n, args.J, args.L, G, cert, A, U, C)

    out = f"G_n{args.n}_J{args.J}.npy"
    np.save(out, G)
    print(f"\n  Matrice sauvegardée : {out}")
    return G, cert


if __name__ == "__main__":
    main()
