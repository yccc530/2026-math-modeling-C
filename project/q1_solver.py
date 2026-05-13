# -*- coding: utf-8 -*-
"""Solver for Question 1: single HeavyEV packing with CG control."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

from data_config import (
    PLOTS_DIR,
    REPORTS_DIR,
    RESULTS_DIR,
    SEEDS,
    TRUCK_TYPES,
    ensure_directories,
    expand_scenario_a_items,
    write_loading_csv,
)
from geometry import total_volume_cm3, total_weight, weighted_x_cg
from packing import multi_start_pack
from q1_objective import q1_margins, q1_score_tuple, q1_upper_bounds
from validator import validate_loading_csv
from visualization import plot_loading


def solve_q1(iteration: int = 0) -> Dict[str, object]:
    ensure_directories()
    items = expand_scenario_a_items()
    truck = TRUCK_TYPES["HeavyEV"]
    all_seeds = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 42, 66, 88, 100, 2026, 4096]
    # Q1's primary goal is loaded_count. Category-first all-seed search found
    # the best incumbent; other orderings are sampled to keep the Pareto record.
    experiments = [("category", seed if iteration == 0 else seed + iteration * 17) for seed in all_seeds]
    experiments.extend((strategy, 0 if iteration == 0 else iteration * 17) for strategy in ["volume", "weight", "base_area", "density", "random"])

    best = None
    best_meta = None
    feasible_records: List[Dict[str, object]] = []
    for strategy, seed in experiments:
        placed, unpacked, meta = multi_start_pack(
            items,
            truck,
            route=[],
            mode="strict",
            vehicle_id="Q1_V1",
            trip_id="Q1_T1",
            strategies=[strategy],
            seeds=[seed],
            require_all=False,
            banded=False,
        )
        if not placed:
            continue
        vol_util = total_volume_cm3(placed) / truck.volume_cm3
        wt_util = total_weight(placed) / truck.max_payload
        xcg = weighted_x_cg(placed)
        weighted_score = 0.45 * vol_util + 0.35 * wt_util - 0.20 * abs(xcg - truck.length / 2) / truck.length
        objective_tuple = q1_score_tuple(placed, truck)
        margins = q1_margins(placed, truck)
        record = {
            **meta,
            "strategy": strategy,
            "seed": seed,
            "weighted_score": weighted_score,
            "objective_tuple": objective_tuple,
            "loaded_count": len(placed),
            "loaded_volume_m3": total_volume_cm3(placed) / 1_000_000.0,
            "loaded_weight": total_weight(placed),
            "volume_utilization": vol_util,
            "weight_utilization": wt_util,
            "x_cg": xcg,
            **margins,
            "_placed": placed,
            "_unpacked": unpacked,
        }
        feasible_records.append(record)
        if best is None or objective_tuple > best_meta["objective_tuple"]:
            best = (placed, unpacked)
            best_meta = record

    # Compatibility fallback, should not be used unless all single-strategy
    # starts fail for an unexpected reason.
    if best is None:
        placed, unpacked, meta = multi_start_pack(
            items,
            truck,
            route=[],
            mode="strict",
            vehicle_id="Q1_V1",
            trip_id="Q1_T1",
            strategies=strategies,
            seeds=window,
            require_all=False,
            banded=False,
        )
        vol_util = total_volume_cm3(placed) / truck.volume_cm3
        wt_util = total_weight(placed) / truck.max_payload
        xcg = weighted_x_cg(placed)
        score = 0.45 * vol_util + 0.35 * wt_util - 0.20 * abs(xcg - truck.length / 2) / truck.length
        best = (placed, unpacked)
        best_meta = {**meta, "weighted_score": score, "objective_tuple": q1_score_tuple(placed, truck), "volume_utilization": vol_util, "weight_utilization": wt_util, "x_cg": xcg, **q1_margins(placed, truck)}

    if best is None:
        raise RuntimeError("Q1 did not find any feasible loading")

    placed, unpacked = best
    loading_path = RESULTS_DIR / "result_q1_loading.csv"
    write_loading_csv(placed, loading_path, scenario="q1", mode="strict")
    report = validate_loading_csv(loading_path, mode="strict", scenario="q1", output_prefix="validation_report_q1")

    summary_path = RESULTS_DIR / "result_q1_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "truck_type",
                "loaded_item_count",
                "unloaded_item_count",
                "load_weight",
                "load_volume_m3",
                "volume_utilization",
                "weight_utilization",
                "x_cg",
                "score",
                "objective_tuple",
                "cg_margin",
                "min_support_margin",
                "min_load_bearing_margin",
                "strategy",
                "seed",
                "validation_status",
                "hard_violation_count",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "truck_type": truck.name,
                "loaded_item_count": len(placed),
                "unloaded_item_count": len(unpacked),
                "load_weight": round(total_weight(placed), 6),
                "load_volume_m3": round(total_volume_cm3(placed) / 1_000_000.0, 6),
                "volume_utilization": round(best_meta["volume_utilization"], 6),
                "weight_utilization": round(best_meta["weight_utilization"], 6),
                "x_cg": round(best_meta["x_cg"], 6),
                "score": str(best_meta["objective_tuple"]),
                "objective_tuple": str(best_meta["objective_tuple"]),
                "cg_margin": round(best_meta.get("cg_margin", 0), 6),
                "min_support_margin": round(best_meta.get("min_support_margin", 0), 6),
                "min_load_bearing_margin": round(best_meta.get("min_load_bearing_margin", 0), 6),
                "strategy": best_meta.get("strategy", ""),
                "seed": best_meta.get("seed", ""),
                "validation_status": report["status"],
                "hard_violation_count": report["hard_violation_count"],
            }
        )

    unloaded_path = RESULTS_DIR / "result_q1_unloaded.csv"
    with unloaded_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["item_id", "cargo_code", "category", "length", "width", "height", "weight"])
        writer.writeheader()
        for item in unpacked:
            writer.writerow(
                {
                    "item_id": item.item_id,
                    "cargo_code": item.cargo_code,
                    "category": item.category,
                    "length": item.length,
                    "width": item.width,
                    "height": item.height,
                    "weight": item.weight,
                }
            )

    _write_q1_optimization_artifacts(feasible_records, best_meta, truck)
    plot_loading(loading_path, PLOTS_DIR / "q1_3d_plot.png", title="Q1 HeavyEV")
    return {
        "status": report["status"],
        "hard_violation_count": report["hard_violation_count"],
        "loaded_item_count": len(placed),
        "unloaded_item_count": len(unpacked),
        "volume_utilization": best_meta["volume_utilization"],
        "weight_utilization": best_meta["weight_utilization"],
        "score": best_meta["objective_tuple"],
        "x_cg": best_meta["x_cg"],
    }


def _write_q1_optimization_artifacts(records: List[Dict[str, object]], best_meta: Dict[str, object], truck) -> None:
    records = sorted(records, key=lambda r: r["objective_tuple"], reverse=True)
    path = RESULTS_DIR / "q1_best_solutions.csv"
    fields = [
        "rank",
        "strategy",
        "seed",
        "loaded_count",
        "loaded_volume_m3",
        "loaded_weight",
        "volume_utilization",
        "weight_utilization",
        "x_cg",
        "cg_offset",
        "cg_margin",
        "min_support_margin",
        "min_load_bearing_margin",
        "objective_tuple",
        "weighted_score",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for idx, r in enumerate(records[:20], start=1):
            writer.writerow({k: (idx if k == "rank" else r.get(k, "")) for k in fields})

    bounds = q1_upper_bounds()
    best_volume = float(best_meta.get("loaded_volume_m3", 0))
    best_count = int(best_meta.get("loaded_count", 0))
    report = REPORTS_DIR / "q1_optimization_report.md"
    report.write_text(
        "# Q1 Optimization Report\n\n"
        "Objective: lexicographic maximization of loaded count, loaded volume, loaded weight, then CG/safety margins.\n\n"
        f"Feasible starts evaluated: {len(records)}\n\n"
        f"Best strategy: {best_meta.get('strategy')} seed={best_meta.get('seed')}\n\n"
        f"Best objective tuple: `{best_meta.get('objective_tuple')}`\n\n"
        f"Relaxed count upper bound: {bounds['relaxed_count_upper']}; current count: {best_count}; gap: {bounds['relaxed_count_upper'] - best_count}\n\n"
        f"Relaxed volume upper bound: {bounds['volume_upper_m3']:.6f} m3; current volume: {best_volume:.6f} m3; "
        f"gap: {max(0.0, bounds['volume_upper_m3'] - best_volume):.6f} m3\n\n"
        f"Category I floor-area upper: {bounds['category_i_floor_area_upper']}; Category II top-area upper: {bounds['category_ii_top_area_upper']}.\n\n"
        "The bounds ignore detailed 3D geometry, support, pressure and class interactions, so they are optimistic.\n",
        encoding="utf-8",
    )
    _plot_q1_pareto(records)


def _plot_q1_pareto(records: List[Dict[str, object]]) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        xs = [float(r["loaded_volume_m3"]) for r in records]
        ys = [float(r["loaded_weight"]) for r in records]
        cs = [float(r["cg_offset"]) for r in records]
        fig, ax = plt.subplots(figsize=(7, 4))
        sc = ax.scatter(xs, ys, c=cs, cmap="viridis_r", s=55)
        ax.set_xlabel("Loaded volume (m3)")
        ax.set_ylabel("Loaded weight (kg)")
        ax.set_title("Q1 feasible solution frontier")
        fig.colorbar(sc, ax=ax, label="CG offset ratio")
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / "q1_pareto_front.png", dpi=180)
        plt.close(fig)
    except Exception:
        (PLOTS_DIR / "q1_pareto_front.txt").write_text("matplotlib plot failed\n", encoding="utf-8")


if __name__ == "__main__":
    print(solve_q1())
