# -*- coding: utf-8 -*-
"""Second-stage optimization runner.

This runner records a baseline, runs the enhanced solvers/reports/tests, and
records the final incumbent in the optimization dashboard.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from audit import audit_project
from data_config import REPORTS_DIR, RESULTS_DIR, ensure_directories
from main import run_all
from optimization_dashboard import record_dashboard
from q1_objective import q1_upper_bounds
from report_generator import generate_report
from second_stage_reports import package_submission, write_final_reports


def run_adversarial_tests() -> bool:
    result = subprocess.run([sys.executable, "tests/test_validator_adversarial.py"], cwd=Path(__file__).resolve().parent, text=True, capture_output=True)
    (REPORTS_DIR / "validator_adversarial_stdout.txt").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    return result.returncode == 0


def write_summary(baseline, final_row, tests_passed: bool) -> None:
    lines = [
        "# Second Stage Optimization Summary\n\n",
        "## Baseline And Final\n\n",
        f"- Baseline dashboard iteration: {baseline['iteration']}\n",
        f"- Final dashboard iteration: {final_row['iteration']}\n",
        f"- Validator adversarial tests: {'PASS' if tests_passed else 'FAIL'}\n\n",
        "## Algorithms Used\n\n",
        "Q1 used extreme/corner-point packing with multiple sort orders, then upgraded from weighted-score selection to lexicographic selection: loaded count, volume, weight, CG offset and safety margins.\n\n",
        "Q2 used route enumeration, validation-gated candidate trips, station batching, strict-LIFO cross-station merge, HeavyEV/LightEV replacement, dominance logging and a relaxed lower-bound estimate.\n\n",
        "Q3 used strict LIFO, block loading, and flexible/block LIFO strategies; sensitivity and Pareto artifacts were generated from the evaluated incumbents.\n\n",
        "Q4 used adversarial validator tests and result traceability checks.\n\n",
        "## Final Incumbents\n\n",
        f"- Q1 loaded_count: {final_row['q1_loaded_count']}, volume_utilization: {final_row['q1_volume_utilization']}, weight_utilization: {final_row['q1_weight_utilization']}.\n",
        f"- Q2 vehicle_count: {final_row['q2_vehicle_count']}, total_cost: {final_row['q2_total_transport_cost']}, LIFO violations: {final_row['q2_lifo_violation_count']}.\n",
        f"- Q3 strict cost: {final_row['q3_strict_total_cost']}, flexible cost: {final_row['q3_flexible_total_cost']}, saving ratio: {final_row['q3_flexible_cost_saving_ratio']}.\n\n",
        "## Limitations\n\n",
        "The project uses heuristic search and relaxed bounds. It cannot honestly claim a global optimum. The result is the current best feasible incumbent found under multi-strategy search and validation.\n",
    ]
    (REPORTS_DIR / "second_stage_optimization_summary.md").write_text("".join(lines), encoding="utf-8")


def main() -> int:
    ensure_directories()
    run_all(max_iterations=1)
    generate_report()
    audit_project()
    baseline = record_dashboard(0, "baseline", "first-stage incumbent", best_so_far=True, notes="baseline before second-stage artifacts")

    result = run_all(max_iterations=1)
    generate_report()
    audit = audit_project()
    tests_passed = run_adversarial_tests()
    write_final_reports()
    audit = audit_project()
    final_row = record_dashboard(
        1,
        "q1/q2/q3/q4",
        "lexicographic Q1 + candidate Q2 + strict/block/flexible Q3 + adversarial Q4",
        best_so_far=bool(audit.get("status") == "PASS" and tests_passed),
        rollback_triggered=False,
        notes="second-stage enhanced incumbent",
    )
    write_summary(baseline, final_row, tests_passed)
    package_submission()
    status = "PASS" if audit.get("status") == "PASS" and tests_passed else "FAIL"
    q1_bounds = q1_upper_bounds()
    q1_count_gap = int(q1_bounds["relaxed_count_upper"]) - int(final_row["q1_loaded_count"])
    q2_relaxed_lb = 1200.0
    q2_gap = (float(final_row["q2_total_transport_cost"]) - q2_relaxed_lb) / float(final_row["q2_total_transport_cost"])
    strict_cost = float(final_row["q3_strict_total_cost"])
    flex_cost = float(final_row["q3_flexible_total_cost"])
    print(f"SECOND STAGE OPTIMIZATION RESULT: {status}")
    print()
    print("Q1:")
    print("baseline -> final")
    print(f"loaded_count: {baseline['q1_loaded_count']} -> {final_row['q1_loaded_count']}")
    print(f"volume_utilization: {baseline['q1_volume_utilization']} -> {final_row['q1_volume_utilization']}")
    print(f"weight_utilization: {baseline['q1_weight_utilization']} -> {final_row['q1_weight_utilization']}")
    print(f"x_cg: {baseline['q1_xcg']} -> {final_row['q1_xcg']}")
    print(f"gap_to_upper_bound: relaxed_count_gap={q1_count_gap}, see reports/q1_optimization_report.md")
    print()
    print("Q2:")
    print("baseline -> final")
    print(f"vehicle_count: {baseline['q2_vehicle_count']} -> {final_row['q2_vehicle_count']}")
    print(f"total_cost: {baseline['q2_total_transport_cost']} -> {final_row['q2_total_transport_cost']}")
    print(f"total_distance: {baseline['q2_total_distance']} -> {final_row['q2_total_distance']}")
    print(f"average_utilization: volume={final_row['q2_average_volume_utilization']}, weight={final_row['q2_average_weight_utilization']}")
    print(f"gap_to_lower_bound: relaxed_fixed_cost_gap_ratio={q2_gap:.6f}, see reports/q2_lower_bound_report.md")
    print(f"LIFO violations: {final_row['q2_lifo_violation_count']}")
    print()
    print("Q3:")
    print("strict/block/flexible final comparison")
    print(f"vehicle_count: strict={final_row['q3_strict_vehicle_count']}, flexible={final_row['q3_flexible_vehicle_count']}")
    print(f"transport_cost: strict={final_row['q3_strict_total_cost']}, flexible={final_row['q3_flexible_transport_cost']}")
    print(f"relocation_penalty: {final_row['q3_flexible_penalty']}")
    print(f"total_cost: strict={final_row['q3_strict_total_cost']}, flexible={final_row['q3_flexible_total_cost']}")
    print(f"saving_ratio: {(strict_cost - flex_cost) / strict_cost:.6f}")
    print(f"relocation_ratio: {final_row['q3_flexible_relocation_ratio']}")
    print()
    print("Q4:")
    print(f"validator tests: {'PASS' if tests_passed else 'FAIL'}")
    print("traceability: reports/result_traceability_table.csv")
    print("paper risk: reports/paper_risk_audit.md")
    print(f"audit: {audit.get('status')}")
    print()
    print("Remaining limitations:")
    print("- Heuristic search only; no global optimality proof.")
    print("- Lower/upper bounds are relaxed and optimistic.")
    print("- More time could be spent on MILP/CP-SAT column generation for stronger Q2/Q3 optimality gaps.")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
