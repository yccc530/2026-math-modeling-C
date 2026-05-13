# C 题提交工程说明

本目录为 C 题“新能源汽车核心零部件三维装载与多点配送协同优化”的整理版工程。目录按题目问题划分，分别保存源码、结果表、图表和验证报告，便于评阅时逐项核查。运行缓存、重复归档副本和临时输出已从提交目录中移除。

## 运行入口

请在 `project_organized` 根目录执行以下命令：

```bash
python run_project.py --check-imports
python run_project.py
python run_project.py --second-stage
```

其中 `--check-imports` 用于检查整理版目录下的模块导入是否正确；不带参数时运行完整求解流程；`--second-stage` 运行第二阶段优化与审计流程。

## 目录结构

- `00_common_core/`：公共数据、几何、装箱、路径、优化、可视化和运行控制代码。
- `01_Q1_single_vehicle/`：问题 1 单车三维装箱、重心控制及其结果材料。
- `02_Q2_multi_vehicle_lifo/`：问题 2 多车型、多站点、严格 LIFO 配送优化材料。
- `03_Q3_block_flexible/`：问题 3 严格 LIFO、区块化装载、柔性 LIFO 三策略对比材料。
- `04_Q4_validation_audit/`：问题 4 独立验证器、对抗测试、审计和结果追溯材料。
- `05_final_report_and_submission/`：最终技术报告、第二阶段优化总结和算法改进说明。

## 推荐核查顺序

1. 阅读 `05_final_report_and_submission/reports/technical_report_final.md`，了解模型、算法和结论。
2. 阅读 `05_final_report_and_submission/reports/second_stage_optimization_summary.md`，核查第二阶段优化过程。
3. 阅读各问题 `reports/validation_report_*.json` 和 `reports/validation_report_*.txt`，核查硬约束验证结果。
4. 阅读各问题 `results/result_*_loading.csv`，核查逐件货物坐标、姿态、车辆编号和站点信息。

## 运行机制

整理版通过根目录的 `bootstrap_paths.py` 将各题代码目录加入 Python 搜索路径，因此 `q1_solver`、`q2_solver`、`q3_solver`、`validator` 等模块可以在整理后的结构中正常导入。

完整运行时，程序会临时在根目录生成 `results/`、`plots/`、`reports/` 三个运行输出目录。运行结束后，`sync_outputs.py` 会将对应文件同步到各问题自己的子目录。提交前可删除根目录临时输出目录，不影响已整理的分题材料。

## 编码说明

所有 `.py`、`.md`、`.txt`、`.csv`、`.json` 文本文件统一使用 `UTF-8 with BOM` 编码，以兼容 Windows、VS Code、Excel 和常见中文文本编辑器。

## 结果表述

本工程使用多起点启发式、候选车次池、集合覆盖、局部搜索和独立验证闭环得到当前高质量可行解。除非报告中明确给出精确证明，否则不声称理论全局最优。
