# 05_final_report_and_submission 最终报告材料

本目录保存竞赛论文和最终提交说明相关文件。源码、结果表、图表和验证报告已按问题保存在前四个目录中，本目录不再重复存放完整工程副本，以保持提交目录简洁。

## 文件说明

- `reports/technical_report_final.md`：最终技术报告草稿，包含问题重述、模型假设、算法设计、结果分析和结论。
- `reports/technical_report_draft.md`：第一阶段技术报告草稿。
- `reports/second_stage_optimization_summary.md`：第二阶段极限优化总结。
- `reports/algorithm_improvement_notes.md`：算法选择、改进来源和新旧策略对比说明。

## 使用说明

正式提交时，建议将本目录下报告与前四个问题目录中的源码、CSV、图表和验证报告一并提交。报告中的数值应以各问题 `results/` 和 `reports/` 下文件为依据，不应手工修改为无法追溯的结果。

## 表述约束

本工程采用启发式与局部搜索方法求解三维装箱和路径协同优化问题。除非提供严格数学证明，论文中应使用“当前高质量可行解”“经验证程序检验通过”等表述，不应声称理论全局最优。
