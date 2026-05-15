"""Routing and transport cost utilities."""

from __future__ import annotations
try:
    from bootstrap_paths import configure_paths as _configure_organized_paths
except ModuleNotFoundError:
    import sys as _organized_sys
    from pathlib import Path as _OrganizedPath
    _organized_root = next((p for p in _OrganizedPath(__file__).resolve().parents if (p / "00_common_core").is_dir()), None)
    if _organized_root is not None:
        _organized_sys.path.insert(0, str(_organized_root))
    from bootstrap_paths import configure_paths as _configure_organized_paths
_configure_organized_paths(__file__)

from itertools import combinations, permutations
from typing import Dict, Iterable, List, Sequence, Tuple

from data_config import BASE_DISTANCE_MATRIX, DISTANCE_MATRIX, Route, TruckType, symmetric_distance_matrix


def route_distance(stops: Sequence[str], matrix: Dict[Tuple[str, str], float] | None = None, return_to_depot: bool = True) -> float:
    matrix = matrix or DISTANCE_MATRIX
    total = 0.0
    current = "Depot"
    for stop in stops:
        total += matrix[(current, stop)]
        current = stop
    if return_to_depot:
        total += matrix[(current, "Depot")]
    return total


def transport_cost(truck: TruckType, distance: float, load_weight_kg: float) -> float:
    return truck.fixed_cost + truck.dynamic_coeff * distance * ((truck.empty_weight + load_weight_kg) / 1000.0)


def all_routes(stations: Sequence[str], max_stops: int | None = None, return_to_depot: bool = True) -> List[Route]:
    out: List[Route] = []
    n = len(stations)
    max_k = max_stops or n
    for k in range(1, min(max_k, n) + 1):
        for subset in combinations(stations, k):
            for perm in permutations(subset):
                out.append(Route(tuple(perm), return_to_depot=return_to_depot))
    return out


def best_route_for_stations(
    stations: Sequence[str],
    matrix: Dict[Tuple[str, str], float] | None = None,
    return_to_depot: bool = True,
) -> Route:
    best: Route | None = None
    best_d = float("inf")
    for perm in permutations(stations):
        d = route_distance(perm, matrix=matrix, return_to_depot=return_to_depot)
        if d < best_d:
            best = Route(tuple(perm), return_to_depot=return_to_depot)
            best_d = d
    if best is None:
        return Route(tuple(), return_to_depot=return_to_depot)
    return best


def route_local_search(stops: Sequence[str], matrix: Dict[Tuple[str, str], float] | None = None, return_to_depot: bool = True) -> Route:
    # For the contest scale in this project, exact permutation is cheap.
    return best_route_for_stations(stops, matrix=matrix, return_to_depot=return_to_depot)


def cluster_stations(stations: Sequence[str], matrix: Dict[Tuple[str, str], float] | None = None, max_cluster_size: int = 3) -> List[List[str]]:
    matrix = matrix or DISTANCE_MATRIX
    remaining = set(stations)
    clusters: List[List[str]] = []
    while remaining:
        seed = min(remaining, key=lambda s: matrix[("Depot", s)])
        remaining.remove(seed)
        cluster = [seed]
        while remaining and len(cluster) < max_cluster_size:
            nxt = min(remaining, key=lambda s: min(matrix[(s, c)] for c in cluster))
            remaining.remove(nxt)
            cluster.append(nxt)
        clusters.append(cluster)
    return clusters

