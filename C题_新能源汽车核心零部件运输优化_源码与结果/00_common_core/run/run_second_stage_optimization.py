# -*- coding: utf-8 -*-
"""Second-stage optimization runner.

该脚本记录基准方案，运行增强求解器、报告和测试，并将最终当前最优可行解写入优化仪表盘。
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
        "# 第二阶段优化总结\n\n",
        "## 基准方案与最终方案\n\n",
        f"- 基准仪表盘轮次：{baseline['iteration']}\n",
        f"- 最终仪表盘轮次：{final_row['iteration']}\n",
        f"- 验证器对抗测试：{'通过' if tests_passed else '未通过'}\n\n",
        "## 使用算法\n\n",
        "Q1 使用 extreme/corner point 三维装箱和多排序策略，并由加权评分升级为字典序选择：先比较装入件数，再比较体积、重量、重心偏移和安全裕度。\n\n",
        "Q2 使用路线枚举、验证门控候选车次、站点批次拆分、严格 LIFO 跨站合并、HeavyEV/LightEV 车型替换、支配剪枝记录和松弛下界估计。\n\n",
        "Q3 使用严格 LIFO、区块化装载和柔性/区块化 LIFO 三策略，并基于已评估可行解生成敏感性分析和 Pareto 结果。\n\n",
        "Q4 使用验证器对抗测试和结果追溯检查。\n\n",
        "## 最终当前最优可行解\n\n",
        f"- Q1 装入件数：{final_row['q1_loaded_count']}，体积利用率：{final_row['q1_volume_utilization']}，载重利用率：{final_row['q1_weight_utilization']}。\n",
        f"- Q2 车辆数：{final_row['q2_vehicle_count']}，总成本：{final_row['q2_total_transport_cost']}，LIFO 违规数：{final_row['q2_lifo_violation_count']}。\n",
        f"- Q3 严格策略成本：{final_row['q3_strict_total_cost']}，柔性策略成本：{final_row['q3_flexible_total_cost']}，节约率：{final_row['q3_flexible_cost_saving_ratio']}。\n\n",
        "## 局限性\n\n",
        "本项目使用启发式搜索和松弛上下界，不能声称理论全局最优。当前结果是在多策略搜索和独立验证下得到的当前最优可行解。\n",
    ]
    (REPORTS_DIR / "second_stage_optimization_summary.md").write_text("".join(lines), encoding="utf-8-sig")


def main() -> int:
    ensure_directories()
    run_all(max_iterations=1)
    generate_report()
    audit_project()
    baseline = record_dashboard(0, "基准方案", "第一阶段当前最优可行解", best_so_far=True, notes="第二阶段输出生成前的基准方案")

    result = run_all(max_iterations=1)
    generate_report()
    audit = audit_project()
    tests_passed = run_adversarial_tests()
    write_final_reports()
    audit = audit_project()
    final_row = record_dashboard(
        1,
        "q1/q2/q3/q4",
        "Q1 字典序目标 + Q2 候选车次池 + Q3 严格/区块/柔性三策略 + Q4 对抗测试",
        best_so_far=bool(audit.get("status") == "PASS" and tests_passed),
        rollback_triggered=False,
        notes="第二阶段增强后的当前最优可行解",
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
    print(f"第二阶段优化结果：{status}")
    print()
    print("Q1:")
    print("基准方案 -> 最终方案")
    print(f"装入件数：{baseline['q1_loaded_count']} -> {final_row['q1_loaded_count']}")
    print(f"体积利用率：{baseline['q1_volume_utilization']} -> {final_row['q1_volume_utilization']}")
    print(f"载重利用率：{baseline['q1_weight_utilization']} -> {final_row['q1_weight_utilization']}")
    print(f"x_cg: {baseline['q1_xcg']} -> {final_row['q1_xcg']}")
    print(f"上界差距：宽松件数差距={q1_count_gap}，详见 reports/q1_optimization_report.md")
    print()
    print("Q2:")
    print("基准方案 -> 最终方案")
    print(f"车辆数：{baseline['q2_vehicle_count']} -> {final_row['q2_vehicle_count']}")
    print(f"总成本：{baseline['q2_total_transport_cost']} -> {final_row['q2_total_transport_cost']}")
    print(f"总里程：{baseline['q2_total_distance']} -> {final_row['q2_total_distance']}")
    print(f"平均利用率：体积={final_row['q2_average_volume_utilization']}，载重={final_row['q2_average_weight_utilization']}")
    print(f"下界差距：宽松固定成本差距率={q2_gap:.6f}，详见 reports/q2_lower_bound_report.md")
    print(f"LIFO 违规数：{final_row['q2_lifo_violation_count']}")
    print()
    print("Q3:")
    print("严格/区块/柔性三策略最终对比")
    print(f"车辆数：strict={final_row['q3_strict_vehicle_count']}，flexible={final_row['q3_flexible_vehicle_count']}")
    print(f"运输成本：strict={final_row['q3_strict_total_cost']}，flexible={final_row['q3_flexible_transport_cost']}")
    print(f"倒箱惩罚：{final_row['q3_flexible_penalty']}")
    print(f"总成本：strict={final_row['q3_strict_total_cost']}，flexible={final_row['q3_flexible_total_cost']}")
    print(f"节约率：{(strict_cost - flex_cost) / strict_cost:.6f}")
    print(f"倒箱比例：{final_row['q3_flexible_relocation_ratio']}")
    print()
    print("Q4:")
    print(f"验证器测试：{'PASS' if tests_passed else 'FAIL'}")
    print("结果追溯：reports/result_traceability_table.csv")
    print("论文风险：reports/paper_risk_audit.md")
    print(f"审计：{audit.get('status')}")
    print()
    print("剩余局限：")
    print("- 当前采用启发式搜索，没有全局最优证明。")
    print("- 上下界为松弛估计，偏乐观。")
    print("- 若时间允许，可进一步使用 MILP/CP-SAT 列生成方法收紧 Q2/Q3 最优性 gap。")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
