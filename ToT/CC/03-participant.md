# CC · 03 · 业务流程参与者 ⭐ 飞轮中枢

> **关键定位**：本 plan 是 4 个 plan 的**飞轮中枢（flywheel hub）**——参与者反馈是最高频的信号源；01/02/04 的多数行动由本 plan 的反馈触发。
>
> **North Star**：参与者自助解决率 ≥ 80%、任务平均时长 ≤ 30 秒。所有其他 plan 的成功，最终都通过这两个指标验证。

---

## 0. 为什么参与者是入口（Why this is the hub）

**参与者的真实使用，是系统最稠密的「压力测试」**：

| 信号 | 频率 | 可观测 |
|---|---|---|
| 每次操作结果 | 每天 ≥ 1000 次（公司全员）| `/wf/processTask/*` 日志 |
| 卡点/异常 | 每周 ≥ 5 起 | 内部 IM / 工单 |
| 建议/吐槽 | 季度 ≥ 20 条 | 季度 NPS / 反馈表 |
| 紧急 bug | 每月 ≥ 1 起 | P0 反馈 |

**对比其他 3 个 persona 的信号源**：

| Persona | 信号频率 | 信号类型 |
|---|---|---|
| 01 引擎开发 | 每周 1-2 次 release | 慢、滞后 |
| 02 流程设计 | 每月 2-3 个新流程 | 中频 |
| 03 参与者 | **每天 ≥ 1000 次操作 + ≥ 5 起卡点** | **最高频** ⭐ |
| 04 运维审计 | 事件驱动（稀疏）| 滞后 |

**结论**：参与者的反馈天然是「信号密度最高 + 延迟最低」的反馈源——飞轮的起点必然在此。

**代价**：参与者没有耐心写详细 issue。所以**飞轮的核心设计是降低上报摩擦**：
1. 5 分钟卡 + 决策树 + FAQ 解决 80%（自救）
2. 自助救不了 → 1 条 IM / 1 个工单（低摩擦上报）
3. CC maintainer 周一评审 → 分流到 01/02/04
4. 修复后 → 反馈到 FAQ → 下一轮自救率更高

---

## 1. Persona Profile

| 维度 | 内容 |
|---|---|
| 角色 | 全员（业务部 + 财务部 + HR ...）|
| 工具 | jeeFlow 前端 / 移动端 / curl（power user） |
| 痛点 | 找不到待办 / 不知道能不能委派 / 驳回到谁 / 历史找不回来 |
| 期望 | 5 分钟搞定一件事 / 出错了能自救 |
| 成功标志 | 任务完成时长 ≤ 30 秒（普通任务）/ 自助解决率 ≥ 80% |

---

## 2. Evidence（事实现状）

| 维度 | 数据 | 来源 |
|---|---|---|
| 参与者相关端点 | `/wf/processInstance/*` / `/wf/processTask/*` / `/wf/processDefine/*` | `main_common.py` + `main_pg.py` |
| 高频 actions | `processTask/todoList` / `processTask/execute` / `processTask/delegate` / `processInstance/startAndExecute` | `docs/actions.md` |
| 启动+执行入口 | `processInstance/startAndExecute` | `actions.md:20` |
| 待办列表 | `processTask/todoList` | `actions.md:32` |
| 任务委派 | `processTask/delegate`（字段名 `targetUserId`）| `actions.md:45` |
| 当前用户文档 | `ToT/docs/manual/06-start-and-approve.md`（一个文件）| `ls ToT/docs/manual/06-*` |
| FAQ 文档 | ❌ 无 | 缺失 |
| 5 分钟快速卡 | ❌ 无 | 缺失 |
| 异常场景手册 | `ToT/docs/manual/07-verify-and-troubleshoot.md` 偏技术向 | 缺口 |
| 移动端文档 | ❌ 无 | 缺失 |

---

## 3. 当前缺口（Gaps）

1. **缺「5 分钟快速卡」**：新人入职不知道从哪开始
2. **缺决策树**：委派 vs 加签 vs 转办的区别场景
3. **异常场景 FAQ 偏技术**：`manual/07-verify-and-troubleshoot.md` 是给运维看的，不是给普通员工
4. **移动端操作**：上游文档说支持但本仓无前端
5. **找不到待办**：UI 不熟时如何 `curl /wf/processTask/todoList` 没文档
6. **缺低摩擦上报通道**：参与者没有耐心写长 issue

---

## 4. 短期行动计划（4 周）

### A1. 5 分钟快速卡（Quick Start）
- **位置**：`ToT/CC/quickstart-card.md`（新建）
- **内容**：
  - 3 步走完一个流程：
    1. `POST /wf/processInstance/startAndExecute`（发起）
    2. `POST /wf/processTask/todoList`（查待办）
    3. `POST /wf/processTask/execute`（同意/驳回）
  - 字段表：operator / submitType / processTaskId / args
  - curl 示例 × 3（含 PG 端口 8102）
- **ETA**：W1 末
- **成功标准**：新员工 5 分钟能独立完成第一次提单

### A2. 决策树：委派 / 加签 / 转办
- **位置**：`ToT/CC/decision-tree.md`（新建）
- **内容**：
  ```
  你不在 → 同事临时处理？
    ├ 是，1-2 天内回来 ─── 委派（delegate，targetUserId）
    ├ 是，长期授权 ────── 转办（transfer，需修改定义）
    └ 需要多人会签 ───── 加签（addSign，需引擎支持）
  ```
  - 每个动作：API + 字段表 + 副作用（任务流向）
  - 反例：把「请假」委派给上级 → 上级看不到原任务
- **ETA**：W2 末
- **成功标准**：调研 3 个真实案例，每个走不同分支都能搞清

### A3. 异常场景 FAQ（10 个）
- **位置**：`ToT/CC/faq.md`（新建）
- **内容**（从历史 issue + 客服记录提炼）：
  - Q: 我点了同意但流程没动？→ 看 `processTask/execute` 返回的 `submitType` 是否匹配
  - Q: 找不到我的待办？→ `todoList` 返回 0 行，先确认 `operator` 字段
  - Q: 我能驳回到申请人吗？→ 看引擎是否支持「驳回任意节点」（BDD #1201 FIX-T 系列）
  - Q: 委派后还能收回吗？→ 不能，委派是永久的（除非重新委派）
  - Q: 抄送给我了但没任务？→ 抄送 = 仅通知，不在 `todoList` 里
  - Q: ... 共 10 个
- **ETA**：W3 末
- **成功标准**：80% 高频问题能在 FAQ 找到答案

### A4. 移动端快速操作卡（受限）
- **位置**：`ToT/CC/mobile-quickref.md`（新建）
- **内容**：
  - 本仓无前端 → 仅给「API 用户」移动端文档
  - 3 个 curl one-liner（用 `-d` + `jq`）：查待办 / 一键同意 / 一键驳回
  - shell 函数（贴到 `.bashrc`）：`jftodo` / `jfok` / `jfreject`
- **ETA**：W3 末
- **成功标准**：CLI user 在手机上能 30 秒完成审批

### A5. 任务历史找回指南
- **位置**：`ToT/CC/history-lookup.md`（新建）
- **内容**：
  - 我发起过的：`/wf/processInstance/myStarted?operator=user1`
  - 我审批过的：`/wf/processTask/myHistory?operator=user1`
  - 委派给我的：`/wf/processTask/delegatedToMe?operator=user1`
  - 抄送给我的：`/wf/processTask/ccToMe?operator=user1`（如存在）
  - 时间范围 + 状态过滤
- **ETA**：W4 末
- **成功标准**：员工找历史不再问 IT

### A6. 低摩擦反馈通道（飞轮润滑剂）
- **位置**：`ToT/CC/feedback/inbox.md`（共享收件箱）
- **动作**：
  - 在 `/wf/processTask/execute` 错误响应中嵌入「反馈这条错误」的链接（前端后续）
  - CLI 工具：执行失败时提示「是否记录到反馈？y/n」— ✅ `ToT/sop/jffeedback.py` 已建
  - 所有反馈自动归到 `feedback/03-participant-<seq>.md`
- **ETA**：W2 末 — ✅ CLI 部分完成（前端嵌入待续）
- **成功标准**：周均 ≥ 3 条反馈（基线 0）

---

## 5. 反馈闭环（Feedback Loop）

| 渠道 | 内容 | 频率 |
|---|---|---|
| `feedback/03-participant-<seq>.md` | 卡点 / 找不到 / 字段疑问 | 随时 |
| `support@` 邮件（公司内部） | 真实使用问题 | 每天 |
| 季度 NPS（5 题） | 体验打分 | 季度 |

**反馈处理 SLA**：
- P0（流程卡住所有人）：2h 内
- P1（个人卡点）：当天
- P2（建议）：季度评审

---

## 6. Success Metrics（量化）

| 指标 | 当前 | 目标（4 周末）|
|---|---|---|
| 5 分钟快速卡 | 0 | 1 个 doc |
| 决策树 | 0 | 1 个 doc |
| FAQ 覆盖 | 0 | ≥ 10 个问题 |
| 移动 CLI 卡 | 0 | 1 个 doc |
| 历史找回指南 | 0 | 1 个 doc |
| 任务平均完成时长 | 未知基线 | ≤ 30 秒 |
| **自助解决率** ⭐ | 未知基线 | ≥ 80% |
| **周均反馈量** | 0 | ≥ 3 条/周 |

---

## 7. 跨 Persona 引用

- ← 02-process-designer：好的模式让参与者体验更好（如会签四模式选择）
- ← 01-engine-developer：API 升级要兼容参与者常见调用方式
- → ToT/docs/manual/06-start-and-approve.md：完整版手册
- → ToT/docs/manual/07-verify-and-troubleshoot.md：异常排查（参与者精简版）
- → ToT/docs/guides/01-quick-start.md：技术快速开始
- **→ 触发 01/02/04 的入口**（见 §8 飞轮）

---

## 8. ★ 反馈飞轮（Flywheel）

```
                    ┌─────────────────────────────┐
                    │      03 参与者（飞轮中枢）    │
                    │  自助解决率 ↑ / 时长 ↓      │
                    └──────────┬──────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
   ┌─────────────────┐ ┌───────────────┐ ┌────────────────┐
   │ 01 引擎开发      │ │ 02 流程设计    │ │ 04 运维审计     │
   │ 修复 API bug     │ │ 改进模式      │ │ 优化监控/容量   │
   │ 加 SPI 实现      │ │ 加 KPI 字典   │ │ 配告警阈值     │
   └────────┬────────┘ └───────┬───────┘ └────────┬───────┘
            │                 │                  │
            └─────────────────┼──────────────────┘
                              ▼
                  ┌───────────────────────┐
                  │   release.sh v1.x.y    │
                  │   ── 自动 ship        │
                  └───────────┬───────────┘
                              ▼
                  ┌───────────────────────┐
                  │ 客户系统同步           │
                  │ /version + /healthz   │
                  └───────────┬───────────┘
                              ▼
                  ┌───────────────────────────┐
                  │ 参与者体验改善            │
                  │ ── 自助解决率 ↑          │
                  │ ── 反馈量 ↑（更多信号）  │
                  └───────────────────────────┘
                              │
                              └─────────────► 飞轮加速
```

**飞轮节奏（季度）**：

| Week | 03 主导 | 01/02/04 接收 |
|---|---|---|
| W1 | 收集上周反馈 + 验证 Q1-Q5 FAQ | 评审自己的 backlog |
| W2 | 更新 FAQ + 5 分钟卡 | 接收本周分流 |
| W3 | 季度 NPS 调研 | 执行分流到的行动 |
| W4 | release + 复盘飞轮 RPM | release + 同步到 03 |

**飞轮健康指标（飞轮 RPM = Revolutions Per Month）**：

| 指标 | 计算 | 当前 | 目标 |
|---|---|---|---|
| 月分流条目数 | `feedback/03-*` → 01/02/04 数 | 0 | ≥ 8 |
| 闭环率 | 已闭环条目 / 总条目 | N/A | ≥ 70% |
| 平均闭环时长 | ship → 写回 FAQ | N/A | ≤ 4 周 |
| 自助解决率 Δ | (本月 - 上月) | N/A | +5% |

---

## 9. ★ 分流矩阵（Triage Matrix）

参与者反馈 → 自动路由到对应 plan：

| 反馈标签 | 触发 plan | 典型例子 |
|---|---|---|
| `bug` + 涉及 `vendor/jeeflow/*.py` | → **01-engine-developer** | "执行 task 报 KeyError" |
| `bug` + 涉及 `main_*.py` 或端点 | → **01-engine-developer** | "/wf/processTask/execute 500 错误" |
| `design-issue` + 流程卡死/走错 | → **02-process-designer** | "会签任务所有人卡 3 天" |
| `design-issue` + 找不到合适模式 | → **02-process-designer** | "想做个 'N 选 M 审批' 没模式" |
| `process-gap` + KPI 不清晰 | → **02-process-designer** | "想知道流程平均时长" |
| `system-perf` + 卡顿超时 | → **04-ops-audit** | "提交后等了 30 秒" |
| `system-down` + 服务挂 | → **04-ops-audit** | "/healthz 返回 500" |
| `audit-trace` + 查不到链路 | → **04-ops-audit** | "想看某 instance 全链路" |
| `doc-gap` + FAQ 缺答案 | → **03-participant**（自身）| "不知道如何导出报表" |
| `ux-issue` + UI 难用 | → **03-participant**（自身）| "按钮位置不合理" |

**自动分流规则**（将由 `ToT/sop/feedback-triage.py` 实现）：
1. 读 `feedback/03-participant-*.md` 全部
2. 提取 `## 标签（Tags）` 一行
3. 命中上表 → 写入 `feedback/_routes/<plan>-<seq>.md`
4. 每周一自动 commit 到 git
5. CC maintainer 在 weekly review 看

**闭环回写**：
- 01/02/04 修复完成后 → 在对应 `feedback/_routes/<plan>-<seq>.md` 标注 `状态: 已闭环`
- 自动同步到 `feedback/03-participant-<seq>.md` 的 `## 闭环` 字段
- FAQ/5分钟卡/决策树 同步更新

---

## 10. 飞轮启动检查清单（首月必做）

- [ ] 建立 `feedback/_routes/` 目录 + `feedback-triage.py`
- [ ] 跑通一次：1 条反馈 → 自动分流到 01/02/04 → 闭环回写
- [ ] 公布反馈入口（IM 群 + 邮件）
- [ ] 第一周收集 ≥ 5 条反馈
- [ ] 第一次 release 后更新 FAQ（验证闭环）
- [ ] 第一个月复盘：飞轮 RPM 是多少？卡在哪？

---

## 11. 附录：本周飞轮状态（live）

| 项 | 当前 |
|---|---|
| 反馈总量 | 0 |
| 已分流 | 0 |
| 已闭环 | 0 |
| 自助解决率 | N/A |
| 月度 RPM | N/A |
| 季度 NPS | N/A |

> 此节每周一由 `ToT/sop/feedback-triage.py --report` 自动更新