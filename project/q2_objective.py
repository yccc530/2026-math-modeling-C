# -*- coding: utf-8 -*-
"""Objective helpers for Q2."""

from __future__ import annotations

from typing import Sequence


def q2_score_tuple(metrics: dict) -> tuple:
    return (
        -int(metrics.get("hard_violation_count", 10**9)),
        -int(metrics.get("unassigned_count", 10**9)),
        -int(metrics.get("duplicate_count", 10**9)),
        -float(metrics.get("total_transport_cost", 10**18)),
        -int(metrics.get("vehicle_count", 10**9)),
        float(metrics.get("average_volume_utilization", 0.0)),
        float(metrics.get("average_weight_utilization", 0.0)),
        -float(metrics.get("total_distance", 10**18)),
    )


def q2_lower_bounds(total_weight: float, total_volume_cm3: float, heavy_volume_cm3: float) -> dict:
    # Cost lower bounds are deliberately relaxed and therefore optimistic.
    min_heavy_by_weight = int((total_weight + 12000 - 1) // 12000)
    min_heavy_by_volume = int((total_volume_cm3 + heavy_volume_cm3 - 1) // heavy_volume_cm3)
    return {
        "min_vehicle_by_weight": min_heavy_by_weight,
        "min_vehicle_by_volume": min_heavy_by_volume,
        "min_vehicle_relaxed": max(min_heavy_by_weight, min_heavy_by_volume),
    }

