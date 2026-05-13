# 公共运行脚本说明

本目录保存完整求解、第二阶段优化、报告生成和审计相关脚本。整理版项目建议通过根目录 `run_project.py` 调用这些脚本，以保证导入路径、输出目录和结果同步逻辑一致。

## 主要文件

- `main.py`：完整求解流程入口，依次运行 Q1、Q2、Q3、验证、报告生成和审计。
- `run_second_stage_optimization.py`：第二阶段优化流程入口，记录优化仪表盘、上下界 gap、验证器测试和最终提交检查。
- `report_generator.py`：根据结果 CSV 和验证报告生成技术报告草稿。
- `audit.py`：项目级最终审计程序。
- `requirements.txt`：运行所需 Python 依赖。

## 运行方式

从 `project_organized` 根目录运行：

```bash
python run_project.py
python run_project.py --second-stage
```

不建议在本目录内直接运行脚本，因为部分输出路径依赖项目根目录。
