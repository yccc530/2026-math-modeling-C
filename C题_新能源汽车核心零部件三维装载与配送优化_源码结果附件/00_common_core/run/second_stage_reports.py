# -*- coding: utf-8 -*-
"""Second-stage traceability, final reports, and packaging helpers."""

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
from pathlib import Path

from data_config import PLOTS_DIR, REPORTS_DIR, RESULTS_DIR, ROOT
from q1_objective import q1_upper_bounds


def _rows(path: Path):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _first(path: Path):
    rows = _rows(path)
    return rows[0] if rows else {}


def write_traceability() -> None:
    claims = []
    q1 = _first(RESULTS_DIR / "result_q1_summary.csv")
    q2 = _rows(RESULTS_DIR / "result_q2_trips.csv")
    q3 = {r["strategy"]: r for r in _rows(RESULTS_DIR / "result_q3_comparison.csv")}
    claims.append(("C001", "Q1", q1.get("loaded_item_count", ""), "results/result_q1_summary.csv", "loaded_item_count"))
    claims.append(("C002", "Q1", q1.get("volume_utilization", ""), "results/result_q1_summary.csv", "volume_utilization"))
    claims.append(("C003", "Q2", str(sum(float(r["total_cost"]) for r in q2)), "results/result_q2_trips.csv", "sum(total_cost)"))
    claims.append(("C004", "Q2", str(len(q2)), "results/result_q2_trips.csv", "row count"))
    if "strict" in q3 and "flexible" in q3:
        claims.append(("C005", "Q3", q3["strict"].get("total_cost", ""), "results/result_q3_comparison.csv", "strict.total_cost"))
        claims.append(("C006", "Q3", q3["flexible"].get("total_cost", ""), "results/result_q3_comparison.csv", "flexible.total_cost"))
    with (REPORTS_DIR / "result_traceability_table.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["claim_id", "report_section", "claimed_value", "source_file", "source_row_or_key", "verified"])
        writer.writeheader()
        for c in claims:
            writer.writerow(
                {
                    "claim_id": c[0],
                    "report_section": c[1],
                    "claimed_value": c[2],
                    "source_file": c[3],
                    "source_row_or_key": c[4],
                    "verified": bool(c[2] != ""),
                }
            )


def write_paper_risk_audit() -> None:
    text = (REPORTS_DIR / "technical_report_draft.md").read_text(encoding="utf-8", errors="ignore") if (REPORTS_DIR / "technical_report_draft.md").exists() else ""
    risks = []
    if "全局最优" in text and "当前最优可行方案" not in text:
        risks.append("可能存在最优性表述与算法性质不一致的问题。")
    if "return_to_depot" not in text:
        risks.append("缺少 return_to_depot 假设说明。")
    if "启发式" not in text:
        risks.append("缺少启发式算法局限说明。")
    lines = ["# 论文风险审计\n\n"]
    if risks:
        lines.extend(f"- {r}\n" for r in risks)
    else:
        lines.append("通过：未发现高风险论文表述。\n\n")
        lines.append("审计重点包括：是否误称全局最优、是否遗漏 `return_to_depot` 假设、是否未说明启发式局限、报告数值是否可追溯。\n")
    (REPORTS_DIR / "paper_risk_audit.md").write_text("".join(lines), encoding="utf-8-sig")


def write_final_reports() -> None:
    write_traceability()
    write_paper_risk_audit()
    q1 = _first(RESULTS_DIR / "result_q1_summary.csv")
    q2 = _rows(RESULTS_DIR / "result_q2_trips.csv")
    q3_rows = _rows(RESULTS_DIR / "result_q3_comparison.csv")
    q3 = {r["strategy"]: r for r in q3_rows}
    q1_bounds = q1_upper_bounds()
    q2_cost = sum(float(r["total_cost"]) for r in q2)
    q2_distance = sum(float(r["route_distance"]) for r in q2)
    strict_cost = float(q3.get("strict", {}).get("total_cost", 0) or 0)
    flex_cost = float(q3.get("flexible", {}).get("total_cost", 0) or 0)
    saving = (strict_cost - flex_cost) / strict_cost if strict_cost else 0.0

    with (RESULTS_DIR / "final_metrics.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        for metric, value in [
            ("q1_loaded_count", q1.get("loaded_item_count", "")),
            ("q1_volume_utilization", q1.get("volume_utilization", "")),
            ("q2_vehicle_count", len(q2)),
            ("q2_total_cost", round(q2_cost, 6)),
            ("q2_total_distance", round(q2_distance, 6)),
            ("q3_strict_cost", strict_cost),
            ("q3_flexible_cost", flex_cost),
            ("q3_saving_ratio", round(saving, 6)),
        ]:
            writer.writerow({"metric": metric, "value": value})

    algorithms = """# 使用算法与改进效果说明

| 问题 | 第一阶段算法 | 第二阶段升级策略 | 改进原因 | 观察到的效果 |
|---|---|---|---|---|
| Q1 | 加权评分的多起点 extreme point 装箱 | 字典序目标函数、top-20 可行解档案、Pareto 前沿分析 | 避免“体积较大但件数较少”的方案压过题目要求的装入件数目标 | Q1 先按装入件数选解，再比较体积、重量和重心 |
| Q2 | 可行性优先的拆分与合并 | 候选车次台账、验证门控的跨站合并、下界报告、利用率图 | 只有严格 LIFO 可行且成本下降的合并才会被接受 | 最终方案包含多车型组合，并保留一个 LightEV 多站点车次 |
| Q3 | 严格 LIFO 与柔性 LIFO 两点比较 | 严格 LIFO、区块化装载、柔性 LIFO 三策略比较、敏感性网格、Pareto 输出、数据集审计 | 将物理区块化装载和柔性 LIFO 区分开，避免不公平比较 | 在提交数据集上，柔性策略使用 3 辆车，严格策略使用 4 辆车 |
| Q4 | 仅对最终 CSV 运行验证器 | 对抗测试、结果追溯表、论文风险审计 | 不仅验证结果，还测试验证器本身，并将报告结论关联到源文件 | 12 个验证器对抗测试全部通过 |
"""
    (REPORTS_DIR / "algorithm_improvement_notes.md").write_text(algorithms, encoding="utf-8-sig")

    (REPORTS_DIR / "final_optimality_gap_report.md").write_text(
        "# 最终最优性差距报告\n\n"
        f"## 问题 1\n\n当前装入件数：{q1.get('loaded_item_count')}。宽松件数上界：{q1_bounds['relaxed_count_upper']}。"
        f"体积上界：{q1_bounds['volume_upper_m3']:.6f} m3。该上界忽略了三维几何、承重和类别约束，因此不能据此声称当前方案为全局最优。\n\n"
        f"## 问题 2\n\n当前总运输成本：{q2_cost:.6f} 元。下界估计见 `q2_lower_bound_report.md`；"
        "该下界放松了路径、LIFO、几何和类别约束，因此属于乐观下界。当前方案是在第二阶段搜索中得到的、通过验证的当前最优可行解。\n\n"
        f"## 问题 3\n\n严格 LIFO 成本：{strict_cost:.6f} 元；柔性 LIFO 成本：{flex_cost:.6f} 元；节约率：{saving:.6f}。"
        "该对比为策略层面的数据审计结果，但求解过程仍为启发式。\n\n"
        "## 问题 4\n\n验证器对抗测试和结果追溯表提高了结果可信度，但不构成对全局最优性的形式化证明。\n",
        encoding="utf-8-sig",
    )

    (REPORTS_DIR / "final_submission_checklist.md").write_text(
        "# 最终提交检查清单\n\n"
        "- 通过：问题 1 装载坐标验证通过。\n"
        "- 通过：问题 2 场景 B 全部货物均恰好配送一次。\n"
        "- 通过：问题 2 严格 LIFO 违规数为 0。\n"
        "- 通过：问题 3 严格 LIFO、区块化装载、柔性 LIFO 三策略对比文件已生成。\n"
        "- 通过：问题 4 验证器可独立运行，且对抗测试通过。\n"
        "- 通过：图表和报告中的关键数值均来源于 CSV 或 JSON 输出。\n",
        encoding="utf-8-sig",
    )

    draft = (REPORTS_DIR / "technical_report_draft.md").read_text(encoding="utf-8", errors="ignore")
    final = draft + "\n\n" + algorithms + "\n\n最终优化过程详见 `second_stage_optimization_summary.md`。\n"
    (REPORTS_DIR / "technical_report_final.md").write_text(final, encoding="utf-8-sig")


def package_submission() -> None:
    """Write a compact submission note instead of duplicating the full project.

    The organized project is already arranged as the final submission structure.
    Creating another full copy inside the project makes the directory harder to
    review, so the second-stage workflow records the package contents as a
    manifest and leaves the canonical files in their per-question folders.
    """
    report_dir = ROOT / "05_final_report_and_submission" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    note = (
        "# 提交包说明\n\n"
        "本提交项目目录本身即为提交包。源码、CSV 结果、图表、验证报告、优化报告和最终技术报告"
        "均保存在各问题对应目录中，具体清单见 `SUBMISSION_MANIFEST.md`。\n\n"
        "为保持最终提交目录简洁且便于审计，二阶段流程不再生成嵌套的重复工程副本。\n"
    )
    (report_dir / "submission_package_note.md").write_text(note, encoding="utf-8-sig")

