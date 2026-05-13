# -*- coding: utf-8 -*-
"""Candidate trip generation and pure-Python set-cover selection."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from data_config import CargoItem, PlacedItem, Route, TRUCK_TYPES, VehiclePlan, ensure_directories
from geometry import total_volume_cm3, weighted_x_cg
from packing import multi_start_pack
from routing import best_route_for_stations, route_distance, transport_cost
from validator import validate_items


@dataclass
class CandidateTrip:
    stations: Tuple[str, ...]
    route: Route
    truck_name: str
    placed_items: List[PlacedItem]
    route_distance: float
    transport_cost: float
    total_cost: float
    relocation_count: int
    relocation_volume_m3: float
    volume_utilization: float
    weight_utilization: float
    x_cg: float
    mode: str
    meta: Dict[str, object]

    @property
    def load_weight(self) -> float:
        return sum(p.weight for p in self.placed_items)

    @property
    def load_volume_cm3(self) -> float:
        return sum(p.volume_cm3 for p in self.placed_items)


def _items_for_stations(items: Sequence[CargoItem], stations: Sequence[str]) -> List[CargoItem]:
    station_set = set(stations)
    return [i for i in items if i.destination in station_set]


def _make_candidate(
    station_subset: Sequence[str],
    all_items: Sequence[CargoItem],
    truck_name: str,
    matrix,
    *,
    mode: str,
    return_to_depot: bool,
    eta: float,
    mu: float,
    seed_offset: int = 0,
) -> CandidateTrip | None:
    truck = TRUCK_TYPES[truck_name]
    items = _items_for_stations(all_items, station_subset)
    if not items:
        return None
    if sum(i.weight for i in items) > truck.max_payload + 1e-7:
        return None
    if sum(i.volume_cm3 for i in items) > truck.volume_cm3 * 0.985:
        # Geometric packing above this level is rarely reliable under the
        # contest constraints, so leave it to a larger/split candidate.
        return None

    route = best_route_for_stations(station_subset, matrix=matrix, return_to_depot=return_to_depot)
    strategies = ["destination_lifo", "category", "volume"]
    seeds = [0 + seed_offset, 42 + seed_offset]
    banded = mode == "strict" and len(route.stops) > 1
    placed, unpacked, meta = multi_start_pack(
        items,
        truck,
        route=route.stops,
        mode=mode,
        vehicle_id="CAND",
        trip_id="CAND",
        strategies=strategies,
        seeds=seeds,
        require_all=True,
        banded=banded,
    )
    if unpacked or not placed:
        return None
    item_ids = [i.item_id for i in items]
    report = validate_items(placed, mode=mode, expected_item_ids=item_ids, relocation_volume_limit=0.15)
    if report["hard_violation_count"] > 0:
        return None
    d = route_distance(route.stops, matrix=matrix, return_to_depot=return_to_depot)
    tc = transport_cost(truck, d, sum(i.weight for i in items))
    penalty = eta * float(report["relocation_count"]) + mu * float(report["relocation_volume_m3"])
    total = tc + (penalty if mode == "flexible" else 0.0)
    return CandidateTrip(
        stations=tuple(sorted(station_subset)),
        route=route,
        truck_name=truck_name,
        placed_items=placed,
        route_distance=d,
        transport_cost=tc,
        total_cost=total,
        relocation_count=int(report["relocation_count"]),
        relocation_volume_m3=float(report["relocation_volume_m3"]),
        volume_utilization=sum(p.volume_cm3 for p in placed) / truck.volume_cm3,
        weight_utilization=sum(p.weight for p in placed) / truck.max_payload,
        x_cg=weighted_x_cg(placed),
        mode=mode,
        meta=meta,
    )


def _make_candidate_for_items(
    explicit_items: Sequence[CargoItem],
    matrix,
    *,
    mode: str,
    return_to_depot: bool,
    eta: float,
    mu: float,
    seed_offset: int = 0,
    preferred_trucks: Sequence[str] = ("LightEV", "HeavyEV"),
) -> CandidateTrip | None:
    """Build a candidate for an exact item subset.

    This is used after station splitting so the optimizer can recombine partial
    station loads into true multi-stop trips while still covering every item
    exactly once.
    """

    items = list(explicit_items)
    stations = tuple(sorted({i.destination for i in items if i.destination}))
    if not items or not stations:
        return None
    route = best_route_for_stations(stations, matrix=matrix, return_to_depot=return_to_depot)
    best: CandidateTrip | None = None
    for truck_name in preferred_trucks:
        truck = TRUCK_TYPES[truck_name]
        if sum(i.weight for i in items) > truck.max_payload + 1e-7:
            continue
        if sum(i.volume_cm3 for i in items) > truck.volume_cm3 * 0.985:
            continue
        strategies = ["destination_lifo", "category", "volume"]
        seeds = [0 + seed_offset, 42 + seed_offset]
        placed, unpacked, meta = multi_start_pack(
            items,
            truck,
            route=route.stops,
            mode=mode,
            vehicle_id="MERGE",
            trip_id="MERGE",
            strategies=strategies,
            seeds=seeds,
            require_all=True,
            banded=(mode == "strict" and len(route.stops) > 1),
        )
        if unpacked or not placed:
            continue
        expected_ids = [i.item_id for i in items]
        report = validate_items(placed, mode=mode, expected_item_ids=expected_ids, relocation_volume_limit=0.15)
        if report["hard_violation_count"] > 0:
            continue
        d = route_distance(route.stops, matrix=matrix, return_to_depot=return_to_depot)
        tc = transport_cost(truck, d, sum(i.weight for i in items))
        penalty = eta * float(report["relocation_count"]) + mu * float(report["relocation_volume_m3"])
        cand = CandidateTrip(
            stations=stations,
            route=route,
            truck_name=truck_name,
            placed_items=placed,
            route_distance=d,
            transport_cost=tc,
            total_cost=tc + (penalty if mode == "flexible" else 0.0),
            relocation_count=int(report["relocation_count"]),
            relocation_volume_m3=float(report["relocation_volume_m3"]),
            volume_utilization=sum(p.volume_cm3 for p in placed) / truck.volume_cm3,
            weight_utilization=sum(p.weight for p in placed) / truck.max_payload,
            x_cg=weighted_x_cg(placed),
            mode=mode,
            meta=meta,
        )
        if best is None or cand.total_cost < best.total_cost:
            best = cand
    return best


def generate_candidates(
    items: Sequence[CargoItem],
    stations: Sequence[str],
    matrix,
    *,
    mode: str = "strict",
    max_stops: int = 3,
    return_to_depot: bool = True,
    eta: float = 20.0,
    mu: float = 30.0,
    seed_offset: int = 0,
) -> List[CandidateTrip]:
    candidates: Dict[Tuple[Tuple[str, ...], str], CandidateTrip] = {}
    stations = list(stations)
    for k in range(1, min(max_stops, len(stations)) + 1):
        for subset in combinations(stations, k):
            for truck_name in ("LightEV", "HeavyEV"):
                cand = _make_candidate(
                    subset,
                    items,
                    truck_name,
                    matrix,
                    mode=mode,
                    return_to_depot=return_to_depot,
                    eta=eta,
                    mu=mu,
                    seed_offset=seed_offset,
                )
                if cand is None:
                    continue
                key = (tuple(sorted(subset)), truck_name)
                prev = candidates.get(key)
                if prev is None or cand.total_cost < prev.total_cost:
                    candidates[key] = cand
    return list(candidates.values())


def select_station_cover(candidates: Sequence[CandidateTrip], stations: Sequence[str]) -> List[CandidateTrip]:
    index = {s: i for i, s in enumerate(stations)}
    full = (1 << len(stations)) - 1
    dp: Dict[int, Tuple[float, List[CandidateTrip]]] = {0: (0.0, [])}
    for mask in range(full + 1):
        if mask not in dp:
            continue
        base_cost, base_list = dp[mask]
        for cand in candidates:
            cmask = 0
            for s in cand.stations:
                cmask |= 1 << index[s]
            if mask & cmask:
                continue
            new_mask = mask | cmask
            new_cost = base_cost + cand.total_cost
            if new_mask not in dp or new_cost < dp[new_mask][0]:
                dp[new_mask] = (new_cost, [*base_list, cand])
    return dp.get(full, (float("inf"), []))[1]


def solve_station_cover(
    items: Sequence[CargoItem],
    stations: Sequence[str],
    matrix,
    *,
    mode: str = "strict",
    max_stops: int = 3,
    return_to_depot: bool = True,
    eta: float = 20.0,
    mu: float = 30.0,
    seed_offset: int = 0,
) -> Tuple[List[VehiclePlan], List[CandidateTrip]]:
    if len(stations) > 4:
        candidates: List[CandidateTrip] = []
        selected: List[CandidateTrip] = []
    else:
        candidates = generate_candidates(
            items,
            stations,
            matrix,
            mode=mode,
            max_stops=max_stops,
            return_to_depot=return_to_depot,
            eta=eta,
            mu=mu,
            seed_offset=seed_offset,
        )
        selected = select_station_cover(candidates, stations)

    # Safety fallback: one HeavyEV per station.  This prioritizes complete
    # delivery over cost if a multi-station cover is not found.
    if not selected:
        selected = []
        for s in stations:
            cand = _make_candidate(
                [s],
                items,
                "HeavyEV",
                matrix,
                mode=mode,
                return_to_depot=return_to_depot,
                eta=eta,
                mu=mu,
                seed_offset=seed_offset,
            )
            if cand is not None:
                selected.append(cand)

    covered_stations = {s for cand in selected for s in cand.stations}
    if covered_stations != set(stations):
        selected = _split_station_batches(
            items,
            stations,
            matrix,
            mode=mode,
            return_to_depot=return_to_depot,
            eta=eta,
            mu=mu,
            seed_offset=seed_offset,
        )

    selected = _merge_batch_trips(
        selected,
        matrix,
        mode=mode,
        max_stops=max_stops,
        return_to_depot=return_to_depot,
        eta=eta,
        mu=mu,
        seed_offset=seed_offset,
    )

    plans: List[VehiclePlan] = []
    for idx, cand in enumerate(selected, start=1):
        trip_id = f"{mode.upper()}_{idx:03d}"
        vehicle_id = f"{cand.truck_name}_{idx:03d}"
        for p in cand.placed_items:
            p.trip_id = trip_id
            p.vehicle_id = vehicle_id
            p.truck_type = cand.truck_name
            p.route = list(cand.route.stops)
        truck = TRUCK_TYPES[cand.truck_name]
        plan = VehiclePlan(
            trip_id=trip_id,
            vehicle_id=vehicle_id,
            truck_type=truck,
            route=cand.route,
            placed_items=cand.placed_items,
            cost=cand.total_cost,
            route_distance=cand.route_distance,
            mode=mode,
            relocation_count=cand.relocation_count,
            relocation_volume_m3=cand.relocation_volume_m3,
            extra={
                "transport_cost": cand.transport_cost,
                "volume_utilization": cand.volume_utilization,
                "weight_utilization": cand.weight_utilization,
                "x_cg": cand.x_cg,
            },
        )
        plans.append(plan)
    return plans, [*candidates, *selected]


def _candidate_item_ids(cand: CandidateTrip) -> set[str]:
    return {p.item_id for p in cand.placed_items}


def _merge_batch_trips(
    selected: Sequence[CandidateTrip],
    matrix,
    *,
    mode: str,
    max_stops: int,
    return_to_depot: bool,
    eta: float,
    mu: float,
    seed_offset: int = 0,
) -> List[CandidateTrip]:
    """Cost-improving local search that creates multi-stop batch trips."""

    current = list(selected)
    improved = True
    while improved:
        improved = False
        best_delta = 0.0
        best_indices: Tuple[int, ...] | None = None
        best_candidate: CandidateTrip | None = None

        # Pairwise merging is repeated, so it can build 3-stop routes while
        # keeping the search reasonably fast and auditable.
        for i, j in combinations(range(len(current)), 2):
            union_stations = set(current[i].stations) | set(current[j].stations)
            if len(union_stations) > max_stops:
                continue
            if len(union_stations) <= 1:
                continue
            if _candidate_item_ids(current[i]) & _candidate_item_ids(current[j]):
                continue
            items = [p.item for p in current[i].placed_items] + [p.item for p in current[j].placed_items]
            old_cost = current[i].total_cost + current[j].total_cost
            cand = _make_candidate_for_items(
                items,
                matrix,
                mode=mode,
                return_to_depot=return_to_depot,
                eta=eta,
                mu=mu,
                seed_offset=seed_offset,
                preferred_trucks=("HeavyEV", "LightEV"),
            )
            if cand is None:
                continue
            delta = old_cost - cand.total_cost
            multi_stop_bonus = 0.01 if len(cand.stations) > 1 else 0.0
            if delta + multi_stop_bonus > best_delta + 1e-6:
                best_delta = delta
                best_indices = (i, j)
                best_candidate = cand
        if best_candidate is not None and best_indices is not None:
            remove = set(best_indices)
            current = [c for idx, c in enumerate(current) if idx not in remove]
            current.append(best_candidate)
            improved = True
    return current


def _split_station_batches(
    items: Sequence[CargoItem],
    stations: Sequence[str],
    matrix,
    *,
    mode: str,
    return_to_depot: bool,
    eta: float,
    mu: float,
    seed_offset: int = 0,
) -> List[CandidateTrip]:
    """Feasibility-first fallback: split each station into as many trips as needed."""

    out: List[CandidateTrip] = []
    tmp_counter = 0
    for station in stations:
        remaining = [i for i in items if i.destination == station]
        while remaining:
            tmp_counter += 1
            best = None
            best_key = None
            for truck_name in ("LightEV", "HeavyEV"):
                truck = TRUCK_TYPES[truck_name]
                if min(i.weight for i in remaining) > truck.max_payload:
                    continue
                placed, unpacked, meta = multi_start_pack(
                    remaining,
                    truck,
                    route=[station],
                    mode=mode,
                    vehicle_id=f"FB_{tmp_counter}",
                    trip_id=f"FB_{tmp_counter}",
                    strategies=["category", "volume", "base_area"],
                    seeds=[0 + seed_offset],
                    require_all=False,
                    banded=False,
                )
                if not placed:
                    continue
                item_ids = [p.item_id for p in placed]
                report = validate_items(placed, mode=mode, expected_item_ids=item_ids, relocation_volume_limit=0.15)
                if report["hard_violation_count"] > 0:
                    continue
                route = Route((station,), return_to_depot=return_to_depot)
                d = route_distance(route.stops, matrix=matrix, return_to_depot=return_to_depot)
                tc = transport_cost(truck, d, sum(p.weight for p in placed))
                penalty = eta * float(report["relocation_count"]) + mu * float(report["relocation_volume_m3"])
                cand = CandidateTrip(
                    stations=(station,),
                    route=route,
                    truck_name=truck_name,
                    placed_items=placed,
                    route_distance=d,
                    transport_cost=tc,
                    total_cost=tc + (penalty if mode == "flexible" else 0.0),
                    relocation_count=int(report["relocation_count"]),
                    relocation_volume_m3=float(report["relocation_volume_m3"]),
                    volume_utilization=sum(p.volume_cm3 for p in placed) / truck.volume_cm3,
                    weight_utilization=sum(p.weight for p in placed) / truck.max_payload,
                    x_cg=weighted_x_cg(placed),
                    mode=mode,
                    meta=meta,
                )
                # Primary objective in fallback is progress; use cheaper truck
                # only when it loads the same number of items.
                key = (len(placed), -cand.total_cost)
                if best is None or key > best_key:
                    best = cand
                    best_key = key
            if best is None:
                raise RuntimeError(f"Could not pack any remaining item for station {station}")
            out.append(best)
            packed_ids = {p.item_id for p in best.placed_items}
            remaining = [i for i in remaining if i.item_id not in packed_ids]
    return out


TRIP_FIELDS = [
    "trip_id",
    "vehicle_id",
    "truck_type",
    "route",
    "route_distance",
    "covered_item_count",
    "load_weight",
    "load_volume_m3",
    "transport_cost",
    "penalty_cost",
    "total_cost",
    "volume_utilization",
    "weight_utilization",
    "x_cg",
    "relocation_count",
    "relocation_volume_m3",
    "mode",
]


def write_trips_csv(plans: Sequence[VehiclePlan], path: Path, eta: float = 20.0, mu: float = 30.0) -> None:
    ensure_directories()
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=TRIP_FIELDS)
        writer.writeheader()
        for p in plans:
            transport = float(p.extra.get("transport_cost", p.cost))
            penalty = eta * p.relocation_count + mu * p.relocation_volume_m3 if p.mode == "flexible" else 0.0
            writer.writerow(
                {
                    "trip_id": p.trip_id,
                    "vehicle_id": p.vehicle_id,
                    "truck_type": p.truck_type.name,
                    "route": p.route.label(),
                    "route_distance": round(p.route_distance, 6),
                    "covered_item_count": len(p.placed_items),
                    "load_weight": round(p.load_weight, 6),
                    "load_volume_m3": round(p.load_volume_cm3 / 1_000_000.0, 6),
                    "transport_cost": round(transport, 6),
                    "penalty_cost": round(penalty, 6),
                    "total_cost": round(p.cost, 6),
                    "volume_utilization": round(p.volume_utilization, 6),
                    "weight_utilization": round(p.weight_utilization, 6),
                    "x_cg": round(float(p.extra.get("x_cg", weighted_x_cg(p.placed_items))), 6),
                    "relocation_count": p.relocation_count,
                    "relocation_volume_m3": round(p.relocation_volume_m3, 6),
                    "mode": p.mode,
                }
            )


def flatten_plans(plans: Sequence[VehiclePlan]) -> List[PlacedItem]:
    out: List[PlacedItem] = []
    for p in plans:
        out.extend(p.placed_items)
    return out
