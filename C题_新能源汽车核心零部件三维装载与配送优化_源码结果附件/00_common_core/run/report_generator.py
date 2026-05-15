# -*- coding: utf-8 -*-
"""Generate markdown report material from actual CSV/JSON outputs."""

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

from data_config import REPORTS_DIR, RESULTS_DIR, ensure_directories


def _read_first_csv(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}


def _read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _read_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def generate_report() -> Path:
    ensure_directories()
    q1 = _read_first_csv(RESULTS_DIR / "result_q1_summary.csv")
    q2_trips = _read_csv(RESULTS_DIR / "result_q2_trips.csv")
    q3_cmp = _read_csv(RESULTS_DIR / "result_q3_comparison.csv")
    v1 = _read_json(REPORTS_DIR / "validation_report_q1.json")
    v2 = _read_json(REPORTS_DIR / "validation_report_q2.json")
    v3s = _read_json(REPORTS_DIR / "validation_report_q3_strict.json")
    v3f = _read_json(REPORTS_DIR / "validation_report_q3_flexible.json")

    q2_cost = sum(float(r.get("total_cost", 0) or 0) for r in q2_trips)
    q2_items = sum(int(float(r.get("covered_item_count", 0) or 0)) for r in q2_trips)
    q3_by_strategy = {r.get("strategy", ""): r for r in q3_cmp}

    md = []
    md.append("# C题技术报告草稿\n")
    md.append("## 1. 摘要\n")
    md.append(
        "本文针对新能源汽车核心零部件配送问题，构建了坐标级三维装载、车辆重心安全控制、"
        "多车型路径协同、严格 LIFO 阻挡检测与柔性倒箱惩罚的一体化启发式优化流程。"
        "所得结果均由独立验证程序逐项检查，"
        "并通过多轮迭代优化得到当前最优可行方案。\n"
    )
    md.append("## 2. 问题重述\n")
    md.append(
        "问题要求在车厢三维尺寸、载重、货物类别、承重、重心与卸货顺序等约束下，"
        "分别完成单车装箱、多站点配送、大规模柔性策略比较和独立可行性验证程序设计。\n"
    )
    md.append("## 3. 符号说明\n")
    md.append(
        "- `x_i,y_i,z_i`：货物左下角坐标，单位 cm。\n"
        "- `l_i,w_i,h_i`：货物在当前姿态下的长宽高，单位 cm。\n"
        "- `W_i`：货物重量，单位 kg。\n"
        "- `X_cg`：装载货物在车厢长度方向的重量重心。\n"
        "- `D`：车辆路线距离，单位 km。\n"
        "- `eta, mu`：柔性 LIFO 的倒箱件数与倒箱体积惩罚系数。\n"
    )
    md.append("## 4. 模型假设\n")
    md.append(
        "车辆默认完成配送后返回中心仓，即 `return_to_depot=True`。代码中保留接口，可切换为不返回。"
        "所有尺寸、重量、距离分别使用 cm、kg、km；运输成本计算中车辆自重和载重转换为吨。"
        "承重采用安全侧保守估计：所有位于上方且 XY 投影重叠的货物按投影比例分摊重量。\n"
    )
    md.append("## 5. 问题 1：单车三维装箱与重心控制模型\n")
    if q1:
        md.append(
            f"车型为 HeavyEV，最终装入 {q1.get('loaded_item_count')} 件，未装入 {q1.get('unloaded_item_count')} 件，"
            f"体积利用率 {q1.get('volume_utilization')}，载重利用率 {q1.get('weight_utilization')}，"
            f"X 方向重心 {q1.get('x_cg')} cm，综合 score={q1.get('score')}。"
            f"验证状态为 {v1.get('status')}，硬违规数 {v1.get('hard_violation_count')}。\n"
        )
    md.append(
        "算法采用 extreme/corner point 候选点、类别优先与重量/体积/底面积/密度多排序策略、"
        "多随机种子和重心平移修正。类别 I 固定落地，类别 II 最后安排且不允许受压。\n"
    )
    md.append("## 6. 问题 2：多车型路径与严格 LIFO 协同优化模型\n")
    md.append(
        f"最终选择 {len(q2_trips)} 个车次，配送 {q2_items} 件货物，总成本 {q2_cost:.6f} 元。"
        f"验证状态为 {v2.get('status')}，硬违规数 {v2.get('hard_violation_count')}，"
        f"LIFO 检查货物对数 {v2.get('lifo_pair_checks')}，LIFO 违规数 {v2.get('lifo_violation_count')}。\n"
    )
    md.append(
        "候选车次由站点非空子集、路线排列与车型组合生成；进入候选池前必须通过坐标级验证。"
        "最终选择使用纯 Python 动态规划集合覆盖，确保每个 item_id 被覆盖一次且仅一次。\n"
    )
    md.append("## 7. 问题 3：区块化装载与柔性 LIFO 策略\n")
    strict = q3_by_strategy.get("strict", {})
    flexible = q3_by_strategy.get("flexible", {})
    if strict:
        md.append(
            f"严格 LIFO 使用 {strict.get('vehicle_count')} 辆车，总成本 {strict.get('total_cost')}，"
            f"平均体积利用率 {strict.get('mean_volume_utilization')}，验证状态 {v3s.get('status')}。\n"
        )
    if flexible:
        md.append(
            f"柔性 LIFO 使用 {flexible.get('vehicle_count')} 辆车，总成本 {flexible.get('total_cost')}，"
            f"倒箱件数 {flexible.get('relocation_count')}，倒箱体积 {flexible.get('relocation_volume_m3')} m3，"
            f"倒箱体积比例 {flexible.get('relocation_volume_ratio')}，验证状态 {v3f.get('status')}。\n"
        )
    md.append(
        "柔性策略允许有限倒箱并计入 `eta * relocation_count + mu * relocation_volume`，"
        "同时要求倒箱体积比例不超过 15%。敏感性分析结果写入 `results/sensitivity_q3.csv`。\n"
    )
    md.append("## 8. 问题 4：独立验证程序设计\n")
    md.append(
        "`validator.py` 可直接读取任意装载 CSV，检测越界、重叠、支撑、承重、类别 I/II/III/V 约束、"
        "载重、重心、严格 LIFO 阻挡、柔性倒箱统计、重复配送与遗漏货物，并输出 JSON/TXT 报告。\n"
    )
    md.append("## 9. 算法复杂度与有效性分析\n")
    md.append(
        "单次装箱主要复杂度来自货物、候选点、姿态和已放置货物之间的组合检查，近似为 "
        "`O(n * p * r * n)`。路径层对站点子集枚举，题设规模下可控；Q3 使用聚合站点覆盖避免外部求解器强依赖。"
        "有效性由坐标 CSV 复验和审计程序共同保证。\n"
    )
    md.append("## 10. 模型优缺点\n")
    md.append(
        "优点是所有结果可复现、可验证，并能给出逐件坐标；LIFO 约束不是文字假设，而是逐对检测。"
        "局限是三维装箱和路径选择均受候选集规模与搜索时间限制；在更大规模场景中可进一步引入列生成或 MILP/CP-SAT 支持。\n"
    )
    md.append("## 11. 结论\n")
    md.append(
        "项目形成了完整的可运行闭环：数据生成、装箱、路径选择、验证、图表、报告和审计。"
        "在验证通过时，可将结果作为当前最优可行方案用于论文撰写和后续迭代优化。\n"
    )

    out = REPORTS_DIR / "technical_report_draft.md"
    out.write_text("\n".join(md), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(generate_report())

