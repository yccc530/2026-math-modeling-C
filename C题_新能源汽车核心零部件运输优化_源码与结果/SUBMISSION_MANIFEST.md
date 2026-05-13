# 提交文件清单

本清单用于说明 `project_organized` 目录中各类文件的提交用途。

## 必交源码

- `bootstrap_paths.py`：整理版工程导入路径配置。
- `run_project.py`：统一运行入口。
- `sync_outputs.py`：运行结果同步脚本。
- `00_common_core/code/`：公共数据、几何、装箱、路径、优化、可视化和验证依赖模块。
- `00_common_core/run/`：主流程、第二阶段优化、报告生成和审计脚本。
- `01_Q1_single_vehicle/code/`：问题 1 专用求解代码。
- `02_Q2_multi_vehicle_lifo/code/`：问题 2 专用求解代码。
- `03_Q3_block_flexible/code/`：问题 3 专用求解代码。
- `04_Q4_validation_audit/code/`：独立验证、审计和追溯代码。
- `04_Q4_validation_audit/tests/`：验证器对抗测试。

## 必交结果

- 各问题 `results/`：装载坐标、车辆方案、候选解、敏感性分析和最终指标 CSV。
- 各问题 `plots/`：三维装载图、对比图、收敛图和敏感性图。
- 各问题 `reports/`：验证报告、优化说明、上下界 gap、审计和风险检查报告。
- `05_final_report_and_submission/reports/`：技术报告与第二阶段优化总结。

## 已清理内容

提交目录中不保留以下运行期文件：

- `__pycache__/`；
- 根目录临时 `results/`、`plots/`、`reports/`；
- 重复的完整归档副本。

重新运行程序后若再次生成根目录临时输出，可保留用于复现实验，也可在确认各问题目录已同步后删除。
