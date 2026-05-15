# 04_Q4 独立验证、审计与结果追溯

本目录对应问题四。问题四实现独立于求解器的验证程序，用于读取装载坐标 CSV，并逐项检查空间几何、支撑承重、货物类别、车辆载重、车辆重心、LIFO 卸货阻挡、倒箱统计、遗漏配送和重复配送等约束。

## 一、验证范围

- 车辆边界越界；
- 三维空间重叠；
- 底部支撑与悬空；
- 顶面单位面积承重；
- 类别 I 落地约束；
- 类别 II 顶层约束；
- 类别 III 连续堆叠层数；
- 类别 V 与类别 II 接触关系；
- 车辆载重与 X 方向重心；
- 严格 LIFO 阻挡；
- 柔性 LIFO 倒箱件数、倒箱体积和倒箱比例；
- 货物遗漏配送和重复配送；
- 结果文件、验证报告和论文关键指标一致性。

## 二、目录内容

- `code/validator.py`：独立验证器，支持命令行读取 CSV 并输出 JSON/TXT 验证报告。
- `code/audit.py`：项目级审计程序。
- `code/optimization_dashboard.py`：第二阶段优化指标读取和仪表盘生成程序。
- `tests/test_validator_adversarial.py`：验证器对抗测试，覆盖重叠、接触、承重、LIFO、重心和重复/遗漏等典型违规样例。
- `results/optimization_dashboard.csv`：第二阶段迭代优化指标记录。
- `results/final_metrics.csv`：最终关键指标汇总。
- `reports/validator_adversarial_report.md`：验证器对抗测试报告。
- `reports/result_traceability_table.csv`：论文关键数值追溯表。
- `reports/paper_risk_audit.md`：论文表述风险审计。
- `reports/audit_report.md`：最终审计报告。
- `reports/bug_list.md`：审计发现问题列表。
- `reports/fix_plan.md`：修复计划记录。
- `reports/final_optimality_gap_report.md`：最终上下界或松弛 gap 说明。
- `reports/final_submission_checklist.md`：提交前检查清单。

## 三、命令示例

在项目根目录验证问题二严格 LIFO 方案：

```bash
python 04_Q4_validation_audit/code/validator.py --csv 02_Q2_multi_vehicle_lifo/results/result_q2_loading.csv --mode strict --scenario q2
```

验证问题三柔性 LIFO 方案：

```bash
python 04_Q4_validation_audit/code/validator.py --csv 03_Q3_block_flexible/results/result_q3_loading_flexible.csv --mode flexible --scenario q3
```

运行验证器对抗测试：

```bash
python 04_Q4_validation_audit/tests/test_validator_adversarial.py
```

验证通过时，文本报告会输出 `PASS: no violations found`。该短语为程序判定标识，详细说明以 JSON 和 TXT 验证报告为准。
