# BDD #106 抄送+权限+委托综合测试 (20260919060000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> submit[提交申请]
    submit --> leader_review[领导审批 f_amount只读]
    leader_review --> manager_review[经理审批 f_secret隐藏]
    manager_review --> end([结束])
```

## 场景
4 节点流程，综合测试：
1. **字段权限** — leader_review 节点 f_amount=1(只读) f_secret=2(编辑)；manager_review 节点 f_secret=3(隐藏)
2. **委托代理** — user1 委托给 manager + surrogate addCandidate
3. **抄送** — startAndExecute 时 f_ccActors="director"，director 的 ccList 应收到
4. **表单回写** — 6 项变量持久化断言

## 关键发现（BUG）

### FIX-DOC-1 字段权限 JSON key 规范

实测发现 `docs/flow.md` §5 + `docs/AGENTS.md` §5.7 描述不准确：

**BUG 1（文档错误）**：
- 旧文档："字段权限码 1=只读 2=隐藏"
- 实测：**1=只读 2=编辑 3=隐藏**（引擎代码 `engine.py:_filter_field_by_perm`）
- 修复：见 `known-issues.md §82` + `flow.md §5.1` 更新

**BUG 2（JSON key 规范）**：
- 旧文档示例：```json "field": { "f_amount": "1" } ```
- 实测：必须用 ```json "field": { "PERMISSION_f_amount": "1" } ```
- 引擎逻辑：`field_perm.get(f"PERMISSION_f_{name}")`，缺前缀则 perm=None → 不过滤
- 修复：`flow.md §5.2` 明确 PERMISSION_ 前缀规范

### DESIGN 委托代理（缺自动展开）

委托关系（userA→userB）**不影响** `processTask/todoList` 的 actor 过滤。
userB 仍需调用 `/wf/processTask/surrogate` addCandidate 才能代办。

## 6 项字段权限断言（双端）

| # | 节点 | 字段 | 操作人 | 操作 | 期望 | 实测 |
|---|------|------|--------|------|------|------|
| 1 | leader_review | f_title (无 PERMISSION) | leader | 改 | LEADER_NEW | ✅ |
| 2 | leader_review | f_amount (PERMISSION=1 只读) | leader | 改 1111→2222 | 1111 | ✅ |
| 3 | leader_review | f_secret (PERMISSION=2 编辑) | leader | 改 ORIG→LEADER_S | LEADER_S | ✅ |
| 4 | manager_review | f_title | manager | 改 | MGR_FINAL | ✅ |
| 5 | manager_review | f_amount (PERMISSION=2 编辑) | manager | 改 1111→8888 | 8888 | ✅ |
| 6 | manager_review | f_secret (PERMISSION=3 隐藏) | manager | 改 LEADER_S→MGR_S | LEADER_S | ✅ |

## 4 大能力实测

| 能力 | API | 测试结果 |
|------|-----|----------|
| 字段权限 | `properties.field.PERMISSION_f_<name>` | ✅ 6/6 双端 PASS |
| 委托代理 | `/wf/processSurrogate/save` + `/wf/processTask/surrogate` | ✅ addCandidate 跑通 |
| 抄送 | `startAndExecute` 的 `variables.f_ccActors` | ✅ director ccList 收到实例 |
| 表单回写 | `processTask/execute` 的 `f_*` args | ✅ 变量持久化到 instance.variables |

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS
