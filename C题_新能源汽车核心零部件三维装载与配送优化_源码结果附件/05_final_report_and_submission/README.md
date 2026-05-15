# 05_final_report_and_submission 最终报告与提交材料

本目录保存技术报告、优化总结和提交说明相关材料。源码、结果表、图表和验证报告已分别存放在前四个问题目录中，本目录主要用于集中呈现模型方法、结果解释、算法改进过程和提交前核查结论。

## 一、目录内容

- `reports/technical_report_final.md`：最终技术报告文本材料，包含问题重述、模型假设、算法设计、结果分析、模型评价和结论。
- `reports/technical_report_draft.md`：阶段性技术报告草稿。
- `reports/second_stage_optimization_summary.md`：第二阶段优化总结，记录优化目标、策略调整、关键指标和最终结果。
- `reports/algorithm_improvement_notes.md`：算法选择、改进来源和新旧策略对比说明。

## 二、与论文的对应关系

论文中的车辆数、运输成本、装载率、倒箱统计、验证状态等关键数值，应与各问题目录中的 `results/` 和 `reports/` 文件保持一致。本目录报告用于说明建模思路和结果解释，不替代原始 CSV 坐标表和独立验证报告。

## 三、提交范围

正式提交时，本目录应与以下材料共同提交：

- `00_common_core/` 公共代码；
- `01_Q1_single_vehicle/` 问题一代码与结果；
- `02_Q2_multi_vehicle_lifo/` 问题二代码与结果；
- `03_Q3_block_flexible/` 问题三代码、数据与结果；
- `04_Q4_validation_audit/` 验证器、审计和追溯材料；
- 根目录 `README.md`、`SUBMISSION_MANIFEST.md`、`run_project.py`、`bootstrap_paths.py` 和 `sync_outputs.py`。

## 四、结果追溯要求

报告中的所有关键结论均应能够追溯到对应的 CSV、JSON、TXT 或图表文件。若重新运行程序得到新结果，应同步更新分题结果目录和论文中的对应数值。
