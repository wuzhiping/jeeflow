# _stories/ · 案例与演示归档

> **目的**：存放「闭环自检 / 飞轮演示 / 季度回顾」等**时间点叙事**文档，与正式 plan 文件分离，避免新读者混淆。

## 文件清单

| 文件 | 类型 | 内容 |
|------|------|------|
| `_story_001_annual_leave.md` | 闭环自检 | 销售部小李请假 3 天 → 4 类 persona 联动 review + 12 个 doc 落地 |
| `_story_002_documentation_layering.md` | 架构变更 | 文档体系 3 层定位 + version-bump-guard 落地 |
| `_flywheel_demo_e2e.md` | 飞轮 E2E 演示 | 3 反馈 → 自动分流 → 100% 闭环，8 组件验证 |
| `_quarterly_retrospective_2026Q3.md` | 季度回顾 | 2026-09-18 → 2026-09-25（1 周冲刺）复盘 |

## 命名约定

`_` 前缀 = 「演示 / 案例 / 时间点叙事」, 不属于常规 plan 文件
`_stories/` 子目录 = 与正式 plan (`01-engine-developer.md` 等) 物理隔离

## 何时新增

- 季度回顾完成
- 闭环自检案例积累（故事 002+）
- 飞轮机制重大验证（演示 002+）
- **架构变更故事**（如故事 002：3 层定位 + version-bump-guard）