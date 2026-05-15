# 03_Q3 中大规模场景与三策略对比

本目录对应问题三。问题三构建包含 8 个配送站点和 20 种规格货物的模拟数据集，并比较严格 LIFO、区块化装载和柔性 LIFO 三类策略在车辆数、运输成本、装载利用率和倒箱复杂度方面的表现。

## 一、策略定义

- 严格 LIFO：任意卸货阻挡均视为不可行，不允许倒箱。
- 区块化装载：按照卸货顺序进行 X 向分区，并通过 Y 向通道控制站点货物的空间归属。
- 柔性 LIFO：允许有限倒箱，将倒箱件数和倒箱体积计入惩罚成本，并要求倒箱体积比例不超过 15%。

## 二、核心算法

- 固定随机种子生成 20 种规格货物；
- 保留题目给定距离并生成 S4--S8 距离矩阵；
- 使用 metric closure 修复距离矩阵并检查三角不等式；
- 基于站点聚类和路线枚举生成候选车次；
- 对 strict、block、flexible 三类策略分别执行三维装载搜索；
- 模拟逐站卸货过程并统计倒箱件数、倒箱体积和倒箱比例；
- 对倒箱惩罚参数进行网格敏感性分析；
- 生成策略对比图、Pareto 前沿图和敏感性热力图。

## 三、目录内容

- `code/q3_solver.py`：问题三求解主程序。
- `code/q3_objective.py`：问题三目标函数和策略评价工具。
- `data/generated_cargo_q3.csv`：生成的 8 站点、20 规格货物数据。
- `data/generated_distance_matrix.csv`：生成并修复后的距离矩阵。
- `data/q3_dataset_candidates.csv`：候选数据集筛选记录。
- `results/result_q3_comparison.csv`：三策略核心指标对比。
- `results/result_q3_trips_strict.csv`、`results/result_q3_trips_block.csv`、`results/result_q3_trips_flexible.csv`：三策略车辆和路线方案。
- `results/result_q3_loading_strict.csv`、`results/result_q3_loading_block.csv`、`results/result_q3_loading_flexible.csv`：三策略逐件装载坐标。
- `results/q3_strategy_grid_search.csv`：策略参数网格搜索结果。
- `results/q3_pareto_solutions.csv`：三策略 Pareto 候选解。
- `results/sensitivity_q3.csv`：倒箱惩罚参数敏感性分析。
- `plots/q3_comparison_plot.png`：三策略成本与车辆数对比图。
- `plots/q3_pareto_front.png`：三策略 Pareto 前沿图。
- `plots/q3_sensitivity_heatmap.png`：柔性 LIFO 惩罚参数敏感性热力图。
- `reports/validation_report_q3_*.json`、`reports/validation_report_q3_*.txt`：三策略独立验证报告。
- `reports/q3_dataset_audit.md`：模拟数据合规性审计。
- `reports/q3_strategy_optimization_report.md`：策略搜索与优化过程说明。
- `reports/q3_fair_comparison_report.md`：三策略公平对比说明。

## 四、复现实验

在项目根目录运行完整流程：

```bash
python run_project.py
```

对柔性 LIFO 方案进行独立验证：

```bash
python 04_Q4_validation_audit/code/validator.py --csv 03_Q3_block_flexible/results/result_q3_loading_flexible.csv --mode flexible --scenario q3
```

验证报告会给出硬约束违规数、配送完整性、倒箱件数、倒箱体积和倒箱体积比例。
