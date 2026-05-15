# -*- coding: utf-8 -*-
"""Objective helpers for Q3 strategy comparison."""

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


def q3_score_tuple(metrics: dict) -> tuple:
    relocation_ratio = float(metrics.get("relocation_ratio", 0.0))
    return (
        -int(metrics.get("hard_violation_count", 10**9)),
        -int(metrics.get("unassigned_count", 10**9)),
        -int(metrics.get("duplicate_count", 10**9)),
        -max(0.0, relocation_ratio - 0.15),
        -float(metrics.get("total_cost_with_penalty", 10**18)),
        -int(metrics.get("vehicle_count", 10**9)),
        float(metrics.get("average_volume_utilization", 0.0)),
        float(metrics.get("average_weight_utilization", 0.0)),
        float(metrics.get("cost_saving_ratio_vs_strict", 0.0)),
        float(metrics.get("vehicle_saving_vs_strict", 0.0)),
    )

