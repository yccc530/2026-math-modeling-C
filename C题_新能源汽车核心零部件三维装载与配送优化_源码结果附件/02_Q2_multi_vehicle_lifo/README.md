# 02_Q2 多车型多站点严格 LIFO 配送优化

本目录对应问题二。问题二在场景 B 下同时考虑 HeavyEV 与 LightEV 两种车型、多站点配送路线、车辆三维装载坐标和严格 LIFO 卸货阻挡约束，目标是在所有货物恰好配送一次的前提下最小化总运输成本。

## 一、求解目标

问题二采用硬约束优先的字典序目标：

1. 硬约束违规数为 0；
2. 遗漏配送数和重复配送数均为 0；
3. 最小化总运输成本；
4. 在成本接近时减少车辆数；
5. 提高平均体积利用率和平均载重利用率；
6. 降低总行驶距离和车辆空载浪费。

## 二、核心算法

- 枚举单站、双站和三站全排列路线；
- 对不同车型、路线、排序策略和随机种子生成候选车次；
- 对每个候选车次执行三维装箱搜索；
- 对同车货物逐对检查严格 LIFO 阻挡关系；
- 对候选车次进行支配剪枝；
- 通过集合覆盖模型选择最终车次组合；
- 对低利用率车辆执行合并、拆分和局部路线替换；
- 使用松弛下界评估当前方案的成本 gap。

## 三、目录内容

- `code/q2_solver.py`：问题二求解主程序。
- `code/q2_objective.py`：目标函数、方案评价和下界估计工具。
- `results/result_q2_trips.csv`：最终车辆组合、车型、路线、距离、成本和利用率。
- `results/result_q2_loading.csv`：最终逐件装载坐标、姿态、目的站点和车辆编号。
- `results/result_q2_unassigned.csv`：未分配货物检查结果。
- `results/q2_candidate_trips.csv`：候选车次池记录。
- `results/q2_selected_trips.csv`：集合覆盖后选中的车次。
- `plots/q2_vehicle_utilization.png`：车辆体积利用率和载重利用率对比图。
- `plots/q2_3d_plot.png`：多车辆三维装载坐标图。
- `plots/q2_cost_convergence.png`：候选方案成本收敛过程图。
- `reports/validation_report_q2.json`：结构化验证报告。
- `reports/validation_report_q2.txt`：文本验证报告。
- `reports/q2_solution_report.txt`：最终车辆组合和路线说明。
- `reports/q2_optimization_report.md`：候选车次生成、集合覆盖和局部修复过程说明。
- `reports/q2_lower_bound_report.md`：下界估计与 gap 分析。
- `reports/q2_dominance_pruning_log.md`：候选车次支配剪枝记录。

## 四、复现实验

在项目根目录运行完整流程：

```bash
python run_project.py
```

对问题二最终装载结果进行独立验证：

```bash
python 04_Q4_validation_audit/code/validator.py --csv 02_Q2_multi_vehicle_lifo/results/result_q2_loading.csv --mode strict --scenario q2
```

验证报告会给出空间约束、车辆载重、车辆重心、配送完整性和严格 LIFO 检查结果。
