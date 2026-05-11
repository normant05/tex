"""Search for counterexamples with an ILP model.

This script encodes the pseudocode shared in the task into executable Python
using PuLP. It loops over (n, r), builds a monotone family F and an
intersecting subfamily A, and looks for feasible instances that violate all
stars.
"""

from __future__ import annotations

from itertools import combinations
from typing import Iterable, Iterator, Sequence, Tuple

import pulp


Subset = Tuple[int, ...]


def subsets(n: int, r_max: int, r_min: int = 0) -> Iterator[Subset]:
    """Yield all subsets of [n] with size between r_min and r_max (inclusive)."""
    universe = range(n)
    for k in range(r_min, r_max + 1):
        for s in combinations(universe, k):
            yield s


def proper_subsets(s: Sequence[int]) -> Iterator[Subset]:
    """Yield all proper subsets of a given subset s."""
    s = tuple(s)
    for k in range(len(s)):
        for t in combinations(s, k):
            yield t


def disjoint_pairs(items: Sequence[Subset]) -> Iterator[Tuple[Subset, Subset]]:
    """Yield unordered disjoint pairs from items."""
    for i in range(len(items)):
        a = set(items[i])
        for j in range(i + 1, len(items)):
            b = items[j]
            if a.isdisjoint(b):
                yield items[i], b


def build_and_solve(n: int, r_max: int) -> tuple[str, dict, dict]:
    all_subsets = list(subsets(n, r_max))

    model = pulp.LpProblem(f"counterexample_n{n}_r{r_max}", pulp.LpStatusOptimal)

    f = {s: pulp.LpVariable(f"f_{'_'.join(map(str, s)) or 'empty'}", cat="Binary") for s in all_subsets}
    a = {s: pulp.LpVariable(f"a_{'_'.join(map(str, s)) or 'empty'}", cat="Binary") for s in all_subsets}

    # Downset constraints: if S in F then every proper subset T of S is in F.
    for s in all_subsets:
        for t in proper_subsets(s):
            model += f[s] <= f[t]

    # A is a subfamily of F.
    for s in all_subsets:
        model += a[s] <= f[s]

    # A is intersecting.
    for s, t in disjoint_pairs(all_subsets):
        model += a[s] + a[t] <= 1

    total_a = pulp.lpSum(a[s] for s in all_subsets)

    # Violate all stars.
    for x in range(n):
        star_x = pulp.lpSum(f[s] for s in all_subsets if x in s)
        model += total_a >= star_x + 1

    # Optional: tau(A) >= 3.
    for i in range(n):
        model += pulp.lpSum(a[s] for s in all_subsets if i not in s) >= 1

    for i in range(n):
        for j in range(i + 1, n):
            model += pulp.lpSum(a[s] for s in all_subsets if i not in s and j not in s) >= 1

    # Symmetry breaking.
    for i in range(n - 1):
        left = pulp.lpSum(f[s] for s in all_subsets if i in s)
        right = pulp.lpSum(f[s] for s in all_subsets if i + 1 in s)
        model += left >= right

    model += 0  # Feasibility model.
    model.solve(pulp.PULP_CBC_CMD(msg=False))

    status = pulp.LpStatus[model.status]
    return status, f, a


def extract_counterexample(f: dict[Subset, pulp.LpVariable], a: dict[Subset, pulp.LpVariable]) -> None:
    family_f = [s for s, var in f.items() if var.value() and var.value() > 0.5]
    family_a = [s for s, var in a.items() if var.value() and var.value() > 0.5]
    print("Found feasible counterexample")
    print(f"|F| = {len(family_f)}, |A| = {len(family_a)}")
    print("F:", family_f)
    print("A:", family_a)


def search(n_max: int, r_max: int) -> bool:
    for n in range(4, n_max + 1):
        for r in range(4, r_max + 1):
            print(f"Trying n={n}, r={r}")
            status, f, a = build_and_solve(n, r)
            if status in {"Optimal", "Feasible"}:
                extract_counterexample(f, a)
                return True
    return False


if __name__ == "__main__":
    found = search(n_max=6, r_max=5)
    if not found:
        print("No feasible counterexample found in the searched range.")
