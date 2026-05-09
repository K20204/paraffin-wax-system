# 石蜡配方设计系统

基于 Python Flask + Bootstrap 5 + SQLite 的石蜡配方设计与计算桌面 Web 应用。

## 功能

- **原料管理** — 10 种石蜡原料的增删改查（熔点、含油量、针入度、粘度、颜色、成本）
- **性能预测** — 选定原料和配比，预测混合后的各项物性指标
- **配比计算** — 给定目标物性值，反向计算 2~3 种原料的最佳配比
- **配方优化** — 设定目标范围，优化求解满足所有约束的原料比例
- **配方管理** — 创建、编辑、保存完整配方

## 快速开始

```bash
pip install flask
python app.py
```

浏览器打开 **http://localhost:5000**。

## 混合模型

| 属性 | 模型 | 说明 |
|------|------|------|
| 熔点 | 线性 | P_blend = Σ(wi · Pi) / Σ(wi) |
| 含油量 | 线性 | 同上 |
| 颜色 | 线性 | 同上 |
| 针入度 | 对数 | ln(P) = Σ(wi · ln(Pi)) / Σ(wi) |
| 粘度 | 对数 | 同上 |

- N=2 时使用解析解，N≥3 时使用投影梯度下降 + 单纯形投影

## 项目结构

```
app.py               Flask 应用入口
config.py            配置常量
database.py          数据库初始化与连接管理
seed_data.py         种子数据（10 种石蜡原料）
engine/              核心计算引擎
  mixing_models.py     线性/对数混合模型
  calculator.py        预测、配比计算、优化
  simplex_projection.py 单纯形投影算法
routes/              API 蓝图
templates/           Jinja2 模板
static/              前端资源 (Bootstrap 5)
```

## 技术栈

- **后端**: Python 3 + Flask
- **前端**: Bootstrap 5 + 原生 JavaScript
- **数据库**: SQLite
- **计算**: NumPy-free，纯 Python 实现梯度下降
