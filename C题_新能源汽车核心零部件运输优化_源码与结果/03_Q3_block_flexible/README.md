# 03_Q3 大规模场景三策略对比

本目录对应问题 3，基于 8 个站点和 20 种规格货物的模拟数据，对严格 LIFO、区块化装载和柔性 LIFO 三类策略进行公平对比。目标是在硬约束通过的前提下，分析车辆数、运输成本、倒箱成本和装载率之间的权衡。

## 策略定义

- 策略 A：严格 LIFO。严格禁止倒箱，任意 LIFO 阻挡均判为不可行。
- 策略 B：区块化装载。按卸货顺序进行 X 向分区，并结合 Y 向通道控制站点货物区块。
- 策略 C：柔性 LIFO。允许有限倒箱，倒箱件数和倒箱体积计入惩罚成本，倒箱体积比例不得超过 15%。

## 主要算法

- 固定随机种子模拟数据生成；
- 距离矩阵 metric closure 修复与三角不等式检查；
- 多站点聚类、路线枚举和候选车次生成；
- 严格 LIFO、区块化装载、柔性 LIFO 三策略统一评价；
- 倒箱模拟与惩罚成本计算；
- 参数网格搜索和敏感性分析；
- Pareto 前沿与多数据集鲁棒性对比。

## 文件说明

- `code/q3_solver.py`：问题 3 求解器。
- `code/q3_objective.py`：问题 3 目标函数。
- `data/generated_cargo_q3.csv`：生成的模拟货物数据。
- `data/generated_distance_matrix.csv`：生成并修复后的距离矩阵。
- `data/q3_dataset_candidates.csv`：候选数据集筛选记录。
- `results/result_q3_comparison.csv`：三策略核心指标对比。
- `results/result_q3_loading_strict.csv`、`results/result_q3_loading_block.csv`、`results/result_q3_loading_flexible.csv`：三策略逐件装载坐标。
- `results/result_q3_trips_strict.csv`、`results/result_q3_trips_block.csv`、`results/result_q3_trips_flexible.csv`：三策略车辆与路线方案。
- `results/q3_strategy_grid_search.csv`：参数网格搜索结果。
- `results/q3_pareto_solutions.csv`：Pareto 候选解。
- `results/sensitivity_q3.csv`：倒箱惩罚敏感性分析。
- `plots/q3_comparison_plot.png`：三策略对比图。
- `plots/q3_pareto_front.png`：Pareto 前沿图。
- `plots/q3_sensitivity_heatmap.png`：敏感性热力图。
- `reports/validation_report_q3_*.json`、`reports/validation_report_q3_*.txt`：三策略验证报告。
- `reports/q3_dataset_audit.md`：模拟数据合规性审计。
- `reports/q3_strategy_optimization_report.md`：策略优化过程说明。
- `reports/q3_fair_comparison_report.md`：公平对比说明。

## 复核方式

从 `project_organized` 根目录运行：

```bash
python 04_Q4_validation_audit/code/validator.py --csv 03_Q3_block_flexible/results/result_q3_loading_flexible.csv --mode flexible --scenario q3
```

柔性方案的验证报告会给出倒箱件数、倒箱体积和倒箱比例。
