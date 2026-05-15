# 02_Q2 多车型多站点严格 LIFO 配送优化

本目录对应问题 2，研究场景 B 下 HeavyEV 与 LightEV 的多车型组合、多站点路径和三维装载协同优化。最终方案要求所有货物恰好配送一次，车辆装载坐标真实可验证，并严格满足 LIFO 卸货阻挡约束。

## 优化目标

问题 2 采用硬约束优先的字典序目标：

1. 硬约束违规数为 0；
2. 遗漏和重复配送数为 0；
3. 最小化总运输成本；
4. 在成本相近时减少车辆数；
5. 提高平均体积利用率和载重利用率；
6. 降低总里程和空载浪费。

## 主要算法

- 单站、双站、三站全排列路线池生成；
- 多车型、多路线、多 seed 候选车次池；
- 三维装箱与路线卸货顺序联合评价；
- 严格 LIFO 逐对阻挡检测；
- candidate trip dominance pruning；
- 集合覆盖选择与贪心回退；
- 低利用率车辆合并与路线局部修复；
- 松弛下界估计与 gap 分析。

## 文件说明

- `code/q2_solver.py`：问题 2 求解器。
- `code/q2_objective.py`：问题 2 目标函数和下界估计工具。
- `results/result_q2_trips.csv`：最终车辆组合、车型、路线、成本和利用率。
- `results/result_q2_loading.csv`：最终逐件装载坐标与配送站点。
- `results/result_q2_unassigned.csv`：未分配货物检查结果。
- `results/q2_candidate_trips.csv`：候选车次池记录。
- `results/q2_selected_trips.csv`：集合覆盖后选中的车次。
- `plots/q2_3d_plot.png`：最终装载图。
- `plots/q2_cost_convergence.png`：成本收敛图。
- `plots/q2_vehicle_utilization.png`：车辆利用率图。
- `reports/validation_report_q2.json`、`reports/validation_report_q2.txt`：独立验证报告。
- `reports/q2_optimization_report.md`：优化过程说明。
- `reports/q2_lower_bound_report.md`：下界和 gap 说明。
- `reports/q2_dominance_pruning_log.md`：候选车次支配剪枝记录。

## 复核方式

从项目根目录运行：

```bash
python 04_Q4_validation_audit/code/validator.py --csv 02_Q2_multi_vehicle_lifo/results/result_q2_loading.csv --mode strict --scenario q2
```

验证报告中会列出 LIFO 检查货物对数量、违规数量以及相关货物编号。
