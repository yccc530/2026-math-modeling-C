# -*- coding: utf-8 -*-
"""Read outputs and append a second-stage optimization dashboard row."""

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

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from data_config import RESULTS_DIR, REPORTS_DIR, TRUCK_TYPES, ensure_directories


DASHBOARD_FIELDS = [
    "iteration",
    "timestamp",
    "changed_module",
    "changed_strategy",
    "q1_loaded_count",
    "q1_loaded_volume",
    "q1_volume_utilization",
    "q1_loaded_weight",
    "q1_weight_utilization",
    "q1_xcg",
    "q1_cg_margin",
    "q1_score",
    "q1_hard_violation_count",
    "q2_vehicle_count",
    "q2_heavy_count",
    "q2_light_count",
    "q2_total_distance",
    "q2_total_transport_cost",
    "q2_average_volume_utilization",
    "q2_average_weight_utilization",
    "q2_unassigned_count",
    "q2_duplicate_count",
    "q2_lifo_violation_count",
    "q2_hard_violation_count",
    "q2_score",
    "q3_strict_vehicle_count",
    "q3_strict_total_cost",
    "q3_strict_average_volume_utilization",
    "q3_strict_average_weight_utilization",
    "q3_flexible_vehicle_count",
    "q3_flexible_transport_cost",
    "q3_flexible_relocation_count",
    "q3_flexible_relocation_volume",
    "q3_flexible_relocation_ratio",
    "q3_flexible_penalty",
    "q3_flexible_total_cost",
    "q3_flexible_cost_saving_ratio",
    "q3_flexible_vehicle_saving",
    "q3_hard_violation_count",
    "q3_score",
    "audit_pass",
    "best_so_far",
    "rollback_triggered",
    "notes",
]


def _rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _json(path: Path) -> Dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def collect_metrics(iteration: int, changed_module: str, changed_strategy: str, notes: str = "", best_so_far: bool = False, rollback_triggered: bool = False) -> Dict[str, object]:
    ensure_directories()
    q1 = (_rows(RESULTS_DIR / "result_q1_summary.csv") or [{}])[0]
    q2 = _rows(RESULTS_DIR / "result_q2_trips.csv")
    q3 = _rows(RESULTS_DIR / "result_q3_comparison.csv")
    q3_by = {r.get("strategy", ""): r for r in q3}
    v1 = _json(REPORTS_DIR / "validation_report_q1.json")
    v2 = _json(REPORTS_DIR / "validation_report_q2.json")
    v3s = _json(REPORTS_DIR / "validation_report_q3_strict.json")
    v3f = _json(REPORTS_DIR / "validation_report_q3_flexible.json")
    audit_text = (REPORTS_DIR / "audit_report.md").read_text(encoding="utf-8", errors="ignore") if (REPORTS_DIR / "audit_report.md").exists() else ""

    def f(row, key):
        try:
            return float(row.get(key, 0) or 0)
        except Exception:
            return 0.0

    q2_heavy = sum(1 for r in q2 if r.get("truck_type") == "HeavyEV")
    q2_light = sum(1 for r in q2 if r.get("truck_type") == "LightEV")
    q2_cost = sum(f(r, "total_cost") for r in q2)
    q2_distance = sum(f(r, "route_distance") for r in q2)
    q2_vol = sum(f(r, "volume_utilization") for r in q2) / max(1, len(q2))
    q2_wt = sum(f(r, "weight_utilization") for r in q2) / max(1, len(q2))
    strict = q3_by.get("strict", {})
    flex = q3_by.get("flexible", {})
    strict_cost = f(strict, "total_cost")
    flex_total = f(flex, "total_cost")
    row = {
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "changed_module": changed_module,
        "changed_strategy": changed_strategy,
        "q1_loaded_count": q1.get("loaded_item_count", 0),
        "q1_loaded_volume": q1.get("load_volume_m3", 0),
        "q1_volume_utilization": q1.get("volume_utilization", 0),
        "q1_loaded_weight": q1.get("load_weight", 0),
        "q1_weight_utilization": q1.get("weight_utilization", 0),
        "q1_xcg": q1.get("x_cg", 0),
        "q1_cg_margin": q1.get("cg_margin", 0),
        "q1_score": q1.get("score", 0),
        "q1_hard_violation_count": v1.get("hard_violation_count", 0),
        "q2_vehicle_count": len(q2),
        "q2_heavy_count": q2_heavy,
        "q2_light_count": q2_light,
        "q2_total_distance": round(q2_distance, 6),
        "q2_total_transport_cost": round(q2_cost, 6),
        "q2_average_volume_utilization": round(q2_vol, 6),
        "q2_average_weight_utilization": round(q2_wt, 6),
        "q2_unassigned_count": sum(1 for _ in _rows(RESULTS_DIR / "result_q2_unassigned.csv")),
        "q2_duplicate_count": v2.get("duplicate_item_count", 0),
        "q2_lifo_violation_count": v2.get("lifo_violation_count", 0),
        "q2_hard_violation_count": v2.get("hard_violation_count", 0),
        "q2_score": round(-q2_cost, 6),
        "q3_strict_vehicle_count": strict.get("vehicle_count", 0),
        "q3_strict_total_cost": strict.get("total_cost", 0),
        "q3_strict_average_volume_utilization": strict.get("mean_volume_utilization", 0),
        "q3_strict_average_weight_utilization": strict.get("mean_weight_utilization", 0),
        "q3_flexible_vehicle_count": flex.get("vehicle_count", 0),
        "q3_flexible_transport_cost": flex.get("transport_cost", 0),
        "q3_flexible_relocation_count": flex.get("relocation_count", 0),
        "q3_flexible_relocation_volume": flex.get("relocation_volume_m3", 0),
        "q3_flexible_relocation_ratio": flex.get("relocation_volume_ratio", 0),
        "q3_flexible_penalty": flex.get("penalty_cost", 0),
        "q3_flexible_total_cost": flex.get("total_cost", 0),
        "q3_flexible_cost_saving_ratio": round((strict_cost - flex_total) / strict_cost, 6) if strict_cost else 0,
        "q3_flexible_vehicle_saving": int(float(strict.get("vehicle_count", 0) or 0) - float(flex.get("vehicle_count", 0) or 0)),
        "q3_hard_violation_count": int(v3s.get("hard_violation_count", 0)) + int(v3f.get("hard_violation_count", 0)),
        "q3_score": round(-flex_total, 6),
        "audit_pass": "Status: PASS" in audit_text,
        "best_so_far": best_so_far,
        "rollback_triggered": rollback_triggered,
        "notes": notes,
    }
    return row


def append_dashboard(row: Dict[str, object]) -> None:
    path = RESULTS_DIR / "optimization_dashboard.csv"
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=DASHBOARD_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in DASHBOARD_FIELDS})
    md = REPORTS_DIR / "optimization_dashboard.md"
    rows = _rows(path)
    lines = [
        "# 优化仪表盘\n\n",
        "| 轮次 | 模块 | 策略 | Q1 装入件数 | Q2 成本 | Q3 柔性成本 | 审计通过 | 是否最优可行解 | 备注 |\n",
        "|---:|---|---|---:|---:|---:|---|---|---|\n",
    ]
    for r in rows:
        audit_text = "是" if str(r.get("audit_pass")).lower() == "true" else "否"
        best_text = "是" if str(r.get("best_so_far")).lower() == "true" else "否"
        lines.append(
            f"|{r.get('iteration')}|{r.get('changed_module')}|{r.get('changed_strategy')}|{r.get('q1_loaded_count')}|"
            f"{r.get('q2_total_transport_cost')}|{r.get('q3_flexible_total_cost')}|{audit_text}|{best_text}|{r.get('notes')}|\n"
        )
    md.write_text("".join(lines), encoding="utf-8-sig")


def record_dashboard(iteration: int, changed_module: str, changed_strategy: str, notes: str = "", best_so_far: bool = False, rollback_triggered: bool = False) -> Dict[str, object]:
    row = collect_metrics(iteration, changed_module, changed_strategy, notes, best_so_far, rollback_triggered)
    append_dashboard(row)
    return row

