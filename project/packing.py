# -*- coding: utf-8 -*-
"""Extreme-point style 3D packing heuristics."""

from __future__ import annotations

from dataclasses import replace
import random
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from data_config import CargoItem, PlacedItem, TRUCK_TYPES, TruckType, legal_orientations
from geometry import EPS, boxes_closed_intersect, boxes_overlap, lifo_blocks, support_area_cm2, weighted_x_cg, xy_overlap_area_cm2
from validator import MAX_TOP_PRESSURE_KG_PER_M2, validate_items


CATEGORY_RANK = {"I": 0, "III": 1, "IV": 2, "V": 3, "II": 4}
CANDIDATE_POINT_LIMIT = 1200


def sort_items(items: Sequence[CargoItem], strategy: str, seed: int = 0, route: Sequence[str] | None = None) -> List[CargoItem]:
    route = list(route or [])
    rng = random.Random(seed)

    def route_rank(item: CargoItem) -> int:
        if item.destination in route:
            # Later stops are placed first/deeper; earlier stops tend to remain closer to door.
            return -route.index(item.destination)
        return 0

    if strategy == "category":
        key = lambda i: (CATEGORY_RANK.get(i.category, 9), -i.weight, -i.volume_cm3)
    elif strategy == "volume":
        key = lambda i: (-i.volume_cm3, CATEGORY_RANK.get(i.category, 9), -i.weight)
    elif strategy == "weight":
        key = lambda i: (-i.weight, -i.volume_cm3)
    elif strategy == "base_area":
        key = lambda i: (-(i.length * i.width), -i.weight)
    elif strategy == "density":
        key = lambda i: (-(i.weight / max(i.volume_cm3, 1.0)), -i.volume_cm3)
    elif strategy == "destination_lifo":
        key = lambda i: (route_rank(i), CATEGORY_RANK.get(i.category, 9), -i.volume_cm3)
    elif strategy == "random":
        out = list(items)
        rng.shuffle(out)
        return out
    else:
        key = lambda i: (CATEGORY_RANK.get(i.category, 9), -i.volume_cm3)
    out = sorted(items, key=key)
    if strategy != "random" and seed not in (0, None):
        # Small deterministic perturbation inside windows keeps multi-start useful.
        windowed: List[CargoItem] = []
        for start in range(0, len(out), 8):
            block = out[start : start + 8]
            if seed % 3:
                rng.shuffle(block)
            windowed.extend(block)
        out = windowed
    return out


def _temporary_item(item: CargoItem, truck_name: str, vehicle_id: str, trip_id: str, route: Sequence[str], x, y, z, l, w, h, orientation) -> PlacedItem:
    return PlacedItem(
        item=item,
        truck_type=truck_name,
        vehicle_id=vehicle_id,
        trip_id=trip_id,
        route=list(route),
        x=float(x),
        y=float(y),
        z=float(z),
        length=float(l),
        width=float(w),
        height=float(h),
        orientation=orientation,
    )


def _candidate_points(placed: Sequence[PlacedItem], truck: TruckType, bounds: Tuple[float, float], item_dims: Tuple[float, float, float]) -> List[Tuple[float, float, float]]:
    xmin, xmax = bounds
    l, w, h = item_dims
    xs = {xmin, max(xmin, xmax - l), max(xmin, xmin + (xmax - xmin - l) / 2.0)}
    ys = {0.0, max(0.0, truck.width - w), max(0.0, (truck.width - w) / 2.0)}
    zs = {0.0}
    x_span = max(0.0, xmax - xmin - l)
    x_step = max(20.0, min(l, 80.0))
    steps = int(x_span // x_step)
    for k in range(steps + 1):
        xs.add(xmin + k * x_step)
        xs.add(max(xmin, xmax - l - k * x_step))
    y_span = max(0.0, truck.width - w)
    y_step = max(20.0, min(w, 80.0))
    y_steps = int(y_span // y_step)
    for k in range(y_steps + 1):
        ys.add(k * y_step)
        ys.add(max(0.0, truck.width - w - k * y_step))
    pts = set()
    for x in xs:
        for y in ys:
            pts.add((round(x, 6), round(y, 6), 0.0))
    for p in placed:
        edges = [
            (p.x + p.length, p.y, p.z),
            (p.x, p.y + p.width, p.z),
            (p.x + p.length + 1.0, p.y, p.z),
            (p.x, p.y + p.width + 1.0, p.z),
            (p.x, p.y, p.z + p.height),
            (p.x + p.length, p.y, p.z + p.height),
            (p.x, p.y + p.width, p.z + p.height),
        ]
        for pt in edges:
            pts.add((round(pt[0], 6), round(pt[1], 6), round(pt[2], 6)))
    filtered = [
        pt
        for pt in pts
        if pt[0] >= xmin - EPS
        and pt[0] + l <= xmax + EPS
        and pt[1] >= -EPS
        and pt[1] + w <= truck.width + EPS
        and pt[2] >= -EPS
        and pt[2] + h <= truck.height + EPS
    ]
    filtered.sort(key=lambda p: (p[2], p[0], p[1]))
    return filtered[:CANDIDATE_POINT_LIMIT]


def _iii_stack_depth(candidate: PlacedItem, placed: Sequence[PlacedItem]) -> int:
    if candidate.category != "III":
        return 1
    depth = 1
    current = candidate
    seen = {candidate.item.item_id}
    while True:
        below = [
            p
            for p in placed
            if p.category == "III"
            and p.item.item_id not in seen
            and abs(p.z + p.height - current.z) <= 1e-5
            and xy_overlap_area_cm2(p, current) > 0.5 * min(p.length * p.width, current.length * current.width)
        ]
        if not below:
            return depth
        current = below[0]
        seen.add(current.item.item_id)
        depth += 1


def _fits_basic(candidate: PlacedItem, placed: Sequence[PlacedItem], truck: TruckType, bounds: Tuple[float, float]) -> bool:
    xmin, xmax = bounds
    if candidate.x < xmin - EPS or candidate.x + candidate.length > xmax + EPS:
        return False
    if candidate.y < -EPS or candidate.z < -EPS:
        return False
    if candidate.y + candidate.width > truck.width + EPS or candidate.z + candidate.height > truck.height + EPS:
        return False
    if candidate.category == "I" and abs(candidate.z) > EPS:
        return False
    for other in placed:
        if boxes_overlap(candidate, other):
            return False
        if {candidate.category, other.category} == {"II", "V"} and boxes_closed_intersect(candidate, other):
            return False
        if other.category == "II" and candidate.z >= other.z + other.height - EPS and xy_overlap_area_cm2(candidate, other) > EPS:
            return False
        if candidate.category == "II" and other.z >= candidate.z + candidate.height - EPS and xy_overlap_area_cm2(candidate, other) > EPS:
            return False
    if candidate.z > EPS:
        support = support_area_cm2(candidate, [*placed, candidate])
        if support + EPS < candidate.length * candidate.width * 0.99:
            return False
    if _iii_stack_depth(candidate, placed) > 2:
        return False
    return True


def _passes_local_constraints(candidate: PlacedItem, placed: Sequence[PlacedItem], truck: TruckType, mode: str) -> bool:
    trial = [*placed, candidate]
    if sum(p.weight for p in trial) > truck.max_payload + EPS:
        return False

    def pressure_on(lower: PlacedItem) -> float:
        area_m2 = lower.length * lower.width / 10_000.0
        if area_m2 <= EPS:
            return 0.0
        carried = 0.0
        for upper in trial:
            if upper is lower:
                continue
            if upper.z >= lower.z + lower.height - EPS:
                overlap = xy_overlap_area_cm2(lower, upper)
                if overlap > EPS:
                    carried += upper.weight * min(1.0, overlap / (upper.length * upper.width))
        return carried / area_m2

    affected = [candidate]
    affected.extend(
        p
        for p in placed
        if candidate.z >= p.z + p.height - EPS and xy_overlap_area_cm2(candidate, p) > EPS
    )
    for lower in affected:
        if pressure_on(lower) > MAX_TOP_PRESSURE_KG_PER_M2 + 1e-6:
            return False

    if mode == "strict" and candidate.route and candidate.destination:
        route = list(candidate.route)

        def order(dest: str | None) -> int:
            if dest in route:
                return route.index(dest)  # earlier index unloads earlier
            return 10_000

        for other in placed:
            if not other.destination or other.destination == candidate.destination:
                continue
            if order(candidate.destination) > order(other.destination) and lifo_blocks(candidate, other):
                return False
            if order(other.destination) > order(candidate.destination) and lifo_blocks(other, candidate):
                return False
    return True


def _placement_score(candidate: PlacedItem, truck: TruckType, route: Sequence[str], mode: str) -> Tuple[float, float, float, float]:
    if route and candidate.destination in route:
        idx = route.index(candidate.destination)
        if len(route) == 1:
            target = truck.length / 2.0
        else:
            target = truck.length * (0.82 - 0.64 * idx / max(1, len(route) - 1))
    else:
        target = truck.length / 2.0
    # Bottom-left-back packing, with a mild pull toward the CG target.
    return (
        candidate.z,
        abs(candidate.x + candidate.length / 2.0 - target) * 0.03 + candidate.x * 0.001,
        candidate.y,
        candidate.x,
    )


def pack_items(
    items: Sequence[CargoItem],
    truck: TruckType | str,
    *,
    vehicle_id: str = "V1",
    trip_id: str = "T1",
    route: Sequence[str] | None = None,
    mode: str = "strict",
    strategy: str = "category",
    seed: int = 0,
    x_bounds: Optional[Tuple[float, float]] = None,
    allow_unpacked: bool = True,
    center_after: bool = True,
) -> Tuple[List[PlacedItem], List[CargoItem]]:
    if isinstance(truck, str):
        truck = TRUCK_TYPES[truck]
    route = list(route or [])
    bounds = x_bounds or (0.0, truck.length)
    ordered = sort_items(items, strategy=strategy, seed=seed, route=route)
    placed: List[PlacedItem] = []
    unpacked: List[CargoItem] = []

    for item in ordered:
        best: Optional[PlacedItem] = None
        best_score = None
        orientations = legal_orientations(item)
        # Larger footprint first improves support and reduces fragile bridges.
        orientations = sorted(orientations, key=lambda o: (-(o[0] * o[1]), o[2]))
        for l, w, h, orient in orientations:
            for x, y, z in _candidate_points(placed, truck, bounds, (l, w, h)):
                cand = _temporary_item(item, truck.name, vehicle_id, trip_id, route, x, y, z, l, w, h, orient)
                if not _fits_basic(cand, placed, truck, bounds):
                    continue
                if not _passes_local_constraints(cand, placed, truck, mode):
                    continue
                score = _placement_score(cand, truck, route, mode)
                if best is None or score < best_score:
                    best = cand
                    best_score = score
        if best is None:
            unpacked.append(item)
            if not allow_unpacked:
                return placed, [*unpacked, *ordered[ordered.index(item) + 1 :]]
        else:
            placed.append(best)

    if center_after and placed:
        _shift_to_center(placed, truck, bounds)
    return placed, unpacked


def _shift_to_center(placed: List[PlacedItem], truck: TruckType, bounds: Tuple[float, float]) -> None:
    xmin, xmax = bounds
    min_x = min(p.x for p in placed)
    max_x = max(p.x + p.length for p in placed)
    span = max_x - min_x
    if span > (xmax - xmin) + EPS:
        return
    current_cg = weighted_x_cg(placed)
    target = truck.length / 2.0
    shift = target - current_cg
    low_limit = xmin - min_x
    high_limit = xmax - max_x
    shift = min(high_limit, max(low_limit, shift))
    if abs(shift) > EPS:
        for p in placed:
            p.x += shift


def pack_route_banded(
    items: Sequence[CargoItem],
    truck: TruckType | str,
    route: Sequence[str],
    *,
    vehicle_id: str = "V1",
    trip_id: str = "T1",
    mode: str = "strict",
    strategy: str = "destination_lifo",
    seed: int = 0,
) -> Tuple[List[PlacedItem], List[CargoItem]]:
    if isinstance(truck, str):
        truck = TRUCK_TYPES[truck]
    if len(route) <= 1:
        return pack_items(items, truck, vehicle_id=vehicle_id, trip_id=trip_id, route=route, mode=mode, strategy=strategy, seed=seed)

    by_dest: Dict[str, List[CargoItem]] = {s: [] for s in route}
    for item in items:
        if item.destination in by_dest:
            by_dest[item.destination].append(item)
    volumes = {s: sum(i.volume_cm3 for i in by_dest[s]) for s in route}
    total_v = sum(volumes.values()) or 1.0
    gap = 2.0
    usable = truck.length - gap * (len(route) - 1)

    def min_station_length(group: Sequence[CargoItem]) -> float:
        # Category I must be on the floor and category II is fragile/top-layer;
        # giving these groups enough discrete X rows prevents tiny-volume
        # stations from receiving an unrealistically narrow LIFO band.
        required = 80.0
        for category in ("I", "II"):
            cat_items = [it for it in group if it.category == category]
            if not cat_items:
                continue
            by_shape: Dict[Tuple[float, float, float], List[CargoItem]] = {}
            for it in cat_items:
                by_shape.setdefault((it.length, it.width, it.height), []).append(it)
            for same_shape in by_shape.values():
                sample = same_shape[0]
                best_need = float("inf")
                for l, w, _h, _ in legal_orientations(sample):
                    if w > truck.width + EPS:
                        continue
                    per_row = max(1, int((truck.width + EPS) // w))
                    rows = (len(same_shape) + per_row - 1) // per_row
                    best_need = min(best_need, rows * l)
                if best_need < float("inf"):
                    required = max(required, best_need)
        return min(required, usable)

    minimums = {s: min_station_length(by_dest[s]) for s in route}
    min_total = sum(minimums.values())
    if min_total > usable:
        scale = usable / min_total
        band_len = {s: minimums[s] * scale for s in route}
    else:
        leftover = usable - min_total
        band_len = {s: minimums[s] + leftover * (volumes[s] / total_v) for s in route}

    placed_all: List[PlacedItem] = []
    unpacked_all: List[CargoItem] = []
    cursor = 0.0
    # Later stops are deeper; first stop is nearest the door.
    for dest in reversed(route):
        length = band_len[dest]
        bounds = (cursor, cursor + length)
        group = by_dest[dest]
        placed, unpacked = pack_items(
            group,
            truck,
            vehicle_id=vehicle_id,
            trip_id=trip_id,
            route=route,
            mode=mode,
            strategy=strategy,
            seed=seed,
            x_bounds=bounds,
            allow_unpacked=True,
            center_after=False,
        )
        placed_all.extend(placed)
        unpacked_all.extend(unpacked)
        cursor += length + gap
    _shift_to_center(placed_all, truck, (0.0, truck.length))
    return placed_all, unpacked_all


def multi_start_pack(
    items: Sequence[CargoItem],
    truck: TruckType | str,
    *,
    route: Sequence[str] | None = None,
    mode: str = "strict",
    vehicle_id: str = "V1",
    trip_id: str = "T1",
    strategies: Sequence[str] | None = None,
    seeds: Sequence[int] | None = None,
    require_all: bool = False,
    banded: bool = False,
) -> Tuple[List[PlacedItem], List[CargoItem], Dict[str, object]]:
    if isinstance(truck, str):
        truck = TRUCK_TYPES[truck]
    strategies = list(strategies or ["category", "volume", "weight", "base_area", "density", "destination_lifo", "random"])
    seeds = list(seeds or [0, 1, 42])
    route = list(route or [])
    best_placed: List[PlacedItem] = []
    best_unpacked: List[CargoItem] = list(items)
    best_meta: Dict[str, object] = {}
    best_score = -1e18

    for strategy in strategies:
        for seed in seeds:
            if banded and len(route) > 1:
                placed, unpacked = pack_route_banded(
                    items,
                    truck,
                    route,
                    vehicle_id=vehicle_id,
                    trip_id=trip_id,
                    mode=mode,
                    strategy=strategy,
                    seed=seed,
                )
            else:
                placed, unpacked = pack_items(
                    items,
                    truck,
                    vehicle_id=vehicle_id,
                    trip_id=trip_id,
                    route=route,
                    mode=mode,
                    strategy=strategy,
                    seed=seed,
                )
            report = validate_items(placed, mode=mode, expected_item_ids=None)
            if report["hard_violation_count"] > 0:
                continue
            if require_all and unpacked:
                continue
            vol_util = sum(p.volume_cm3 for p in placed) / truck.volume_cm3
            wt_util = sum(p.weight for p in placed) / truck.max_payload
            xcg = weighted_x_cg(placed) if placed else 0.0
            cg_penalty = abs(xcg - truck.length / 2.0) / truck.length
            score = 0.45 * vol_util + 0.35 * wt_util - 0.20 * cg_penalty - 10.0 * (len(unpacked) / max(1, len(items)))
            if score > best_score:
                best_score = score
                best_placed = placed
                best_unpacked = unpacked
                best_meta = {
                    "strategy": strategy,
                    "seed": seed,
                    "score": score,
                    "volume_utilization": vol_util,
                    "weight_utilization": wt_util,
                    "x_cg": xcg,
                    "hard_violation_count": report["hard_violation_count"],
                }
    return best_placed, best_unpacked, best_meta
