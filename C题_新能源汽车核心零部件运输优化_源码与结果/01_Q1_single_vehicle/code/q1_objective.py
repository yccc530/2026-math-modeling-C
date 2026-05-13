# -*- coding: utf-8 -*-
"""Lexicographic objective and bounds for Q1."""

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

from typing import Iterable, Sequence

from data_config import SCENARIO_A_TYPES, TRUCK_TYPES
from geometry import EPS, support_area_cm2, total_volume_cm3, total_weight, weighted_x_cg, xy_overlap_area_cm2
from validator import MAX_TOP_PRESSURE_KG_PER_M2


def q1_margins(placed: Sequence, truck=TRUCK_TYPES["HeavyEV"]) -> dict:
    xcg = weighted_x_cg(placed)
    cg_margin = min(xcg - truck.length / 3.0, 2.0 * truck.length / 3.0 - xcg) if placed else 0.0
    min_support_margin = 1.0
    min_bearing_margin = MAX_TOP_PRESSURE_KG_PER_M2
    for item in placed:
        if item.z > EPS:
            ratio = support_area_cm2(item, placed) / max(item.length * item.width, EPS)
            min_support_margin = min(min_support_margin, ratio - 0.99)
        area_m2 = item.length * item.width / 10000.0
        carried = 0.0
        for upper in placed:
            if upper is item:
                continue
            if upper.z >= item.z + item.height - EPS:
                overlap = xy_overlap_area_cm2(item, upper)
                if overlap > EPS:
                    carried += upper.weight * min(1.0, overlap / max(upper.length * upper.width, EPS))
        pressure = carried / max(area_m2, EPS)
        min_bearing_margin = min(min_bearing_margin, MAX_TOP_PRESSURE_KG_PER_M2 - pressure)
    return {
        "x_cg": xcg,
        "cg_offset": abs(xcg - truck.length / 2.0) / truck.length if placed else 1.0,
        "cg_margin": cg_margin,
        "min_support_margin": min_support_margin,
        "min_load_bearing_margin": min_bearing_margin,
    }


def q1_score_tuple(placed: Sequence, truck=TRUCK_TYPES["HeavyEV"]) -> tuple:
    margins = q1_margins(placed, truck)
    return (
        len(placed),
        total_volume_cm3(placed),
        total_weight(placed),
        -margins["cg_offset"],
        margins["cg_margin"],
        margins["min_support_margin"],
        margins["min_load_bearing_margin"],
    )


def q1_upper_bounds() -> dict:
    truck = TRUCK_TYPES["HeavyEV"]
    total_items = sum(c.quantity for c in SCENARIO_A_TYPES)
    total_volume = sum(c.volume_cm3 * c.quantity for c in SCENARIO_A_TYPES)
    total_weight_all = sum(c.weight * c.quantity for c in SCENARIO_A_TYPES)
    floor_area = truck.length * truck.width
    category_i = next(c for c in SCENARIO_A_TYPES if c.category == "I")
    category_ii = next(c for c in SCENARIO_A_TYPES if c.category == "II")
    i_floor_area_bound = int(floor_area // (category_i.length * category_i.width))
    ii_top_area_bound = int(floor_area // min(category_ii.length * category_ii.width, category_ii.width * category_ii.length))
    # Relaxed item-count upper bound: choose smallest-volume items first under
    # volume and weight capacities, ignoring geometry and class constraints.
    unit_items = []
    for c in SCENARIO_A_TYPES:
        unit_items.extend([(c.volume_cm3, c.weight, c.code)] * c.quantity)
    by_volume = sorted(unit_items)
    v = w = count_v = 0
    for vol, wt, _ in by_volume:
        if v + vol <= truck.volume_cm3 + EPS and w + wt <= truck.max_payload + EPS:
            v += vol
            w += wt
            count_v += 1
    return {
        "total_item_count": total_items,
        "truck_volume_cm3": truck.volume_cm3,
        "total_cargo_volume_cm3": total_volume,
        "volume_upper_m3": min(truck.volume_cm3, total_volume) / 1_000_000.0,
        "weight_upper_kg": min(truck.max_payload, total_weight_all),
        "relaxed_count_upper": count_v,
        "category_i_floor_area_upper": min(category_i.quantity, i_floor_area_bound),
        "category_ii_top_area_upper": min(category_ii.quantity, ii_top_area_bound),
    }

