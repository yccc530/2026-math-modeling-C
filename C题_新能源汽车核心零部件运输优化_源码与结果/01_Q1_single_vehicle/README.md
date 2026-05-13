# 01_Q1 单车三维装箱与重心控制

本目录对应问题 1，研究车型 1 HeavyEV 的单车三维装箱问题。目标是在所有硬约束通过的前提下，尽可能提高装入件数、体积利用率和载重利用率，并控制 X 方向重心位置。

## 优化目标

问题 1 使用字典序目标函数评价可行解：

1. 最大化装入货物件数；
2. 在件数相同的情况下最大化装入体积；
3. 在前两项相近时最大化装入重量；
4. 最小化 X 方向重心偏移；
5. 提高重心、支撑和承重等安全裕度。

## 主要算法

- extreme point / corner point 三维装箱启发式；
- 多排序策略：类别优先、体积降序、重量降序、底面积降序、密度降序、随机扰动等；
- 多合法姿态枚举；
- 多随机种子搜索；
- 重心修正与局部插入修复；
- 独立验证器硬约束复核。

## 文件说明

- `code/q1_solver.py`：问题 1 求解器。
- `code/q1_objective.py`：问题 1 字典序目标函数、上界估计和 gap 计算。
- `results/result_q1_loading.csv`：最终逐件装载坐标与姿态。
- `results/result_q1_summary.csv`：最终装载指标摘要。
- `results/result_q1_unloaded.csv`：未装入货物记录。
- `results/q1_best_solutions.csv`：多起点搜索得到的可行解记录。
- `plots/q1_3d_plot.png`：最终三维装载图。
- `plots/q1_pareto_front.png`：可行解前沿图。
- `reports/validation_report_q1.json`、`reports/validation_report_q1.txt`：独立验证报告。
- `reports/q1_optimization_report.md`：优化过程、上界估计与 gap 说明。

## 复核方式

从 `project_organized` 根目录运行：

```bash
python run_project.py --check-imports
```

若需要重新生成问题 1 结果，可运行完整主程序后由 `sync_outputs.py` 同步输出到本目录。
