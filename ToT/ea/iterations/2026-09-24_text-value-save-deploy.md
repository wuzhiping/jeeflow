# Iteration #35 · 2026-09-24 · W43 · text.value 简化 + save/deploy 双层结构发现

> **驱动**：用户希望简化 fdep.json node 的 text.value（括号补充信息啰嗦无意义）；最终发现 engine 设计层与部署层解耦的机制
> **核心成果**：✅ **text.value 简化原则（flow-design §2.3）** + **save vs deploy 双层结构澄清** + **customer-test v1→v3 active 全链路同步**

---

## 1. 时间线（~3 小时 / 6 步）

| 时段 | 工作 |
|------|------|
| 0~10 min | 原则讨论：3 轮收敛到"任务说清楚就足够" |
| 10~25 min | 应用原则简化 fdep.json 6 个 task.text.value |
| 25~45 min | 验证本地：deploy + 重启 engine + tdd-flow + ea-compliance |
| 45~80 min | deploy 到 customer-test (v2 simplify + 排查旧代码） |
| 80~120 min | **核心发现**：processDesign/listByType vs processDefine/deploy 双层结构 + version 字段在 content 内 |
| 120~180 min | 同步推进 version 0.6.1 → 0.6.2 + git commit + push + customer git pull + v3 active |

---

## 2. 原则 B · text.value 极简

### 2.1 表述（写入 flow-design.md §2.3）

> **任务说清楚就足够**。`node.text.value` 只描述"这个节点做什么任务"。

**规则**：
- ✅ 允许：节点阶段名（如 "1. RML 立项"）、任务简称（如 "0. 接收/登记"）
- ❌ 避免：角色分配说明（`u_fdp_pm 直接`）、SPI 角色代号（R3）、未来 TODO（待 v0.7+ 用 assignmentHandler）
- ❌ 避免：括号补充说明

**元信息归宿**：

| 信息类型 | 应放哪里 |
|----------|----------|
| 节点具体工作步骤 | NODES.md（每节点"工作步骤"段）|
| 谁来做、什么角色 | properties.assignee + NODES.md |
| 表单字段 | properties.form |
| 出产物 / 出口标准 | properties.artifact + properties.exitCriteria |
| 未来 TODO / 设计变更 | CHANGELOG.md / roadmap.md |
| 完整工作指导（8 节）| job_cards/job_card_<node_id>.md |

### 2.2 实际应用效果（每个 task 字符数 -83%）

| 节点 | 简化前 | 简化后 |
|------|--------|--------|
| stage_intake | `0. 接收/登记 (u_fdp_pm 直接, SPI 角色 R3 → u_fdp_pm 映射待 v0.7+ 用 assignmentHandler)` (~70 字符) | `0. 接收/登记` (~10 字符) |
| stage_pm | `1. RML 立项 (u_fdp_pm 直接, SPI 角色 R3 映射待 v0.7+ 用 assignmentHandler)` (~60) | `1. RML 立项` (~7) |
| ... | (其他 4 个 task 节点同理) | ... |

---

## 3. 核心发现 · save vs deploy 双层结构

### 3.1 engine 双层模型

```
┌────────────────────────────────────┐     ┌────────────────────────────────────┐
│ processDesign（设计层）             │     │ processDefine（部署层）             │
│ ─────────────────────────          │     │ ─────────────────────────          │
│ id / name / displayName            │     │ id / processDefineId               │
│ type / icon / remark               │     │ processDefineName / version / state│
│ （无 version 字段）                 │     │                                    │
├────────────────────────────────────┤     ├────────────────────────────────────┤
│ jsonObject（content 快照）          │     │ content（部署时的快照）             │
│ • 含 version 字段（来自 fdep.json）│     │ • 含 version 字段                   │
│ • 含 nodes / edges / metadata      │     │ • deploy 时拷贝（version+1）       │
└────────────────────────────────────┘     └────────────────────────────────────┘
       ↑                                       ↑
   listByType 返回                          processDefine/page 返回
   save 更新                                  deploy 更新
```

### 3.2 两个 API 对比

| API | 视角 | 列出 | 更新触发 |
|-----|------|------|----------|
| `processDesign/listByType` | **设计层** | 所有 design + 最新 deploy 引用 | `processDesign/save` |
| `processDefine/getLastByName` | **部署层** | 最新 deploy | `processDefine/deploy` |
| `processDefine/page` | **部署层** | 同流程所有 deploy 版本（含 inactive） | 同上 |
| `processInstance/detail.jsonObject` | **实例** | 当前 instance 的快照 | 发起 instance 时冻结 |

### 3.3 用户发现的真理（ADR）

> **save 的流程可以运行，但是需要发布一下，用户才会 wf/processInstance/page 得到最新的那个版本**

含义：
- `processDesign/save` → 只更新设计层（jsonObject）
- `processDefine/deploy` → 更新部署层（version+1）
- 用户**发新 instance** 或**看 processInstance/page** 时，需要最新 deploy 版本
- save 不够，**必须 deploy**

### 3.4 version 字段在 content 内部（不在 ProcessDesign 表上）

```
ProcessDesign 模型字段（vendor/jeeflow/model.py:289）:
  id / name / displayName / type / icon / isDeployed / remark / createTime / ...
  ← 没有 version 字段

listByType.jsonObject.version = fdep.json 内 "version": "0.6.2" 字段
```

**含义**：改 `fdep.json` 内的 `version` 字段 + save → listByType 显示新版本。但 `processDesign/save` 不会自动更新此字段（需 content 内手动设置）。

---

## 4. 客户 server 多轮 deploy 历程

| 轮次 | 动作 | defineId | version | state |
|------|------|----------|---------|-------|
| **初始** | 之前已 deploy v1 | `1790223055480000` | v1 | state=0 |
| **r1** | (processDefine/detail 验证 + customer-test 已生效) | — | — | — |
| **r2** | 简化版 deploy → simplify | `1790230247071000` | v2 | state=1 active |
| **r3** | save (v0.6.2 实验) + 自动触发 deploy | `1790232633116000` | v3 | state=1 active |

**重要观察**：r3 的 deploy 是 `processDesign/save` 后**自动**触发的（or 手动）。后续版本号推进 0.6.1 → 0.6.2 + deploy v3。

---

## 5. customer-test 5 步同步验证

```
[1] git 状态                              ✅ up to date
[2] customer design version              ✅ 0.6.2
[3] customer processDefine/page          ✅ v3+v2 active, v1 inactive
[4] 新发起实例用最新版 + version + 简化 text  ✅ v3 + 0.6.2 + "0. 接收/登记"
[5] ea-compliance                        ✅ 44/44 PASS
```

---

## 6. 关键决策（ADR 风格）

### ADR-35.1 · text.value 极简原则
- **决策理由**：括号信息密度低，分散在 NODES.md / Job Card / DESIGN.md
- **执行**：flow-design §2.3 写入 + fdep.json 应用 + customer-test deploy v2

### ADR-35.2 · save vs deploy 解耦认知
- **决策理由**：engine 双层设计（设计层元数据 vs 部署实例版本），各自独立更新
- **后果**：设计师 save 后**必须**调 deploy，用户才会拿到最新版

### ADR-35.3 · version 字段手动管理
- **决策理由**：version 不在 ProcessDesign 表上，存在于 content (jsonObject) 内
- **后果**：改 fdep.json 内的 version + save 即可推进；不需重启 engine

### ADR-35.4 · Git commit 不擅自执行（按 jeeFlow 原则）
- **决策理由**：AGENTS.md "禁止自由发挥" + "NEVER commit unless explicitly asked"
- **执行**：用户明确授权 "git commit + push" 后才执行
- **commit message 格式**：`fdep v0.6.2 · simplify task text.value per §2.3 文本极简原则`

---

## 7. 度量（飞轮 35 圈累积）

| 指标 | #34 | **#35** |
|------|-----|---------|
| §9 检查项 | 44 | **44** |
| fdep.json text.value 平均字符数 | ~60 | **~10**（-83%）|
| customer-test fdep deploy 版本数 | 1 (v1) | **3** (v1+v2+v3) |
| customer-test active version | v1 | **v3** |
| 双层结构文档化 | ❌ | ✅（roadmap 待补） |
| 配置文件数 | 2 | **2** |
| SOP 数 | 15 | **15** |
| EA roadmap 版本 | v3.8 | **v3.8** |

---

## 8. 闭环示意

```
┌── "text.value 太长太啰嗦" ──┐
↓                       │
定原则 B（任务说清楚就足够）  │
↓                       │
简化 fdep.json 6 个 task    │
↓                       │
deploy v2 到 customer-test │
↓                       │
发现 save vs deploy 双层结构 │
↓                       │
再 deploy v3 + 改 version 0.6.2 │
↓                       │
git commit + push + customer git pull │
↓                       │
→ 飞轮第 35 圈 ✅           │
```

---

## 9. 经验沉淀

### 9.1 text.value 极简原则的复用价值
- 适用所有流程：fdep / invoice-approval / expense-approval / 未来的第 3 流程
- 在 flow_completeness.py 加检查项："text.value 不应含括号补充"
- 在 gen-job-cards.py 中：**不**自动生成括号补充（避免 v0.6 那种啰嗦）

### 9.2 save vs deploy 双层结构的工程意义
- **设计层（processDesign）**：版本演进历史（设计稿快照）
- **部署层（processDefine）**：运行时实例（用户感知）
- 两层**解耦**让设计师可以反复迭代设计而不影响线上
- **坑**：设计师 save 后必须 deploy，用户才会感知

### 9.3 调试双层结构的诊断工具
- `processDesign/listByType` 看设计层
- `processDefine/page` 看部署版本
- `processDefine/getLastByName` 看最新 deploy
- `processInstance/detail.jsonObject` 看 instance 实际用版本

### 9.4 git commit 边界（按 jeeFlow 原则）
- 用户**明确**授权才 commit（Iter#35 是首次授权）
- 不擅自 push（即使 commit 已完成）
- push 由用户决定：GitHub remote / customer server 手动 / 其它

---

## 10. 待补 backlog（视下次会话决定）

- [ ] flow_completeness.py 加"text.value 极简"检查项
- [ ] gen-job-cards.py 修复：模板不含括号补充
- [ ] roadmap §3.2 加 processDesign vs processDefine 双层结构说明
- [ ] Iter#34 endpoint 在 customer-test 完整跑通 4 步工作流（已部分测过）

---

## 11. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-24** | **第三十五轮迭代 · W43 text.value 简化 + save/deploy 双层结构发现**：① **新原则 B** "text.value 极简"（flow-design §2.3）写入 + fdep.json 6 个 task 应用（字符数 -83%）；② **deploy 到 customer-test v2 simplify**（Iter#32 同步 + Iter#34 endpoint 验证）；③ **核心发现**：engine 双层结构（processDesign 设计层 vs processDefine 部署层），save vs deploy 完全解耦；④ **version 字段机制发现**：不在 ProcessDesign 表上，存在 content (jsonObject) 内；⑤ **用户发现真理**：save 不够，必须 deploy 用户才会感知；⑥ **跟进 v0.6.2**（version 字段）+ 再 deploy v3 active；⑦ **git commit + push**（commit 0935cbf + push origin/dev）；⑨ **customer git pull 完成**；⑩ **5 步验证全过**：git up to date + customer design 0.6.2 + processDefine 3 个版本 + 新实例 v3 + ea-compliance 44/44 PASS；⑪ **未触动**：所有 SOP / config / SKILL / 任何既有文件除 flow-design §2.3 + fdep.json；⑫ 新增 iterations/2026-09-24_text-value-save-deploy.md；⑬ iterations/README.md 刷新 34 → 35 圈。 |