# 04_Q4 独立验证、审计与结果追溯

本目录对应问题 4，目标是提高结果可信度。验证器与求解器分离，能够独立读取装载坐标 CSV，并检查空间、类别、承重、重心、LIFO、遗漏和重复配送等核心约束。

## 验证范围

- 空间越界和空间重叠；
- 支撑、悬空和顶面承重；
- 类别 I、II、III、V 的专属约束；
- 车辆载重和 X 方向重心；
- 严格 LIFO 阻挡；
- flexible LIFO 倒箱统计；
- 同一货物重复配送和遗漏配送；
- 结果文件、图表、报告和论文表述一致性。

## 文件说明

- `code/validator.py`：独立验证器，可从命令行运行。
- `code/audit.py`：项目级审计程序。
- `code/optimization_dashboard.py`：第二阶段优化指标仪表盘。
- `tests/test_validator_adversarial.py`：验证器对抗测试。
- `results/optimization_dashboard.csv`：第二阶段迭代指标记录。
- `results/final_metrics.csv`：最终关键指标汇总。
- `reports/validator_adversarial_report.md`：对抗测试报告。
- `reports/result_traceability_table.csv`：结果追溯表。
- `reports/paper_risk_audit.md`：论文风险审计。
- `reports/audit_report.md`：最终审计结论。
- `reports/bug_list.md`、`reports/fix_plan.md`：审计问题与修复计划。
- `reports/final_optimality_gap_report.md`：最终上下界或松弛 gap 说明。
- `reports/final_submission_checklist.md`：提交前检查清单。

## 命令示例

从 `project_organized` 根目录运行：

```bash
python 04_Q4_validation_audit/code/validator.py --csv 02_Q2_multi_vehicle_lifo/results/result_q2_loading.csv --mode strict --scenario q2
python 04_Q4_validation_audit/code/validator.py --csv 03_Q3_block_flexible/results/result_q3_loading_flexible.csv --mode flexible --scenario q3
python 04_Q4_validation_audit/tests/test_validator_adversarial.py
```

验证通过时，文本报告会输出 `PASS: no violations found`；该英文短语保留为程序判定标识，正文报告均使用中文说明。
