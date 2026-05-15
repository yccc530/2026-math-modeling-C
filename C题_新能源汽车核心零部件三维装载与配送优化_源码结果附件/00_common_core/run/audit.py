# -*- coding: utf-8 -*-
"""Final project audit for data, constraints, output files and report risk."""

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
from pathlib import Path
from typing import Dict, List

from data_config import (
    BASE_DISTANCE_MATRIX,
    REPORTS_DIR,
    RESULTS_DIR,
    PLOTS_DIR,
    SCENARIO_A_TYPES,
    SCENARIO_B_TYPES,
    TRUCK_TYPES,
    ensure_directories,
)


REQUIRED_FILES = [
    "results/result_q1_loading.csv",
    "results/result_q1_summary.csv",
    "results/result_q1_unloaded.csv",
    "results/result_q2_trips.csv",
    "results/result_q2_loading.csv",
    "results/result_q2_unassigned.csv",
    "results/generated_cargo_q3.csv",
    "results/generated_distance_matrix.csv",
    "results/result_q3_comparison.csv",
    "results/result_q3_trips_strict.csv",
    "results/result_q3_trips_flexible.csv",
    "results/result_q3_loading_strict.csv",
    "results/result_q3_loading_flexible.csv",
    "results/sensitivity_q3.csv",
    "plots/q1_3d_plot.png",
    "plots/q2_3d_plot.png",
    "plots/q3_comparison_plot.png",
    "plots/q3_sensitivity_plot.png",
    "reports/validation_report_q1.json",
    "reports/validation_report_q1.txt",
    "reports/validation_report_q2.json",
    "reports/validation_report_q2.txt",
    "reports/validation_report_q3_strict.json",
    "reports/validation_report_q3_strict.txt",
    "reports/validation_report_q3_flexible.json",
    "reports/validation_report_q3_flexible.txt",
    "reports/validation_report_q3_block.json",
    "reports/validation_report_q3_block.txt",
    "reports/q2_solution_report.txt",
    "reports/technical_report_draft.md",
]


def _load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _check_q3_ranges(issues: List[str]) -> None:
    rows = _read_csv(RESULTS_DIR / "generated_cargo_q3.csv")
    if not rows:
        issues.append("Q3 generated cargo CSV is empty or missing.")
        return
    stations = set()
    for r in rows:
        length = float(r["length"])
        width = float(r["width"])
        height = float(r["height"])
        weight = float(r["weight"])
        qty = int(float(r["quantity"]))
        category = r["category"]
        stations.add(r["destination"])
        if not (40 <= length <= 120 and 40 <= width <= 80 and 40 <= height <= 60 and 25 <= weight <= 350):
            issues.append(f"Q3 cargo range violation: {r}")
        if category not in {"I", "II", "III", "IV", "V"}:
            issues.append(f"Q3 cargo category violation: {r}")
        if qty <= 0:
            issues.append(f"Q3 cargo quantity violation: {r}")
    missing = {f"S{i}" for i in range(1, 9)} - stations
    if missing:
        issues.append(f"Q3 stations without cargo: {sorted(missing)}")


def _check_distance_matrix(issues: List[str]) -> None:
    path = RESULTS_DIR / "generated_distance_matrix.csv"
    rows = _read_csv(path)
    if not rows:
        issues.append("Generated distance matrix is missing.")
        return
    header_nodes = list(rows[0].keys())[1:]
    matrix = {}
    for row in rows:
        a = row["from_to"]
        for b in header_nodes:
            matrix[(a, b)] = float(row[b])
    for edge, expected in BASE_DISTANCE_MATRIX.items():
        if abs(matrix.get(edge, -1) - expected) > 1e-6:
            issues.append(f"Fixed distance {edge} changed: {matrix.get(edge)} vs {expected}")
        rev = (edge[1], edge[0])
        if abs(matrix.get(rev, -1) - expected) > 1e-6:
            issues.append(f"Fixed reverse distance {rev} changed: {matrix.get(rev)} vs {expected}")
    for i in range(1, 9):
        d = matrix.get(("Depot", f"S{i}"), -1)
        if not (15 <= d <= 150):
            issues.append(f"Depot distance out of range for S{i}: {d}")


def audit_project() -> Dict[str, object]:
    ensure_directories()
    root = Path(__file__).resolve().parent
    issues: List[str] = []
    warnings: List[str] = []

    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.exists():
            issues.append(f"Missing required file: {rel}")
        elif path.suffix.lower() == ".png" and path.stat().st_size < 100:
            issues.append(f"Plot appears empty: {rel}")

    for truck_name, truck in TRUCK_TYPES.items():
        if truck.length <= 0 or truck.width <= 0 or truck.height <= 0 or truck.max_payload <= 0:
            issues.append(f"Invalid truck parameters for {truck_name}")
    if len(SCENARIO_A_TYPES) != 5 or len(SCENARIO_B_TYPES) != 7:
        issues.append("Scenario A/B cargo type counts do not match the statement.")

    _check_q3_ranges(issues)
    _check_distance_matrix(issues)

    for name in ["q1", "q2", "q3_strict", "q3_block", "q3_flexible"]:
        report = _load_json(REPORTS_DIR / f"validation_report_{name}.json")
        if not report:
            issues.append(f"Missing validation report for {name}")
            continue
        if report.get("hard_violation_count") != 0:
            issues.append(f"Validation hard violations remain in {name}: {report.get('hard_violation_count')}")
        if report.get("status") != "PASS":
            issues.append(f"Validation status is not PASS in {name}: {report.get('status')}")

    flex = _load_json(REPORTS_DIR / "validation_report_q3_flexible.json")
    if flex and float(flex.get("relocation_volume_ratio", 0.0)) > 0.15 + 1e-9:
        issues.append("Q3 flexible relocation volume ratio exceeds 15%.")

    report_text = (REPORTS_DIR / "technical_report_draft.md").read_text(encoding="utf-8", errors="ignore") if (REPORTS_DIR / "technical_report_draft.md").exists() else ""
    if "全局最优" in report_text and "当前最优可行方案" not in report_text:
        issues.append("技术报告存在最优性表述与算法性质不一致的风险。")
    if "return_to_depot" not in report_text:
        issues.append("技术报告未说明 return_to_depot 假设。")
    if "启发式" not in report_text:
        warnings.append("技术报告应明确说明启发式算法局限。")

    status = "PASS" if not issues else "FAIL"
    audit_md = REPORTS_DIR / "audit_report.md"
    bug_md = REPORTS_DIR / "bug_list.md"
    fix_md = REPORTS_DIR / "fix_plan.md"
    audit_lines = [f"# 审计报告\n\n审计状态：{'通过' if status == 'PASS' else '未通过'}。\n"]
    if issues:
        audit_lines.append("## 待解决问题\n")
        audit_lines.extend(f"- {issue}\n" for issue in issues)
    else:
        audit_lines.append("\n所有硬约束、必需文件和验证报告均通过项目审计。\n")
    if warnings:
        audit_lines.append("\n## 风险提示\n")
        audit_lines.extend(f"- {w}\n" for w in warnings)
    audit_md.write_text("".join(audit_lines), encoding="utf-8-sig")

    if issues:
        bug_md.write_text("# 问题清单\n\n" + "".join(f"- {issue}\n" for issue in issues), encoding="utf-8-sig")
        fix_md.write_text(
            "# 修复计划\n\n"
            "1. 重新运行 `python main.py` 以生成失败的结果文件。\n"
            "2. 检查验证报告 JSON，定位具体货物级违规。\n"
            "3. 若问题仍存在，减少路线聚类规模或拆分超载站点组。\n",
            encoding="utf-8-sig",
        )
    else:
        bug_md.write_text("# 问题清单\n\n未发现尚未解决的问题。\n", encoding="utf-8-sig")
        fix_md.write_text("# 修复计划\n\n当前审计未发现需要自动修复的问题，因此无需生成额外修复步骤。\n", encoding="utf-8-sig")

    return {"status": status, "issues": issues, "warnings": warnings}


if __name__ == "__main__":
    print(audit_project())
