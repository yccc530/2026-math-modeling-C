# C题：新能源汽车核心零部件三维装载与多点配送

这是一个可运行、可验证、可迭代的 Python 项目，覆盖题目四个问题：

- Q1：HeavyEV 单车三维装箱与重心控制。
- Q2：HeavyEV/LightEV 多车型、多站点配送与严格 LIFO。
- Q3：8 站点、20 规格模拟数据，严格 LIFO 与柔性 LIFO 对比。
- Q4：独立 `validator.py` 验证程序。

## 运行方式

在本目录执行：

```bash
python main.py
```

独立验证示例：

```bash
python validator.py --csv results/result_q2_loading.csv --mode strict
python validator.py --csv results/result_q3_loading_flexible.csv --mode flexible
```

## 输出目录

- `results/`：装载坐标、车辆方案、模拟数据、敏感性分析 CSV。
- `plots/`：三维装载图与对比图。
- `reports/`：验证报告、Q2 方案报告、技术报告草稿、最终审计报告。

## 方法说明

项目采用 extreme/corner point 三维装箱启发式、多排序策略、多随机种子、重心修正、站点集合覆盖和局部修复。优化结果表述为经验证程序检验通过的高质量可行解，不声称理论全局最优。

默认车辆配送后返回中心仓，即 `return_to_depot=True`；求解器函数保留该参数接口。

