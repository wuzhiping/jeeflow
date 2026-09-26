# ToT/GETTING_STARTED.md — 新用户 5 分钟入门

> **目的**：让任何人**快速找到**自己需要的入口（不论你是流程设计师 / 审计员 / 部署员 / 文档撰写员）
> **设计**：1 文档 4 角色 4 路径 —— 按你的"角色"直接跳到对应入口
> **不替代** `roadmap.md` / `HANDBOOK.md` / SOP —— 那些是深入文档；本文只是"导航"

---

## 1. 你是什么角色？（30 秒）

| 我是... | 我想... | 跳到 |
|---------|---------|------|
| **🟢 流程设计师** | 设计新流程 | §2.1 |
| **🟡 流程审计员** | 检查流程完整性 / 找缺失 | §2.2 |
| **🔵 部署运维员** | 部署 / 重置 / 切换环境 | §2.3 |
| **🟣 文档撰写员** | 写流程 README / NODES / Job Cards | §2.4 |
| **⚫ 其他**（学习 / 复盘 / 演进）| 了解整体 | §3 通用路径 |

---

## 1.5 零配置使用（v2.17 新增）

> **所有 SOP 命令无需 `cd` 到项目根、无需 export 环境变量！**

```bash
# 方式 A（推荐单命令）—— 无需任何前置
./ToT/bin/jf python3 ToT/sop/ea-compliance.py
./ToT/bin/jf python3 ToT/sop/flow_completeness.py ToT/flows/fdep.json
./ToT/bin/jf python3 ToT/sop/promote.py list

# 方式 B（长时间会话）—— 在 .bashrc 加一行
echo 'source ~/projects/jeeFlow/ToT/bin/with-jf.sh' >> ~/.bashrc
# 之后会话内：REPO_ROOT 自动导出，所有命令直接可用

# 方式 C（已 cd 到项目根）—— 最朴素
cd /path/to/project
python3 ToT/sop/ea-compliance.py
```

**当前状态**：43/43 PASS（§9.9 自动化 4/4 + §9.8 路径可移植性 4/4）。

### 1.6 ToT/docs/ 知识体系（v2，2026-09-18+）

> **重要**：本节是 ToT/docs/ 与本文档的协同说明。
> 遇到术语不明 / API 签名不确定 / 与上游约定差异 → 进 `ToT/docs/`。

| 角色 | 主入口 | 受众 |
|------|--------|------|
| **任意角色** | [`ToT/docs/README.md`](./docs/README.md) | ToT/docs/ 文档地图 |
| **任意角色** | [`ToT/docs/REPORT.html`](./docs/REPORT.html) | 健康度可视化（100/100 🟢）|
| **流程设计师** | `ToT/docs/concepts/`（10 文件）| 设计原理 |
| **流程设计师** | `ToT/docs/patterns/`（5 文件）| 模式库 |
| **开发者** | `ToT/docs/spec/`（11 文件）| 数据模型 + API |
| **参与者** | [`ToT/CC/quickstart-card.md`](./CC/quickstart-card.md) | 5 分钟卡 |
| **参与者** | [`ToT/CC/decision-tree.md`](./CC/decision-tree.md) | 决策树 |
| **运维** | [`ToT/CC/monitoring-dashboard.md`](./CC/monitoring-dashboard.md) | 监控解读 |
| **运维** | [`ToT/CC/runbook.md`](./CC/runbook.md) | 5 故障场景 |
| **AI Agent** | [`ToT/skills/flow-operator/SKILL.md`](./skills/flow-operator/SKILL.md) | 流程执行技能 |

**当前健康度**：100/100 🟢（drift 0/146 · API 73/73 覆盖 · 飞轮首次 E2E 演示通过）

---

## 2. 角色专属路径（按需看）

### 2.1 🟢 流程设计师路径

> **目标**：从"我有模糊需求"到"能跑通的流程"

```
Step 1: 读 ToT/sop/flow-design.md (10 分钟)
        → 知道设计原则：先跑通，再严谨

Step 2: 跑 flow_designer.py
        → 5 问生成 flow.json 草稿
        $ python3 ToT/sop/flow_designer.py

Step 3: 部署到引擎
        $ python3 -m uvicorn main:app --port 8101
        (auto-deploy 会自动 deploy ToT/flows/<flow>.json)

Step 4: 启动一个实例 + 跑到底
        $ curl ... /wf/processDefine/startAndExecute ...
        $ curl ... /wf/processTask/execute ... (循环到 DONE)

Step 5: 跑 completeness 看分
        $ python3 ToT/sop/flow_completeness.py ToT/flows/<flow>.json
        → 0-100% 打分 + 下一步建议

Step 6: 按建议补严谨（按需）
        - README/ROLES/NODES/CHANGELOG (P1)
        - RESPONSES + Job Cards (P2)
        - tdd-flow.py baseline (P3)
```

**关键文档**：`ToT/sop/flow-design.md`
**关键工具**：`flow_designer.py` + `flow_completeness.py`
**预期时间**：30 分钟到"可文档化"（50% 分）

---

### 2.2 🟡 流程审计员路径

> **目标**：检查流程完整性 + EA 合规 + 找缺失项

```
Step 1: 跑 flow_completeness.py
        $ python3 ToT/sop/flow_completeness.py ToT/flows/<flow>.json
        → 6 层 31 项打分（流程 / Job Card / 基线 / 运维 / 飞轮 / 配置）
        → 0-100% + 4 级评级（🔴<30% / 🟡30-60% / 🟢60-90% / ✅>90%）
        → 下一步建议（按权重排序）

Step 2: 跑 ea-compliance.py
        $ python3 ToT/sop/ea-compliance.py
        → 5 层 31 项 EA 合规（流程级 / Job Card / 基线 / 运维 / 飞轮）
        → 已含 §C1-C6 用户流程子集

Step 3: 看 roadmap §9 合规清单
        ToT/ea/roadmap.md §9 — 完整清单（27+4 项）
        → 与运行结果对照

Step 4: 看迭代记录找历史问题
        ToT/ea/iterations/  — 4 个迭代记录
        → 知道哪些坑被踩过
```

**关键文档**：`ToT/ea/roadmap.md §9 合规清单`
**关键工具**：`flow_completeness.py` + `ea-compliance.py`
**预期时间**：10 分钟跑出全报告

---

### 2.3 🔵 部署运维员路径

> **目标**：部署 / 重置 / 切换环境 / 处理 issue

```
A. 部署到客户服务器
   Step 1: 编辑 ToT/config/servers.json 改 active 字段
   Step 2: 人工 push 引擎代码到 abc.feg.cn
   Step 3: 人工重启 jeeflow 服务
   Step 4: AI 跑 reset + deploy + smoke test（详见 customer-data-reset.md §8）

B. 切换默认环境
   Step 1: $EDITOR ToT/config/servers.json
   Step 2: 改 "active" 字段（local-memory / local-pg / customer-test）
   Step 3: $ python3 ToT/sop/server_config.py --list 验证

C. 重置客户数据
   $ python3 ToT/sop/customer-data-reset.md   # 一键命令在 §8

D. 处理 issue（FDEP 元闭环）
   $ python3 ToT/sop/issue_link.py \
       --instance <原 instance id> \
       --reason "..." --severity high
   → 自动创建 fdep 实例处理 issue
   → fdep 走完 stage_review+end = bug 关闭

E. 清场（新会话）
   $ python3 ToT/sop/new-trip.md           # 清 tdd/
   $ python3 ToT/sop/clean-customer-data.md # 清 customer-* 留档
```

**关键文档**：`ToT/config/servers.json`（直接编辑）+ `ToT/sop/customer-data-reset.md` + `ToT/sop/flow-design.md §3 Step 5`
**关键工具**：`server_config.py --list`（验证）+ `issue_link.py`
**预期时间**：3 分钟切换环境，10 分钟处理 issue

---

### 2.4 🟣 文档撰写员路径

> **目标**：为流程写完整文档（README / ROLES / NODES / Job Cards）

```
A. 写 README.md（流程总览）
   模板：ToT/flows/fdep/README.md（5 节模板）
   必须含：流程概览 / 节点清单 / 角色清单 / 变更记录 / Job Card 模板 §5

B. 写 ROLES.md / NODES.md / CHANGELOG.md
   §10 永久规则：4 文件齐全 + 文件名小写
   模板参考：ToT/flows/fdep/{ROLES,NODES,CHANGELOG}.md

C. 写 Job Cards
   $ python3 ToT/sop/gen-job-cards.py --force
   → 自动从 fdep.json + NODES.md + RESPONSES.md §X.2.1 生成
   → 每节点 1 张 8 节卡

D. 写 RESPONSES.md（Decision Mem 模板）
   协议见 ToT/ea/roadmap.md §5 Pattern 2
   每节点 §X.2.1 模板（5 字段：decision_reason / decision_memo / context / job_card_url / next_handoff）

E. §10 合规检查
   $ python3 ToT/sop/flow_completeness.py ToT/flows/<flow>.json
   → 缺什么一目了然
```

**关键文档**：`ToT/flows/fdep/README.md`（模板）
**关键工具**：`gen-job-cards.py`
**预期时间**：1 小时写完整 5 文件 + 6 张卡

---

## 3. 通用路径（5 分钟懂整体）

### Step 1 · 30 秒懂（30 秒）

读 [`ToT/HANDBOOK.md`](./HANDBOOK.md)：
- 一张架构图
- 三环境介绍
- 快速开始

### Step 2 · 架构基线（5 分钟）

读 [`ToT/ea/roadmap.md`](./ea/roadmap.md)：
- 14 节：飞轮定位 / 5 原则 / 5 阶段 / 3 制品层 / 10 模式 / 13 SOP / 3 环境 / 迭代机制 / 31 项合规 / 传承教学 / 路线图 / 风险
- **§10 在路上**：下一步具体做什么
- **§9 合规清单**：怎么验证

### Step 3 · 看蓝本（3 分钟）

[`ToT/flows/fdep/`](./flows/fdep/) —— 一个完整流程的所有制品：
- `fdep.json`（Snaker 格式定义）
- `README.md` / `ROLES.md` / `NODES.md` / `CHANGELOG.md` / `RESPONSES.md`（5 文件）
- `job_cards/*.md` × 6（每节点执行器手册）

### Step 4 · 跑 2 个演示（2 分钟）

```bash
# 演示 1：5 问设计
python3 ToT/sop/flow_designer.py --demo --name my-test

# 演示 2：完整性打分
python3 ToT/sop/flow_completeness.py ToT/flows/expense-approval.json
# → 50% 🟡
python3 ToT/sop/flow_completeness.py ToT/flows/fdep.json
# → 100% ✅
```

---

## 4. 工具速查（按场景找工具）

| 我想做... | 工具 | 命令 |
|-----------|------|------|
| **设计流程** | `flow_designer.py` | `python3 ToT/sop/flow_designer.py` |
| **检查完整性** | `flow_completeness.py` | `python3 ToT/sop/flow_completeness.py <flow>.json` |
| **跑 TDD / 生成 baseline** | `tdd-flow.py` | `python3 ToT/sop/tdd-flow.py <flow>.json` |
| **EA 合规自验证** | `ea-compliance.py` | `python3 ToT/sop/ea-compliance.py` |
| **生成 Job Cards** | `gen-job-cards.py` | `python3 ToT/sop/gen-job-cards.py --force` |
| **处理 issue**（FDEP 元闭环）| `issue_link.py` | `python3 ToT/sop/issue_link.py --instance <id>` |
| **切换服务器环境** | `servers.json` | 编辑 `ToT/config/servers.json` 改 `active` |
| **重置客户数据** | `customer-data-reset.md` | §8 一键命令清单 |
| **清场（新会话）** | `new-trip.md` / `clean-customer-data.md` | 跑 2 个 SOP |
| **查看所有 SOP** | `ToT/sop/` | 13 个 .md + 7 个 .py |

---

## 5. 详细文档索引（点哪去哪）

### 顶层文档

| 文档 | 用途 | 何时读 |
|------|------|--------|
| [`ToT/README.md`](./README.md) | 工作规范（v2.13） | **必读第 1 份** |
| [`ToT/HANDBOOK.md`](./HANDBOOK.md) | 30 秒懂 jeeFlow | **必读第 2 份** |
| [`ToT/mapping.md`](./mapping.md) | R 角色 ↔ SPI ↔ 用户映射 | 写新流程时查 |

### EA 飞轮（元方法论）

| 文档 | 用途 | 何时读 |
|------|------|--------|
| [`ToT/ea/README.md`](./ea/README.md) | EA 索引 | 第一次接触 EA |
| [`ToT/ea/roadmap.md`](./ea/roadmap.md) | 架构基线（v1.3） | **必读第 3 份** |
| [`ToT/ea/PPT.md`](./ea/PPT.md) | 营销材料（10 张 slide） | 对外推广时 |
| [`ToT/ea/iterations/`](./ea/iterations/) | 4 个迭代记录 | 了解演进路径 |

### SOP 集（13 个）

详见 [`ToT/sop/`](./sop/) 目录，常用：

| 文档 | 用途 |
|------|------|
| `flow-design.md` | 用户流程设计引导（**新用户必读**）|
| `flow-folder.md` | 流程文件组织规范 |
| `tdd-flow.md` | 流程 TDD |
| `customer-data-reset.md` | 客户数据 reset |
| `server_config.py`（无对应 .md）| 环境配置管理：直接看 `ToT/config/servers.json` |
| `ea-compliance.py`（无对应 .md）| EA 合规检查 SOP：直接看脚本输出 |

### 示例与流程

| 文档 | 用途 |
|------|------|
| [`ToT/flows/fdep.json`](./flows/fdep.json) | 蓝本定义（100% 评分）|
| [`ToT/flows/fdep/`](./flows/fdep/) | 蓝本完整制品 |
| [`ToT/flows/expense-approval.json`](./flows/expense-approval.json) | 用户流程示例（50% 评分）|

### 测试与运维

| 文档 | 用途 |
|------|------|
| [`ToT/tdd/`](./tdd/) | Baselines（v0.6.2 / v1 / v2 / v3）|
| [`ToT/customer-resets/`](./customer-resets/) | reset 留档 |
| [`ToT/customer-checks/`](./customer-checks/) | 健康检查留档 |

---

## 6. 常见场景速查（FAQ 风格）

### Q1：我是新人，第一天该做什么？

```
1. 读 ToT/README.md 顶部摘要（2 分钟）
2. 读 ToT/HANDBOOK.md（5 分钟）
3. 读 ToT/ea/roadmap.md §10 传承与教学（5 分钟）
4. 跑 python3 ToT/sop/flow_designer.py --demo（2 分钟）
5. 看 ToT/flows/fdep/ 蓝本（10 分钟）
合计: 25 分钟上手
```

### Q2：我接到一个新流程需求怎么办？

```
1. 跑 flow_designer.py（5 问）
2. 部署 + 跑通最小闭环
3. 跑 flow_completeness.py 看 0-100%
4. 按"下一步建议"逐项补（按业务需求）
5. 跑 tdd-flow.py 生成 baseline
合计: 半天一个可用流程
```

### Q3：流程出 bug 怎么办？

```
1. 跑 issue_link.py --instance <id> --reason "..."
2. → 自动创建 fdep 实例处理
3. → fdep 走完 stage_review+end = bug 关闭
4. 在 ToT/ea/iterations/ 记录这个 issue + 经验
合计: 30 分钟一个 issue 闭环
```

### Q4：客户服务器 URL 变了怎么办？

```
1. 编辑 ToT/config/servers.json（改对应 server 的 url）
2. python3 ToT/sop/server_config.py --list 验证
3. python3 ToT/sop/ea-compliance.py 跑 §9.6 检查
合计: 1 分钟
```

### Q5：飞轮怎么继续转？

```
1. 每次重大迭代结束：写 ToT/ea/iterations/<date>_<purpose>.md
2. 跑 ea-compliance.py 自查（31/31 PASS）
3. 更新 ToT/ea/roadmap.md §14 changelog
4. 更新 ToT/README.md §8 changelog
合计: 30 分钟一次飞轮转动
```

---

## 7. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-22** | **新用户发现入口**：1 文档 4 角色 4 路径 + 通用 5 分钟入门 + 工具速查 + 详细索引 + FAQ。解决"用户如何获取工作模式说明"的发现性需求。 |
| **v0.2** | **2026-09-22** | **零配置使用**：新增 §1.5 —— jf wrapper / with-jf.sh / cd 3 种姿势任选；用户无需 `export REPO_ROOT` 即可跑所有 SOP 命令。 |