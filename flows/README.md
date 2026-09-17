# ./flows 示例流程索引

本目录收录可直接部署到引擎的流程 JSON。每个文件 `name` 与文件名（不含 `.json`）严格一致，可作为 `/wf/processDesign/save` 的 `content` 字段提交。

> **使用约定**：所有改动需先落 `./tdd/<key>.json`，稳定后 `cp` 到本目录。现有文件（含双 `11-`）**只读**，禁止就地修改（详见 `../docs/known-issues.md` §8）。

---

## 1. 示例索引表（基于 `validate_flow.py` 验证结果）

| 文件 | name | displayName | 节点数 | 边数 | 说明 | 测试状态 |
| --- | --- | --- | --- | --- | --- | --- |
| `01-simple.json` | `simple` | 简单审批流程 | 4 | 3 | 线性最简流 | ✅ validate_flow OK + ✅ 部署回归 PASS（详见 `../tdd/test_01-simple_20260917085500.md`） |
| `02-multi-task.json` | `multi-task` | 多级审批流程 | 6 | 5 | 顺序多人审批 (applicant→leader→manager→boss) | ✅ validate_flow OK + ✅ 部署回归 PASS（详见 `../tdd/test_02-multi-task_20260917085900.md`） |
| `03-decision-expr.json` | `decision-expr` | 决策表达式流程 | 7 | 7 | 决策分流参考样例；✅ **已修复**（业务变量放 `startAndExecute` 顶层），详见 `../docs/known-issues.md` §14 / `../docs/flow.md` §3.4 | ✅ PASS（amount=500→task3 / amount=2000→task2） |
| `04-fork-join.json` | `fork-join` | 并行分支合并流程 | 7 | 7 | fork/join 并行汇聚 | ✅ PASS（详见 `../tdd/test_04-fork-join_20260917091700.md`） |
| `05-countersign-parallel.json` | `countersign-parallel` | 并行会签流程 | 4 | 3 | 并行会签（实测：全员通过才流转，非"任一通过"） | ✅ PASS（详见 `../tdd/test_05-countersign-parallel_20260917091900.md`） |
| `06-countersign-sequential.json` | `countersign-sequential` | 串行会签流程 | 4 | 3 | 串行会签（实测：逐人创建子任务，loopCounter 0→1→退出） | ✅ PASS（详见 `../tdd/test_06-countersign-sequential_20260917092000.md`） |
| `07-countersign-ratio.json` | `countersign-ratio` | 按比例会签流程 | 4 | 3 | 按比例会签 | ✅ PASS（修复后 2/4 通过即流转；详见 `../tdd/test_07-countersign-ratio_20260917092200.md` + 修复回归报告） |
| `08-countersign-sequential-approve.json` | `cs-seq-approve` | 串行会签-审批 | 5 | 4 | 串行会签 + 审批 | ✅ PASS（详见 `../tdd/test_08-countersign-sequential-approve_20260917100500.md`） |
| `08-custom-node.json` | `custom-node` | 自定义节点流程 | 4 | 3 | 自定义节点 | ❌ FAIL（详见 `../tdd/test_08-custom-node_20260917101500.md`：引擎未实现 clazz/methodName 反射调用） |
| `09-with-reject.json` | `with-reject` | 含驳回流程 | 5 | 4 | **线性流**（驳回由引擎自动 ROLLBACK，无显式驳回节点；文件名误导，详见 `../docs/known-issues.md` §5） | ✅ PASS（详见 `../tdd/test_09-with-reject_20260917102500.md`：submitType=2 REJECT → state=45） |
| `10-mixed-mode.json` | `mixed-mode` | 混合模式流程 | 9 | 10 | 混合会签/决策/分支 | ✅ PASS（详见 `../tdd/test_10-mixed-mode_20260917103500.md`：fork-join + decision 正确，业务变量需顶层传入） |
| `11-assignee-vars.json` | `assignee-vars` | assignee 变量解析流程 | 5 | 4 | assignee 变量解析 | ✅ PASS（详见 `../tdd/test_11-assignee-vars_20260917104500.md`：变量解析+字面量 fallback 都正确） |
| `11-assignment-handler.json` | `assignment-handler` | 参与者解析流程（内置 handler） | 6 | 5 | 参与者解析 | ✅ PASS（详见 `../tdd/test_11-assignment-handler_20260917113000.md`：补 SPI task4/finance 后 4/4 handler 通过，state=20 DONE） |
| `12-candidate-page.json` | `candidate-flow` | 候选人双源流程 | 4 | 3 | 候选人双源 | ✅ PASS（详见 `../tdd/test_12-candidate-page_20260917113000.md`：补 SPI finance 后 candidatePage 在 apply 节点返回 4 个候选人=userA/userB/leader/manager） |
| `13-countersign-one-vote-veto.json` | `countersign-one-vote-veto` | 并行会签·一票否决流程 | 4 | 3 | 并行会签·一票否决 | ✅ PASS（详见 `../tdd/test_13-countersign-one-vote-veto_20260917110500.md`：userA DISAGREE → state=20，userB/C ABANDON） |
| `14-decision-submitType.json` | `14-decision-submitType` | 决策路由按 submitType 分流 | 5 | 5 | submitType 路由矩阵测试 | ❌ FAIL（详见 `../tdd/test_14-decision-submitType_20260917111000.md`：decision expr `\|\|` 不支持 + submitType=2/3/6 被 facade 拦截） |
| `15-decision-amount.json` | `15-decision-amount` | 决策路由按金额阈值分流 | 5 | 5 | **本轮新增**：amount < 10000 → end / amount >= 10000 → task1 | ✅ PASS（含 Issue D 修复 4/4，详见 `../tdd/test_15-decision-amount_20260917112000.md`） |

> 节点数 / 边数仅以 `validate_flow.py` 拓扑扫描结果为准。详细测试结果参见 `./tdd/` 目录下的对应测试报告。

---

## 2. 字段命名约定

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | **必须与文件名（不含 `.json`）一致**，否则引擎按 `name` 索引会冲突 |
| `displayName` | string | 中文显示名，可包含括号说明 |
| `type` | string | `"approval"` 或 `"custom"`（暂未使用 `custom` 类型） |
| `nodes[].id` | string | 全局唯一，便于边引用 |
| `nodes[].type` | string | `snaker:start` / `snaker:end` / `snaker:task` / `snaker:decision` / `snaker:fork` / `snaker:join` / `snaker:custom` |
| `nodes[].properties.assignee` | string | 任务受理人（userId / role），如 `user1` / `user2` |
| `nodes[].properties.taskType` | int | 0=普通 / 1=会签 / 2=或签 |
| `nodes[].properties.performType` | int | 0=单人 / 1=多人 |
| `edges[].properties.expr` | string | OGNL 表达式，**仅 `snaker:decision` 出边生效**，详见 `../docs/known-issues.md` §2 |

---

## 3. `name` 与文件名的对应关系

引擎部署流程时，**实际不强制文件名与 `name` 一致**；但本目录约定二者一致，以便检索、引用、git diff。约定示例：

```text
14-decision-submitType.json  →  name = "14-decision-submitType"
15-decision-amount.json      →  name = "15-decision-amount"
```

> 注：`08-countersign-sequential-approve.json` 与 `08-custom-node.json` 共享 `08-` 前缀但 `name` 完全不同（`cs-seq-approve` vs `custom-node`），是历史遗留。外部引用以 `name` 为准。

---

## 4. 部署流程

```text
1. 选 JSON：cat ./flows/<key>.json | jq -c
2. 提交设计：POST /wf/processDesign/save   body={"content": <JSON 字符串>}
3. 部署：POST /wf/processDesign/deploy    body={"id": <processDesignId>}
4. 启动实例：POST /wf/processInstance/startAndExecute   body={"processDefineId": <id>, "operator": "...", "assignees": {"apply": "user1", "task1": "user2"}, "variables": {"amount": 5000}}
```

详细端点参数见 `../docs/api.md`。

---

## 5. 已知歧义

- **`09-with-reject.json`**：文件名暗示"含驳回节点"，实际是线性流靠引擎自动 ROLLBACK（详见 `../docs/known-issues.md` §5）
- **`08-countersign-sequential-approve.json` 与 `08-custom-node.json`**：共享 `08-` 前缀，`name` 完全不同，外部引用以 `name` 为准
- **`11-assignee-vars.json` 与 `11-assignment-handler.json`**：共享 `11-` 前缀，`name` 完全不同
- **`03-decision-expr.json`**：是决策分流参考模板，与本轮新增 `14-decision-submitType` / `15-decision-amount` 模式一致
- **本轮新增的 `14-decision-submitType.json` / `15-decision-amount.json`**：14 ❌ FAIL（决策 expr `\|\|` 不支持 + submitType=2/3/4/6 被 facade 拦截），15 ✅ PASS（修复 Issue D 后 4/4）
