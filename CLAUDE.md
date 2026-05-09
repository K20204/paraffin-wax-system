# CLAUDE.md

石蜡配方设计系统 — Python Flask + Bootstrap 5 + SQLite 桌面 Web 应用。

## 运行

```
cd D:\paraffin-wax-system
python app.py
# 浏览器打开 http://localhost:5000
```

依赖：仅 `flask`（pip install flask）。

## 架构

```
app.py              Flask 应用入口 + 页面路由
config.py           配置常量（数据库路径等）
database.py         SQLite 初始化 + 连接管理 + 种子属性配置
seed_data.py        种子数据（10 种石蜡原料）
engine/             核心计算引擎
  mixing_models.py     线性/对数混合模型
  calculator.py        WaxCalculator: predict(), calculate_ratios(), optimize()
  simplex_projection.py 单纯形投影算法
routes/             API 蓝图
  materials.py        /api/materials CRUD
  formulas.py         /api/formulas CRUD
  calculate.py        /api/calculate/{predict,ratio,optimize}
  properties.py       /api/properties CRUD
templates/          Jinja2 模板（7 个页面）
static/             前端资源
  js/api.js           fetch 封装
  js/app.js           导航 + toast + 工具函数
  css/style.css       自定义样式
```

## 数据库表

- **property_configs**: 属性元数据（property_key, display_name, unit, mixing_model, min/max）
- **materials**: 石蜡原料（固定列: melting_point, oil_content, penetration, viscosity, color, cost_per_kg）
- **formulas**: 配方主表
- **formula_items**: 配方明细（formula_id, material_id, ratio）

## 混合模型

- 线性: `P_blend = Σ(wi * Pi) / Σ(wi)` — 熔点、含油量、颜色
- 对数: `ln(P) = Σ(wi * ln(Pi)) / Σ(wi)` — 针入度、粘度
- N=2 时解析解，N≥3 时投影梯度下降 + 单纯形投影

## 测试

启动应用后：
1. 仪表盘 — 确认原料/配方统计正确
2. 原料管理 — 添加、编辑、删除
3. 性能预测 — 选 2 种原料各 50%，验证熔点预测 = 平均值
4. 配比计算 — 选 3 种原料 + 目标值，验证配比和为 100%
5. 配方优化 — 设目标范围，验证返回结果在范围内
6. 配方管理 — 创建 → 添加原料 → 调整比例 → 保存
