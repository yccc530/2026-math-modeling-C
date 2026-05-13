# -*- coding: utf-8 -*-
"""Synchronize runtime outputs into the per-question submission folders.

The solver modules write to root-level ``results/``, ``plots/`` and
``reports/`` directories during execution. The organized submission layout keeps
final artifacts beside the corresponding problem, so this script copies known
output files into their designated folders after a run.
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

import shutil
from pathlib import Path

from bootstrap_paths import configure_paths


ROOT = configure_paths(__file__)


MAPPINGS = [
    ("results/result_q1_loading.csv", "01_Q1_single_vehicle/results"),
    ("results/result_q1_summary.csv", "01_Q1_single_vehicle/results"),
    ("results/result_q1_unloaded.csv", "01_Q1_single_vehicle/results"),
    ("results/q1_best_solutions.csv", "01_Q1_single_vehicle/results"),
    ("plots/q1_3d_plot.png", "01_Q1_single_vehicle/plots"),
    ("plots/q1_pareto_front.png", "01_Q1_single_vehicle/plots"),
    ("reports/validation_report_q1.json", "01_Q1_single_vehicle/reports"),
    ("reports/validation_report_q1.txt", "01_Q1_single_vehicle/reports"),
    ("reports/q1_optimization_report.md", "01_Q1_single_vehicle/reports"),
    ("results/result_q2_loading.csv", "02_Q2_multi_vehicle_lifo/results"),
    ("results/result_q2_trips.csv", "02_Q2_multi_vehicle_lifo/results"),
    ("results/result_q2_unassigned.csv", "02_Q2_multi_vehicle_lifo/results"),
    ("results/q2_candidate_trips.csv", "02_Q2_multi_vehicle_lifo/results"),
    ("results/q2_selected_trips.csv", "02_Q2_multi_vehicle_lifo/results"),
    ("plots/q2_3d_plot.png", "02_Q2_multi_vehicle_lifo/plots"),
    ("plots/q2_cost_convergence.png", "02_Q2_multi_vehicle_lifo/plots"),
    ("plots/q2_vehicle_utilization.png", "02_Q2_multi_vehicle_lifo/plots"),
    ("reports/validation_report_q2.json", "02_Q2_multi_vehicle_lifo/reports"),
    ("reports/validation_report_q2.txt", "02_Q2_multi_vehicle_lifo/reports"),
    ("reports/q2_solution_report.txt", "02_Q2_multi_vehicle_lifo/reports"),
    ("reports/q2_optimization_report.md", "02_Q2_multi_vehicle_lifo/reports"),
    ("reports/q2_lower_bound_report.md", "02_Q2_multi_vehicle_lifo/reports"),
    ("reports/q2_dominance_pruning_log.md", "02_Q2_multi_vehicle_lifo/reports"),
    ("results/generated_cargo_q3.csv", "03_Q3_block_flexible/data"),
    ("results/generated_distance_matrix.csv", "03_Q3_block_flexible/data"),
    ("results/q3_dataset_candidates.csv", "03_Q3_block_flexible/data"),
    ("results/result_q3_comparison.csv", "03_Q3_block_flexible/results"),
    ("results/result_q3_loading_strict.csv", "03_Q3_block_flexible/results"),
    ("results/result_q3_loading_block.csv", "03_Q3_block_flexible/results"),
    ("results/result_q3_loading_flexible.csv", "03_Q3_block_flexible/results"),
    ("results/result_q3_trips_strict.csv", "03_Q3_block_flexible/results"),
    ("results/result_q3_trips_block.csv", "03_Q3_block_flexible/results"),
    ("results/result_q3_trips_flexible.csv", "03_Q3_block_flexible/results"),
    ("results/q3_best_strict.csv", "03_Q3_block_flexible/results"),
    ("results/q3_best_block.csv", "03_Q3_block_flexible/results"),
    ("results/q3_best_flexible.csv", "03_Q3_block_flexible/results"),
    ("results/q3_strategy_grid_search.csv", "03_Q3_block_flexible/results"),
    ("results/q3_pareto_solutions.csv", "03_Q3_block_flexible/results"),
    ("results/sensitivity_q3.csv", "03_Q3_block_flexible/results"),
    ("plots/q3_comparison_plot.png", "03_Q3_block_flexible/plots"),
    ("plots/q3_flexible_3d_plot.png", "03_Q3_block_flexible/plots"),
    ("plots/q3_pareto_front.png", "03_Q3_block_flexible/plots"),
    ("plots/q3_sensitivity_heatmap.png", "03_Q3_block_flexible/plots"),
    ("plots/q3_sensitivity_plot.png", "03_Q3_block_flexible/plots"),
    ("plots/q3_strategy_cost_boxplot.png", "03_Q3_block_flexible/plots"),
    ("reports/validation_report_q3_strict.json", "03_Q3_block_flexible/reports"),
    ("reports/validation_report_q3_strict.txt", "03_Q3_block_flexible/reports"),
    ("reports/validation_report_q3_block.json", "03_Q3_block_flexible/reports"),
    ("reports/validation_report_q3_block.txt", "03_Q3_block_flexible/reports"),
    ("reports/validation_report_q3_flexible.json", "03_Q3_block_flexible/reports"),
    ("reports/validation_report_q3_flexible.txt", "03_Q3_block_flexible/reports"),
    ("reports/q3_dataset_audit.md", "03_Q3_block_flexible/reports"),
    ("reports/q3_strategy_optimization_report.md", "03_Q3_block_flexible/reports"),
    ("reports/q3_fair_comparison_report.md", "03_Q3_block_flexible/reports"),
    ("results/optimization_dashboard.csv", "04_Q4_validation_audit/results"),
    ("results/final_metrics.csv", "04_Q4_validation_audit/results"),
    ("reports/validator_adversarial_report.md", "04_Q4_validation_audit/reports"),
    ("reports/validator_adversarial_stdout.txt", "04_Q4_validation_audit/reports"),
    ("reports/result_traceability_table.csv", "04_Q4_validation_audit/reports"),
    ("reports/paper_risk_audit.md", "04_Q4_validation_audit/reports"),
    ("reports/audit_report.md", "04_Q4_validation_audit/reports"),
    ("reports/bug_list.md", "04_Q4_validation_audit/reports"),
    ("reports/fix_plan.md", "04_Q4_validation_audit/reports"),
    ("reports/final_optimality_gap_report.md", "04_Q4_validation_audit/reports"),
    ("reports/final_submission_checklist.md", "04_Q4_validation_audit/reports"),
    ("reports/optimization_dashboard.md", "04_Q4_validation_audit/reports"),
    ("reports/technical_report_draft.md", "05_final_report_and_submission/reports"),
    ("reports/technical_report_final.md", "05_final_report_and_submission/reports"),
    ("reports/second_stage_optimization_summary.md", "05_final_report_and_submission/reports"),
    ("reports/algorithm_improvement_notes.md", "05_final_report_and_submission/reports"),
]


def sync_outputs() -> None:
    """Copy every available runtime artifact listed in ``MAPPINGS``."""
    for source_rel, dest_rel in MAPPINGS:
        source = ROOT / source_rel
        if not source.exists():
            continue
        dest_dir = ROOT / dest_rel
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest_dir / source.name)


if __name__ == "__main__":
    sync_outputs()
    print("Outputs synchronized into per-question folders.")

