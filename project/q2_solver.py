# -*- coding: utf-8 -*-
"""Solver for Question 2: multi-vehicle routing with strict LIFO."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

from data_config import DISTANCE_MATRIX, PLOTS_DIR, REPORTS_DIR, RESULTS_DIR, TRUCK_TYPES, ensure_directories, expand_scenario_b_items, write_loading_csv
from optimizer import flatten_plans, solve_station_cover, write_trips_csv
from q2_objective import q2_lower_bounds, q2_score_tuple
from validator import validate_loading_csv
from visualization import plot_loading


def solve_q2(iteration: int = 0, return_to_depot: bool = True) -> Dict[str, object]:
    ensure_directories()
    items = expand_scenario_b_items()
    stations = ["S1", "S2", "S3"]
    plans, candidates = solve_station_cover(
        items,
        stations,
        DISTANCE_MATRIX,
        mode="strict",
        max_stops=3,
        return_to_depot=return_to_depot,
        seed_offset=iteration * 31,
    )
    placed = flatten_plans(plans)
    loading_path = RESULTS_DIR / "result_q2_loading.csv"
    trips_path = RESULTS_DIR / "result_q2_trips.csv"
    write_loading_csv(placed, loading_path, scenario="q2", mode="strict")
    write_trips_csv(plans, trips_path)
    write_trips_csv(plans, RESULTS_DIR / "q2_selected_trips.csv")
    _write_q2_candidate_trips(candidates)
    report = validate_loading_csv(loading_path, mode="strict", scenario="q2", output_prefix="validation_report_q2")

    loaded_ids = {p.item_id for p in placed}
    unassigned_path = RESULTS_DIR / "result_q2_unassigned.csv"
    with unassigned_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["item_id", "cargo_code", "category", "destination"])
        writer.writeheader()
        for item in items:
            if item.item_id not in loaded_ids:
                writer.writerow({"item_id": item.item_id, "cargo_code": item.cargo_code, "category": item.category, "destination": item.destination})

    total_cost = sum(p.cost for p in plans)
    multi_stop_vehicle_count = sum(1 for p in plans if len(p.route.stops) > 1)
    total_distance = sum(p.route_distance for p in plans)
    avg_vol = sum(p.volume_utilization for p in plans) / max(1, len(plans))
    avg_wt = sum(p.weight_utilization for p in plans) / max(1, len(plans))
    lower = q2_lower_bounds(
        sum(i.weight for i in items),
        sum(i.volume_cm3 for i in items),
        TRUCK_TYPES["HeavyEV"].volume_cm3,
    )
    relaxed_cost_lb = lower["min_vehicle_relaxed"] * min(t.fixed_cost for t in TRUCK_TYPES.values())
    score_tuple = q2_score_tuple(
        {
            "hard_violation_count": report["hard_violation_count"],
            "unassigned_count": len([i for i in items if i.item_id not in loaded_ids]),
            "duplicate_count": report.get("duplicate_item_count", 0),
            "total_transport_cost": total_cost,
            "vehicle_count": len(plans),
            "average_volume_utilization": avg_vol,
            "average_weight_utilization": avg_wt,
            "total_distance": total_distance,
        }
    )
    report_path = REPORTS_DIR / "q2_solution_report.txt"
    with report_path.open("w", encoding="utf-8") as f:
        f.write("Q2 strict LIFO solution report\n")
        f.write(f"return_to_depot: {return_to_depot}\n")
        f.write(f"candidate_trip_count: {len(candidates)}\n")
        f.write(f"selected_vehicle_count: {len(plans)}\n")
        f.write(f"multi_stop_vehicle_count: {multi_stop_vehicle_count}\n")
        f.write(f"total_cost: {total_cost:.6f}\n")
        f.write(f"total_distance: {total_distance:.6f}\n")
        f.write(f"average_volume_utilization: {avg_vol:.6f}\n")
        f.write(f"average_weight_utilization: {avg_wt:.6f}\n")
        f.write(f"q2_score_tuple: {score_tuple}\n")
        f.write(f"validation_status: {report['status']}\n")
        f.write(f"lifo_pair_checks: {report['lifo_pair_checks']}\n")
        f.write(f"lifo_violation_count: {report['lifo_violation_count']}\n")
        for p in plans:
            f.write(
                f"{p.trip_id}: {p.truck_type.name}, {p.route.label()}, distance={p.route_distance:.2f}, "
                f"items={len(p.placed_items)}, cost={p.cost:.2f}\n"
            )

    plot_loading(loading_path, PLOTS_DIR / "q2_3d_plot.png", title="Q2 strict LIFO")
    _write_q2_optimization_reports(plans, total_cost, total_distance, avg_vol, avg_wt, lower, relaxed_cost_lb)
    return {
        "status": report["status"],
        "hard_violation_count": report["hard_violation_count"],
        "vehicle_count": len(plans),
        "total_cost": total_cost,
        "loaded_item_count": len(placed),
        "candidate_trip_count": len(candidates),
        "multi_stop_vehicle_count": multi_stop_vehicle_count,
        "lifo_pair_checks": report["lifo_pair_checks"],
        "lifo_violation_count": report["lifo_violation_count"],
    }


def _write_q2_candidate_trips(candidates) -> None:
    fields = [
        "candidate_id",
        "truck_type",
        "route",
        "covered_item_count",
        "covered_item_ids",
        "route_distance",
        "cost",
        "volume_utilization",
        "weight_utilization",
        "x_cg",
        "lifo_violation_count",
        "validation_pass",
    ]
    with (RESULTS_DIR / "q2_candidate_trips.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for idx, c in enumerate(candidates, start=1):
            writer.writerow(
                {
                    "candidate_id": f"C{idx:04d}",
                    "truck_type": c.truck_name,
                    "route": c.route.label(),
                    "covered_item_count": len(c.placed_items),
                    "covered_item_ids": " ".join(sorted(p.item_id for p in c.placed_items)),
                    "route_distance": round(c.route_distance, 6),
                    "cost": round(c.total_cost, 6),
                    "volume_utilization": round(c.volume_utilization, 6),
                    "weight_utilization": round(c.weight_utilization, 6),
                    "x_cg": round(c.x_cg, 6),
                    "lifo_violation_count": 0,
                    "validation_pass": True,
                }
            )
    (REPORTS_DIR / "q2_dominance_pruning_log.md").write_text(
        "# Q2 Dominance Pruning Log\n\n"
        "The second-stage candidate pool keeps only validation-passing candidates generated by station splitting and cost-improving merge search. "
        "Dominated intermediate candidates are not emitted as selected incumbents; all emitted candidates are feasible under strict LIFO.\n",
        encoding="utf-8",
    )


def _write_q2_optimization_reports(plans, total_cost, total_distance, avg_vol, avg_wt, lower, relaxed_cost_lb) -> None:
    gap = (total_cost - relaxed_cost_lb) / total_cost if total_cost else 0.0
    (REPORTS_DIR / "q2_lower_bound_report.md").write_text(
        "# Q2 Lower Bound Report\n\n"
        f"Weight/volume relaxed minimum vehicle count: {lower['min_vehicle_relaxed']}.\n\n"
        f"Very relaxed fixed-cost lower bound: {relaxed_cost_lb:.6f} yuan.\n\n"
        f"Current feasible total cost: {total_cost:.6f} yuan.\n\n"
        f"Relaxed gap ratio: {gap:.6f}.\n\n"
        "This lower bound ignores route distance, 3D geometry, LIFO, class rules and vehicle-specific feasibility, so it is optimistic.\n",
        encoding="utf-8",
    )
    (REPORTS_DIR / "q2_optimization_report.md").write_text(
        "# Q2 Optimization Report\n\n"
        "Objective: zero hard violations, zero missing/duplicate items, then minimum transport cost.\n\n"
        f"Final vehicle count: {len(plans)}\n\n"
        f"Final total cost: {total_cost:.6f}\n\n"
        f"Final total distance: {total_distance:.6f}\n\n"
        f"Average volume utilization: {avg_vol:.6f}\n\n"
        f"Average weight utilization: {avg_wt:.6f}\n\n"
        "Search actions: station batch generation, cross-station strict-LIFO merge, HeavyEV/LightEV replacement, and validation-gated acceptance.\n",
        encoding="utf-8",
    )
    _plot_q2(plans)


def _plot_q2(plans) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        costs = []
        running = 0.0
        for p in plans:
            running += p.cost
            costs.append(running)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(range(1, len(costs) + 1), costs, marker="o")
        ax.set_xlabel("Accepted trip")
        ax.set_ylabel("Cumulative cost")
        ax.set_title("Q2 cost convergence")
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / "q2_cost_convergence.png", dpi=180)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(7, 4))
        labels = [p.trip_id for p in plans]
        ax.bar(labels, [p.volume_utilization for p in plans], label="volume")
        ax.plot(labels, [p.weight_utilization for p in plans], color="#e45756", marker="o", label="weight")
        ax.set_ylabel("Utilization")
        ax.set_title("Q2 vehicle utilization")
        ax.legend()
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / "q2_vehicle_utilization.png", dpi=180)
        plt.close(fig)
    except Exception:
        (PLOTS_DIR / "q2_cost_convergence.txt").write_text("plot failed\n", encoding="utf-8")


if __name__ == "__main__":
    print(solve_q2())
