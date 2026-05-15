# C 题源码与结果附件说明

本目录为 C 题“新能源汽车核心零部件三维装载与多点配送协同优化”的源码与结果附件。项目按照“公共核心模块、分问题求解、独立验证审计、最终报告材料”的结构组织，便于评阅者复现实验、核查结果和追溯论文中的关键数值。

## 一、目录结构

- `00_common_core/`：四个问题共同使用的数据结构、几何计算、三维装箱、路径成本、优化选择、可视化和流程控制代码。
- `01_Q1_single_vehicle/`：问题一单车三维装箱与重心控制的求解代码、结果表、图表和验证报告。
- `02_Q2_multi_vehicle_lifo/`：问题二多车型、多站点、严格 LIFO 配送优化的求解代码、候选车次、最终路线、装载坐标和验证报告。
- `03_Q3_block_flexible/`：问题三中大规模模拟数据、严格 LIFO、区块化装载和柔性 LIFO 三策略对比材料。
- `04_Q4_validation_audit/`：独立验证器、验证器对抗测试、结果追溯、最终审计和提交检查材料。
- `05_final_report_and_submission/`：技术报告草稿、第二阶段优化总结、算法改进说明和最终提交相关说明。
- `bootstrap_paths.py`：整理版目录的 Python 导入路径配置。
- `run_project.py`：项目统一运行入口。
- `sync_outputs.py`：将根目录运行结果同步到各分题目录的脚本。
- `SUBMISSION_MANIFEST.md`：提交文件清单与用途说明。

## 二、运行环境

推荐使用 Python 3.10 及以上版本。主要依赖包括 `numpy`、`pandas`、`matplotlib` 等。依赖清单见：

```text
00_common_core/run/requirements.txt
```

安装依赖可在项目根目录执行：

```bash
pip install -r 00_common_core/run/requirements.txt
```

## 三、运行方式

请在本目录，即项目根目录下执行以下命令。

检查模块导入路径：

```bash
python run_project.py --check-imports
```

运行完整求解、验证、图表生成和报告生成流程：

```bash
python run_project.py
```

运行第二阶段优化、仪表盘记录、审计和提交检查流程：

```bash
python run_project.py --second-stage
```

程序运行后会在根目录生成统一的 `results/`、`plots/`、`reports/` 输出目录，并通过 `sync_outputs.py` 将结果同步到各问题对应目录。提交版本保留分题目录中的结果文件，便于逐题核查。

## 四、结果复核顺序

推荐按以下顺序审阅附件：

1. 阅读 `05_final_report_and_submission/reports/technical_report_final.md`，了解模型、算法和主要结论。
2. 阅读各问题目录下的 `results/`，核查车辆方案、装载坐标和关键指标。
3. 阅读各问题目录下的 `plots/`，查看三维装载图、策略对比图和敏感性分析图。
4. 阅读各问题目录下的 `reports/validation_report_*.json` 与 `reports/validation_report_*.txt`，核查硬约束验证结果。
5. 阅读 `04_Q4_validation_audit/reports/audit_report.md` 和 `04_Q4_validation_audit/reports/final_submission_checklist.md`，核查最终审计结论。

## 五、编码与文件格式

文本文件采用 UTF-8 编码，CSV 文件可使用 Excel、WPS 或 Python 读取。所有装载结果均以 CSV 表形式给出，包含车辆编号、货物编号、站点、左下角坐标、姿态尺寸、重量和类别等字段，可由独立验证器重新读取并验证。

## 六、结果说明

本项目通过多起点装箱启发式、候选车次池、集合覆盖选择、局部修复、三策略对比和独立验证闭环得到当前最优可行方案。论文和附件中的关键数值均来源于 `results/` 或 `reports/` 中的可复核文件。
