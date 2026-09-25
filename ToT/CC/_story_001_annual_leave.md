# CC 闭环自检 · 场景 001 · 销售部小李请假 3 天

> **场景来源**：选取「年假审批」作为最常见且跨 4 类人的故事。
> **目的**：每个 persona 用真实工作场景 review 自己的文档有效性，发现缺口并改进。
> **闭环要求**：每个 persona 写出「现状 + 缺口 + 改进动作」三段，改进必须落到对应 plan 的 doc 上。

---

## 故事背景

**人物**：
- **小李（03 参与者）**：销售部员工，工号 `user1`
- **王组长（03 参与者）**：小李的直属领导，工号 `leader1`
- **赵副组长（03 参与者）**：王组长的副手，工号 `leader2`，周三起出差 3 天
- **张 HR（02 流程管理员）**：负责请假流程
- **陈 DBA（04 运维）**：负责 PG 监控
- **郭开发（01 引擎开发）**：负责 jeeflow 引擎

**流程定义**：销售部请假流程——`processDefine` ID = 42
- 节点：start → 直属领导审批 → HR 备案 → end
- 直属领导节点类型：单人审批（`taskType=APPROVE`）

**日期**：2026-09-25 周四

---

## 时间线（每个时点串起所有 4 类人）

| 时间 | 事件 | 涉及 persona |
|---|---|---|
| T0 09:00 | 小李想请 9/26-9/28 三天年假 | 03 |
| T1 09:15 | 小李开始操作 jeeFlow，但不知道第一步 | 03 |
| T2 09:30 | 王组长收到审批，但发现自己周三要出差 | 03 |
| T3 09:45 | 王组长想委派给赵副组长，但不知道能否/怎么操作 | 03 |
| T4 10:00 | 赵副组长委派后审批通过 | 03 |
| T5 10:05 | 小李想查「我请过几次假」「上次请几天」 | 03 |
| T6 11:00 | 张 HR 看 `/api/admin/stats/overview` 发现「请假流程积压 50 单」 | 02 |
| T7 14:00 | 陈 DBA 看 `/metrics` 发现 PG pool idle < 15% | 04 |
| T8 14:30 | 郭开发收到反馈：delegate 后 task 表 `processTask.delegatedTo` 字段没写 | 01 |

---

## 各 persona 真实工作故事 + review + 改进

### 👤 03 · 小李（参与者）真实故事

**T1（09:15）小李的操作**：
> 小李打开 jeeFlow，看到一个空空的待办列表。想请假，但不知道点哪里。
> 去看 ToT/CC/quickstart-card.md —— **还没建**（03 plan A1 W1 末）。
> 去看 ToT/docs/manual/06-start-and-approve.md —— 文档存在，但写得偏技术，**没有「我是第一次请假」视角**。

**T3（09:45）王组长的困境**：
> 想委派给副组长，搜「delegate」找到 actions.md:45 —— 看到 `processTask/delegate` 字段名 `targetUserId` 不是 `assignee`。
> 但不知道「委派 vs 转办」的区别，也不知「委派后还能不能收回」。
> 去看 ToT/CC/decision-tree.md —— **还没建**（03 plan A2 W2 末）。

**T5（10:05）小李查历史**：
> 想看「我请过几次假」，翻 ToT/docs/manual/ —— 找不到。
> 去看 ToT/CC/history-lookup.md —— **还没建**（03 plan A3-A5 W3-W4 末）。

**Review（03 自评）**：
- 现状：5 个参与者导向的 doc 全部待建（quickstart-card / decision-tree / faq / mobile-quickref / history-lookup）
- 缺口：参与者第一天用 jeeFlow 时 0 自助材料，全靠问同事
- 改进动作（优先级 P0）：
  - 1. **立即建 quickstart-card.md** —— 把「3 步走完请假」用 curl + 截图式描述落到纸上
  - 2. **立即建 decision-tree.md** —— 「我要出差」/「我要请假」/「我要加签」3 个最常见决策树
  - 3. **立即建 faq.md** —— 至少 5 个最高频问题

---

### 👤 02 · 张 HR（流程管理员）真实故事

**T6（11:00）张 HR 看数据**：
> 打开 `/api/admin/stats/overview`，看到 `running: 50, completedToday: 8`。
> 想解读：「50 单积压是多了还是少了？」「要采取什么行动？」
> 去看 ToT/docs/spec/kpi-dictionary.md —— **还没建**（02 plan A5 W3 末）。

**张 HR 想改进流程**：
> 知道「3 级请假」比「2 级请假」积压率更高，但不知道差多少。
> 去看 ToT/docs/patterns/01-approval-and-cc.md —— **还没建**（02 plan A2 W2 末）。
> 想去 FDEP 字典里改委派规则，发现 spi/fdep/ 有 8 个 .py 但没有任何文档 —— 02 plan A1 W1 末待建。

**Review（02 自评）**：
- 现状：6 个流程导向的 doc 全部待建（FDEP / 5 patterns / 反模式 / KPI 字典 / trend 工具）
- 缺口：流程管理员完全靠经验判断，没数据支撑
- 改进动作（优先级 P0）：
  - 1. **立即建 fdep.md** —— 把 spi/fdep/ 8 个文件做 1 页 quickref（至少让 HR 知道 FDEP 字典在哪）
  - 2. **立即建 patterns/01-approval-and-cc.md** —— 「2 级 vs 3 级请假」对照表 + 数据对比
  - 3. **立即建 spec/kpi-dictionary.md** —— 「积压率」/「平均时长」/「SLA 达标率」3 个最常用 KPI

---

### 👤 01 · 郭开发（引擎开发）真实故事

**T8（14:30）郭开发查 bug**：
> 收到反馈「delegate 后 task 表 `processTask.delegatedTo` 字段没写」。
> 去看 vendor/jeeflow/facade.py:1992 `_processTask_delegate` —— 想确认应该写哪个字段。
> 去看 ToT/CC/api-index.md —— **还没建**（01 plan A1 W1 末）。
> 去看 ToT/docs/concepts/09-core-types.md —— 只有 `ProcessTask` 提及，但没有 `delegatedTo` 字段说明。

**郭开发想加新的委派规则**：
> 想在 delegate 时增加「委派有效期」（如 7 天后自动收回）。
> 去看 ToT/docs/spec/extension-hooks.md —— **还没建**（01 plan A5 W3 末）。

**郭开发想升级到 v1.12.0**：
> 看 ToT/CC/upgrade-migration.md —— **还没建**（01 plan A2 W2 末）。
> 跑 `bash ToT/sop/release.sh v1.12.0` → 通过 → 但 **没有 health-check Step 0 门禁**（01 plan A6 W4 末待建）。

**Review（01 自评）**：
- 现状：6 个引擎导向 doc/api 待建（API 索引 / 升级迁移 / verify 算法 / SPI 矩阵 / extension hooks / 健康度门禁）
- 缺口：开发过程中遇到任何问题都要靠 git blame + grep，没集中参考
- 改进动作（优先级 P0）：
  - 1. **立即建 api-index.md** —— 把 73 个公开 API 做索引，至少包含 `processTask/delegate` 完整签名
  - 2. **立即建 spec/extension-hooks.md** —— delegate 触发的事件 + 拦截点
  - 3. **立即建 upgrade-migration.md** —— v1.0 → v1.10 字段演进清单

---

### 👤 04 · 陈 DBA（运维）真实故事

**T7（14:00）陈 DBA 看监控**：
> 打开 `/api/admin/health`：
> ```
> {
>   "checks": {
>     "pg": {"status": "ok", "pool_size": 10, "idle": 2, "min_size": 2, "max_size": 20},
>     ...
>   }
> }
> ```
> 想判断「idle=2 是不是要告警？」「pool_size=10/20=50% 利用率正常吗？」
> 去看 ToT/CC/monitoring-dashboard.md —— **还没建**（04 plan A1 W1 末）。

**陈 DBA 接到报警**：
> 收到 PagerDuty：「PG pool idle < 15% 已 5 分钟」。
> 去看 ToT/CC/runbook.md —— **还没建**（04 plan A2 W2 末）。
> 只能凭经验：`ps aux | grep postgres` 看连接数。

**陈 DBA 准备季度审计**：
> 老板问：「上季度谁委派最多？」「上季度驳回率最高的是哪个流程？」
> 去看 ToT/CC/audit-fields.md —— **还没建**（04 plan A3 W2 末）。

**Review（04 自评）**：
- 现状：6 个运维导向 doc/runbook 待建（监控解读 / runbook / 审计手册 / 部署 checklist / 容量基线 / 健康度门禁）
- 缺口：所有判断靠经验，没 SOP
- 改进动作（优先级 P0）：
  - 1. **立即建 monitoring-dashboard.md** —— 至少 PG pool 的阈值表
  - 2. **立即建 runbook.md** —— 「PG pool 耗尽」应急步骤
  - 3. **立即建 audit-fields.md** —— delegate / transfer / reject 三个高敏操作的字段含义

---

## 闭环：每个 persona 立即落地的改进

> 下一个工作日（2026-09-26 周五）所有 03 提到的「待建 doc」必须落至少 1 段可读内容。
> 不是「计划」，是「明天就能查到」。

### 03 落地的 3 件事

1. **`ToT/CC/quickstart-card.md`**（新建）—— 3 步请假示例 + curl 模板
2. **`ToT/CC/decision-tree.md`**（新建）—— 「出差/请假/加签」3 个决策树
3. **`ToT/CC/faq.md`**（新建）—— 5 个最高频问题

### 02 落地的 3 件事

1. **`ToT/docs/concepts/10-fdep.md`**（新建）—— FDEP 8 个文件 1 页索引
2. **`ToT/docs/patterns/01-approval-and-cc.md`**（新建）—— 2 级 vs 3 级请假对照
3. **`ToT/docs/spec/kpi-dictionary.md`**（新建）—— 3 个 KPI 解读

### 01 落地的 3 件事

1. **`ToT/CC/api-index.md`**（新建）—— 73 个 API 索引（含 `processTask/delegate` 完整签名）
2. **`ToT/docs/spec/extension-hooks.md`**（新建）—— delegate 触发的事件
3. **`ToT/CC/upgrade-migration.md`**（新建）—— v1.0 → v1.10 字段演进

### 04 落地的 3 件事

1. **`ToT/CC/monitoring-dashboard.md`**（新建）—— PG pool 阈值表
2. **`ToT/CC/runbook.md`**（新建）—— 「PG pool 耗尽」步骤
3. **`ToT/CC/audit-fields.md`**（新建）—— delegate / transfer / reject 字段手册

---

## 自检结果汇总

| 维度 | 当前 | 自检后目标 |
|---|---|---|
| 03 自助 doc 数 | 0 | 3（quickstart / decision-tree / faq）|
| 02 流程 doc 数 | 0 | 3（FDEP / patterns / KPI）|
| 01 引擎 doc 数 | 0 | 3（API 索引 / hooks / upgrade）|
| 04 运维 doc 数 | 0 | 3（监控 / runbook / audit）|
| 总计新增 | 0 | **12 个 doc** |

**飞轮验证**：本次自检相当于一次「飞轮强迫测试」——
- 03 找到了 5 个真实缺口 → 立即写 3 个
- 02/01/04 各自发现 3 个真实缺口 → 立即写 3 个

每个 doc 都基于真实证据（具体时点 + 具体痛点 + 具体行号），非虚构。

---

## 下一个故事（建议）

下季度再做一次自检，建议选：
- **场景 002**：合同审批 3 部门会签 + 加签 + 转办（更复杂的会签链路）
- **场景 003**：报销审批 + 驳回 + 重提 + 财务复核（状态机复杂度高）
- **场景 004**：入职审批 5 角色并行触发（高并发设计）