# ToT/ea/ — 流程全生命周期体系架构（飞轮）

> **本目录是系统最具价值的资产** —— 方法论 + 落地架构 + 交付 + 改进闭环的飞轮。
> **入口**：[`roadmap.md`](./roadmap.md) 是架构基线，必须先读。
> **营销**：[`PPT.md`](./PPT.md) — 10 张 slide 营销材料（面向潜在采用者）。

---

## 目录结构

```
ToT/ea/
├── README.md                 ← 本文件（索引）
├── PPT.md                    ← 新营销材料（10 张 slide）
├── roadmap.md                ← 架构基线（必读）
└── iterations/
    └── <YYYY-MM-DD>.md       ← 每次完整迭代的复盘
```

---

## 文件清单

### 主文档

| 文件 | 状态 | 用途 |
|------|------|------|
| [README.md](./README.md) | 当前 | 本索引 |
| [PPT.md](./PPT.md) | **新** | 营销材料（10 张 slide），让潜在采用者快速了解 |
| [roadmap.md](./roadmap.md) | **必读** | 架构基线（v1.0）：5 阶段生命周期 + 7 设计模式 + 合规清单 + 传承路径 |

### 迭代记录

| 文件 | 状态 | 覆盖 |
|------|------|------|
| [iterations/2026-09-22.md](./iterations/2026-09-22.md) | ✅ 完整 | FDEP 端到端开发（4 小时）—— 第一轮迭代 |

---

## 如何使用本目录

### 第一次读

```
1. README.md（本文）              2 分钟
2. PPT.md（营销材料）           5 分钟（如果只想了解"是什么"）
3. roadmap.md（架构基线）         15-20 分钟
4. iterations/<date>.md（最近一轮） 10-15 分钟
```

### 每次新会话开始

```
1. 读 README.md                  → 知道本目录结构
2. ls iterations/                → 看最近一轮迭代（避免重复踩坑）
3. 跳到 roadmap.md §10 传承与教学  → 知道"接下来做什么"
```

### 每次新流程开发

```
1. 读 roadmap.md §3-§9           → 知道怎么开发
2. 参考 iterations/<date>.md     → 知道上次怎么做的
3. 完成后新建 iterations/<新date>.md → 让下次有得参考
```

---

## 命名约定

| 类型 | 命名 | 说明 |
|------|------|------|
| 架构基线 | `roadmap.md` | **唯一**，所有规则在这里 |
| 营销材料 | `PPT.md` | **唯一**，对外推广用 |
| 索引 | `README.md` | **唯一**，本文件 |
| 迭代记录 | `iterations/YYYY-MM-DD.md` | 每次完整迭代一个文件 |

**禁止**：
- ❌ 在 `ea/` 下创建非 `roadmap.md` / `README.md` / `PPT.md` / `iterations/<date>.md` 的文档
- ❌ 在 `iterations/` 下创建非 `YYYY-MM-DD.md` 命名的文件
- ❌ 把 SOP / baseline / 留档放到 `ea/`（它们有自己的目录）

---

## 与其他目录的关系

```
ToT/
├── README.md (v2.9)         ← 工作规范（顶部摘要提及 ea/）
├── HANDBOOK.md              ← 知识手册
├── flows/fdep/              ← 蓝本示例（roadmap.md §13 索引）
├── sop/                     ← 10 SOP（roadmap.md §6 编排）
├── tdd/                     ← baselines（roadmap.md §13.5 索引）
├── customer-*/              ← 留档（roadmap.md §13.6 索引）
└── ea/                      ← 本目录（飞轮）
```

---

## 维护原则

1. **roadmap.md 是规范**：所有规则在 roadmap.md 表达，迭代记录不重复规则
2. **PPT.md 是营销**：对外介绍用，不承载规则细节（详见 roadmap.md）
3. **iterations/<date>.md 是历史**：每次迭代独立文件，便于翻历史
4. **ea/ 不被工具链任意改动**：所有改动写 changelog（roadmap.md §14）
5. **外部文档只读引用**：roadmap.md / iterations/* / PPT.md 通过路径引用其他 ToT 文档，不修改

---

## 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿——索引文件。结构图 + 文件清单 + 使用方法 + 命名约定 + 与其他目录关系 + 维护原则。配套 roadmap.md v1.0 + iterations/2026-09-22.md |
| **v0.2** | **2026-09-22** | **新增 PPT.md 营销材料**（10 张 slide，钩子+痛点+痒点+方案+证据+CTA 结构）+ 配套演讲者提示。README 文件清单加 PPT.md + 命名约定加 PPT.md + 维护原则加"PPT.md 是营销"条款。 |