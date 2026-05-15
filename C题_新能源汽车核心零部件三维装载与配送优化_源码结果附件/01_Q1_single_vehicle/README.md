# 01_Q1 单车三维装箱与重心控制

本目录对应问题一。问题一在 HeavyEV 单车车厢内对场景 A 货物进行三维装载优化，要求满足车厢边界、空间不重叠、载重、重心、类别规则、支撑和承重等硬约束，并尽可能提高装载件数、体积利用率和载重利用率。

## 一、求解目标

问题一采用硬约束优先的字典序目标：

1. 最大化装入货物件数；
2. 在件数相同的情况下最大化装入体积；
3. 在前两项相近时最大化装入重量；
4. 最小化车辆 X 方向重心偏移；
5. 提高支撑、承重和重心安全裕度。

## 二、核心算法

- 极点/角点三维装箱启发式；
- 类别优先、体积降序、重量降序、底面积降序、密度降序和随机扰动等多排序策略；
- 按货物类别枚举合法姿态；
- 多随机种子搜索；
- 重心修正、空隙插入和局部修复；
- 独立验证器复核硬约束。

## 三、目录内容

- `code/q1_solver.py`：问题一求解主程序。
- `code/q1_objective.py`：字典序目标函数、上界估计和 gap 计算。
- `results/result_q1_loading.csv`：最终逐件装载坐标、姿态和车辆编号。
- `results/result_q1_summary.csv`：装载件数、体积利用率、载重利用率、重心等摘要指标。
- `results/result_q1_unloaded.csv`：未装入货物清单。
- `results/q1_best_solutions.csv`：多起点搜索得到的候选可行方案记录。
- `plots/q1_3d_plot.png`：HeavyEV 最终三维装载图。
- `plots/q1_pareto_front.png`：多起点可行解前沿图。
- `reports/validation_report_q1.json`：结构化验证报告。
- `reports/validation_report_q1.txt`：文本验证报告。
- `reports/q1_optimization_report.md`：问题一优化过程、上界估计和 gap 说明。

## 四、复现实验

在项目根目录执行完整流程：

```bash
python run_project.py
```

若仅需检查模块导入：

```bash
python run_project.py --check-imports
```

运行完成后，问题一相关输出会同步到本目录的 `results/`、`plots/` 和 `reports/` 子目录中。
