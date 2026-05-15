# 公共运行脚本说明

本目录保存项目级运行脚本，负责组织四个问题的求解、验证、图表生成、报告生成和最终审计。为保证路径一致性，推荐通过项目根目录的 `run_project.py` 调用本目录中的脚本。

## 一、主要脚本

- `main.py`：完整主流程入口，依次运行问题一、问题二、问题三、独立验证、图表生成、报告生成和审计。
- `run_second_stage_optimization.py`：第二阶段优化入口，记录优化指标、生成上下界分析、运行验证器对抗测试并输出提交检查材料。
- `report_generator.py`：读取结果 CSV 与验证报告，生成 Markdown 技术报告草稿。
- `audit.py`：执行项目级审计，检查数据、约束、结果文件、图表和报告一致性。
- `second_stage_reports.py`：生成第二阶段优化总结、最终指标和提交检查清单。
- `requirements.txt`：Python 依赖清单。

## 二、推荐运行命令

在项目根目录执行：

```bash
python run_project.py --check-imports
python run_project.py
python run_project.py --second-stage
```

其中：

- `--check-imports` 用于检查整理后目录结构下的模块导入是否正常；
- 不带参数时运行完整求解与结果生成流程；
- `--second-stage` 用于运行第二阶段优化、审计和提交材料生成流程。

## 三、输出位置

运行过程中会先在项目根目录生成统一的 `results/`、`plots/`、`reports/` 输出目录，再通过 `sync_outputs.py` 同步到各问题目录。分题目录中的结果是论文和附件复核的主要依据。
