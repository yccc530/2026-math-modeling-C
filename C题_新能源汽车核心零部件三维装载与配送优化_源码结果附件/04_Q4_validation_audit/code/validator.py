# -*- coding: utf-8 -*-
"""Independent coordinate-level validator.

The module can be imported by solvers and can also be run as:

    python validator.py --csv results/result_q2_loading.csv --mode strict
"""

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

import argparse
import csv
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from data_config import (
    REPORTS_DIR,
    RESULTS_DIR,
    TRUCK_TYPES,
    cargo_type_lookup,
    expand_q3_items,
    expand_scenario_b_items,
    load_q3_cargo_types,
)
from geometry import (
    EPS,
    boxes_closed_intersect,
    boxes_overlap,
    interval_overlap,
    lifo_blocks,
    support_area_cm2,
    total_volume_cm3,
    total_weight,
    weighted_x_cg,
    xy_overlap_area_cm2,
)


MAX_TOP_PRESSURE_KG_PER_M2 = 400.0
MIN_SUPPORT_RATIO = 0.99


def _violation(vehicle_id: str, item_id: str, violation_type: str, description: str, related_item_id: str = "") -> Dict[str, str]:
    return {
        "vehicle_id": vehicle_id,
        "trip_id": vehicle_id,
        "item_id": item_id,
        "violation_type": violation_type,
        "description": description,
        "related_item_id": related_item_id,
    }


def row_to_item(row: Dict[str, str]):
    return SimpleNamespace(
        scenario=row.get("scenario", ""),
        mode=row.get("mode", ""),
        trip_id=row.get("trip_id") or row.get("vehicle_id") or "V1",
        vehicle_id=row.get("vehicle_id") or row.get("trip_id") or "V1",
        truck_type=row["truck_type"],
        route=[s for s in (row.get("route") or "").split("->") if s and s != "Depot"],
        destination=row.get("destination") or "",
        item_id=row["item_id"],
        cargo_code=row.get("cargo_code", ""),
        category=row["category"],
        x=float(row["x"]),
        y=float(row["y"]),
        z=float(row["z"]),
        length=float(row["length"]),
        width=float(row["width"]),
        height=float(row["height"]),
        weight=float(row["weight"]),
        original_length=float(row.get("original_length") or row["length"]),
        original_width=float(row.get("original_width") or row["width"]),
        original_height=float(row.get("original_height") or row["height"]),
        orientation=row.get("orientation", ""),
    )


def read_loading_csv(path: Path) -> List:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return [row_to_item(row) for row in csv.DictReader(f)]


def _group_by_trip(items: Iterable) -> Dict[str, List]:
    grouped: Dict[str, List] = {}
    for item in items:
        grouped.setdefault(item.trip_id, []).append(item)
    return grouped


def _route_order(route: Sequence[str], destination: str) -> int:
    try:
        return list(route).index(destination)
    except ValueError:
        return 10_000


def validate_items(
    items: Sequence,
    *,
    mode: str = "strict",
    expected_item_ids: Optional[Iterable[str]] = None,
    relocation_volume_limit: float = 0.15,
) -> Dict[str, object]:
    violations: List[Dict[str, str]] = []
    warning_violations: List[Dict[str, str]] = []
    grouped = _group_by_trip(items)
    pair_checks = 0
    lifo_violation_count = 0
    relocation_ids = set()
    relocation_volume_cm3 = 0.0

    for trip_id, group in grouped.items():
        if not group:
            continue
        truck_name = group[0].truck_type
        truck = TRUCK_TYPES[truck_name]
        route = group[0].route

        for item in group:
            if item.x < -EPS or item.y < -EPS or item.z < -EPS:
                violations.append(_violation(trip_id, item.item_id, "out_of_bounds", "negative coordinate"))
            if item.x + item.length > truck.length + EPS or item.y + item.width > truck.width + EPS or item.z + item.height > truck.height + EPS:
                violations.append(_violation(trip_id, item.item_id, "out_of_bounds", "item exceeds truck inner dimensions"))

            if item.category == "I":
                if abs(item.z) > EPS:
                    violations.append(_violation(trip_id, item.item_id, "category_I", "category I must be placed on the floor"))
                if (
                    abs(item.length - item.original_length) > EPS
                    or abs(item.width - item.original_width) > EPS
                    or abs(item.height - item.original_height) > EPS
                ):
                    violations.append(_violation(trip_id, item.item_id, "category_I", "category I has fixed orientation"))
            if item.category == "II":
                if abs(item.height - item.original_height) > EPS:
                    violations.append(_violation(trip_id, item.item_id, "category_II", "category II must keep Z axis up"))

        for i, a in enumerate(group):
            for b in group[i + 1 :]:
                if boxes_overlap(a, b):
                    violations.append(_violation(trip_id, a.item_id, "overlap", "3D boxes overlap", b.item_id))
                if {a.category, b.category} == {"II", "V"} and boxes_closed_intersect(a, b):
                    violations.append(_violation(trip_id, a.item_id, "category_V_II_contact", "category V and II touch or overlap", b.item_id))

        for item in group:
            if item.z > EPS:
                support = support_area_cm2(item, group)
                required = item.length * item.width * MIN_SUPPORT_RATIO
                if support + EPS < required:
                    violations.append(
                        _violation(
                            trip_id,
                            item.item_id,
                            "unsupported",
                            f"support area {support:.2f} cm2 below required {required:.2f} cm2",
                        )
                    )

        for lower in group:
            top_area_m2 = lower.length * lower.width / 10_000.0
            if top_area_m2 <= EPS:
                continue
            carried = 0.0
            for upper in group:
                if upper is lower:
                    continue
                if upper.z >= lower.z + lower.height - EPS:
                    overlap = xy_overlap_area_cm2(lower, upper)
                    if overlap > EPS:
                        upper_area = upper.length * upper.width
                        carried += upper.weight * min(1.0, overlap / upper_area)
            pressure = carried / top_area_m2
            if pressure > MAX_TOP_PRESSURE_KG_PER_M2 + 1e-6:
                violations.append(
                    _violation(
                        trip_id,
                        lower.item_id,
                        "bearing",
                        f"top pressure {pressure:.2f} kg/m2 exceeds {MAX_TOP_PRESSURE_KG_PER_M2}",
                    )
                )

        for lower in group:
            if lower.category != "II":
                continue
            for upper in group:
                if upper is lower:
                    continue
                if upper.z >= lower.z + lower.height - EPS and xy_overlap_area_cm2(lower, upper) > EPS:
                    violations.append(_violation(trip_id, lower.item_id, "category_II_top", "category II has cargo above", upper.item_id))

        # Category III: no three consecutive directly stacked motor layers.
        for item in group:
            if item.category != "III":
                continue
            count = 1
            current = item
            seen = {item.item_id}
            while True:
                below_candidates = [
                    other
                    for other in group
                    if other.category == "III"
                    and other.item_id not in seen
                    and abs(other.z + other.height - current.z) <= 1e-5
                    and xy_overlap_area_cm2(other, current) > 0.5 * min(other.length * other.width, current.length * current.width)
                ]
                if not below_candidates:
                    break
                below = below_candidates[0]
                seen.add(below.item_id)
                count += 1
                current = below
            if count > 2:
                violations.append(_violation(trip_id, item.item_id, "category_III_stack", "more than two consecutive category III layers"))

        load_weight = total_weight(group)
        if load_weight > truck.max_payload + EPS:
            violations.append(_violation(trip_id, "*", "payload", f"payload {load_weight:.2f} kg exceeds {truck.max_payload:.2f} kg"))

        xcg = weighted_x_cg(group)
        if group and not (truck.length / 3.0 - EPS <= xcg <= 2.0 * truck.length / 3.0 + EPS):
            violations.append(_violation(trip_id, "*", "center_of_gravity", f"Xcg {xcg:.2f} outside [{truck.length/3:.2f}, {2*truck.length/3:.2f}]"))

        if route:
            for a in group:
                for b in group:
                    if a is b or not a.destination or not b.destination or a.destination == b.destination:
                        continue
                    order_a = _route_order(route, a.destination)
                    order_b = _route_order(route, b.destination)
                    if order_a > order_b:
                        pair_checks += 1
                        if lifo_blocks(a, b):
                            lifo_violation_count += 1
                            if mode == "strict":
                                violations.append(_violation(trip_id, a.item_id, "lifo_block", "later-stop item blocks earlier-stop item", b.item_id))
                            else:
                                warning_violations.append(
                                    _violation(trip_id, a.item_id, "flexible_relocation", "item must be temporarily relocated", b.item_id)
                                )
                                relocation_ids.add((trip_id, a.item_id))

    relocation_lookup = {(i.trip_id, i.item_id): i for i in items}
    for key in relocation_ids:
        item = relocation_lookup.get(key)
        if item:
            relocation_volume_cm3 += item.length * item.width * item.height

    all_ids = [i.item_id for i in items]
    duplicates = sorted({x for x in all_ids if all_ids.count(x) > 1})
    for dup in duplicates:
        violations.append(_violation("*", dup, "duplicate_item", "item appears more than once"))

    missing: List[str] = []
    if expected_item_ids is not None:
        expected = set(expected_item_ids)
        loaded = set(all_ids)
        missing = sorted(expected - loaded)
        extra = sorted(loaded - expected)
        for m in missing:
            violations.append(_violation("*", m, "missing_item", "expected item is not loaded"))
        for e in extra:
            violations.append(_violation("*", e, "unknown_item", "loaded item is not in expected set"))

    loaded_volume_cm3 = total_volume_cm3(items)
    relocation_ratio = relocation_volume_cm3 / loaded_volume_cm3 if loaded_volume_cm3 else 0.0
    if mode == "flexible" and relocation_ratio > relocation_volume_limit + EPS:
        violations.append(
            _violation(
                "*",
                "*",
                "relocation_ratio",
                f"relocation volume ratio {relocation_ratio:.4f} exceeds {relocation_volume_limit:.4f}",
            )
        )

    hard_count = len(violations)
    return {
        "status": "PASS" if hard_count == 0 else "FAIL",
        "hard_violation_count": hard_count,
        "soft_violation_count": len(warning_violations),
        "lifo_pair_checks": pair_checks,
        "lifo_violation_count": lifo_violation_count,
        "relocation_count": len(relocation_ids),
        "relocation_volume_m3": relocation_volume_cm3 / 1_000_000.0,
        "relocation_volume_ratio": relocation_ratio,
        "loaded_item_count": len(items),
        "duplicate_item_count": len(duplicates),
        "missing_item_count": len(missing),
        "violations": violations,
        "soft_violations": warning_violations,
    }


def expected_ids_for_scenario(scenario: str) -> Optional[List[str]]:
    scenario = scenario.lower()
    if scenario == "q2":
        return [i.item_id for i in expand_scenario_b_items()]
    if scenario.startswith("q3"):
        q3_types = load_q3_cargo_types(RESULTS_DIR / "generated_cargo_q3.csv")
        if q3_types:
            return [i.item_id for i in expand_q3_items(q3_types)]
    return None


def validate_loading_csv(
    csv_path: Path,
    *,
    mode: str = "strict",
    scenario: str = "",
    output_prefix: str = "validation_report",
    expected_item_ids: Optional[Iterable[str]] = None,
) -> Dict[str, object]:
    items = read_loading_csv(csv_path)
    if not scenario and items:
        scenario = str(getattr(items[0], "scenario", ""))
    if expected_item_ids is None:
        expected_item_ids = expected_ids_for_scenario(scenario)
    report = validate_items(items, mode=mode, expected_item_ids=expected_item_ids)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / f"{output_prefix}.json"
    txt_path = REPORTS_DIR / f"{output_prefix}.txt"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with txt_path.open("w", encoding="utf-8") as f:
        if report["status"] == "PASS":
            f.write("PASS: no violations found\n")
        else:
            f.write(f"FAIL: {report['hard_violation_count']} hard violations found\n")
        f.write(f"loaded_item_count: {report['loaded_item_count']}\n")
        f.write(f"lifo_pair_checks: {report['lifo_pair_checks']}\n")
        f.write(f"lifo_violation_count: {report['lifo_violation_count']}\n")
        f.write(f"relocation_count: {report['relocation_count']}\n")
        f.write(f"relocation_volume_m3: {report['relocation_volume_m3']:.6f}\n")
        for v in report["violations"][:500]:
            f.write(f"{v}\n")
        if len(report["violations"]) > 500:
            f.write(f"... {len(report['violations']) - 500} more violations omitted\n")
    return report


def infer_prefix(path: Path, mode: str) -> str:
    stem = path.stem
    if "q1" in stem:
        return "validation_report_q1"
    if "q2" in stem:
        return "validation_report_q2"
    if "q3" in stem and "strict" in stem:
        return "validation_report_q3_strict"
    if "q3" in stem and "flexible" in stem:
        return "validation_report_q3_flexible"
    return f"validation_report_{stem}_{mode}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--mode", choices=["strict", "flexible"], default="strict")
    parser.add_argument("--scenario", default="")
    parser.add_argument("--output-prefix", default="")
    args = parser.parse_args()
    prefix = args.output_prefix or infer_prefix(args.csv, args.mode)
    report = validate_loading_csv(args.csv, mode=args.mode, scenario=args.scenario, output_prefix=prefix)
    if report["status"] == "PASS":
        print("PASS: no violations found")
        return 0
    print(f"FAIL: {report['hard_violation_count']} hard violations found")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

