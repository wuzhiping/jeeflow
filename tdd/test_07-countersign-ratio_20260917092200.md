# 07-countersign-ratio 测试日志

**日期**：2026-09-17 09:22（初始 FAIL）→ 2026-09-17 10:00（**修复后 PASS**，详见同目录 `test_07-countersign-ratio-fixed_20260917100000.md`）
**测试文件**：`./flows/07-countersign-ratio.json`
**结论**：✅ **PASS**（修复后 2/4 通过即流转）

> **修复摘要**：`main.py` + `main_pg.py` 新增 `RatioCapableEngine(EngineImpl)` 扩展 + `SimpleExprEvaluator` 支持 `#varname`。修复后 07 比例会签按设计运行。回归测试 02/03/05/06/13 无影响。详见 `tdd/test_07-countersign-ratio-fixed_20260917100000.md`。

---

## 1. 流程结构（4 节点 / 3 边）

```
start → apply(applicant) → task1(userA,userB,userC,userD, performType=1, countersignType=PARALLEL) → end
```

**设计意图**：4 人中 2 人通过即流转
- `countersignCompletionCondition: "#nrOfCompletedInstances==2"` 放在 `properties.field.countersignCompletionCondition`

**实测**：4 人全部完成才流转（与 05 PARALLEL 行为一致）

## 2. 测试步骤

### 2.1 部署 + 启动

```bash
design_id=9, process_define_id=113
instance_id=91758737136631
```

启动后 4 子任务同时激活（userA/B/C/D 各一 taskActorIdList）。

### 2.2 ⚠️ 2/4 完成不流转（设计意图失败）

仅完成 userA + userB：

```json
{
  "state": 10,                          ← 仍 DOING
  "activeTaskList": [
    {"taskActorIdList": ["userC"], "taskState": 10},
    {"taskActorIdList": ["userD"], "taskState": 10}
  ]
}
```

**期望**：按 `#nrOfCompletedInstances==2` 应流转到 end
**实际**：userC/D 仍 DOING，state=10，未流转

### 2.3 4/4 完成才流转

完成 userC + userD 后：state=20 DONE，approvalRecord 含 5 条（apply + 4 user）。

## 3. 修复尝试 fixH：把 condition 放 properties 根

创建 `tdd/07-countersign-ratio-fixH.json`：
```diff
  "properties": {
    "assignee": "userA,userB,userC,userD",
    "performType": 1,
    "countersignType": "PARALLEL",
    "form": "ratio-form",
+   "countersignCompletionCondition": "#nrOfCompletedInstances==2",
    "field": {
      "candidateUsers": "userA,userB,userC,userD",
-     "countersignCompletionCondition": "#nrOfCompletedInstances==2"
    }
  }
```

**实测**：行为与原版**完全一致**——2/4 完成不流转，4/4 完成才流转。

## 4. 源码定位（根因）

`engine.py:95-104`：

```python
cs_cond = str(cur_node.properties.get("countersignCompletionCondition", "") or "").strip()
...
try:
    cs_veto = ct != "" and cs_cond.upper() == "ONE_VOTE_VETO" and \
        int(vars_.get(KEY_SUBMIT_TYPE, -1)) == int(SubmitType.COUNTERSIGN_DISAGREE)
except (ValueError, TypeError):
    cs_veto = False
```

**关键发现**：
1. 引擎**只**读取 `node.properties.countersignCompletionCondition`（properties 根），**不读** `field.countersignCompletionCondition`
2. 引擎**只**用 `cs_cond.upper() == "ONE_VOTE_VETO"` 做特殊检查，**没有任何通用条件求值逻辑**
3. 全 jeeflow 包 grep `nrOfCompletedInstances` / `RATIO` 字符串 → **0 命中**
4. 通用会签完成条件（如比例会签的 N/K 阈值）**引擎完全未实现**

## 5. 行为总结

| 维度 | 实测 |
|---|---|
| 启动时子任务数 | 4 个同时创建 |
| 2/4 完成 → 流转 | ❌ 仍 DOING（设计意图失败） |
| 4/4 完成 → 流转 | ✅ state=20 DONE（按 PARALLEL 全员通过） |
| `countersignCompletionCondition` 字段是否被读取 | ❌ 完全忽略（除 ONE_VOTE_VETO 字符串外） |
| 比例会签功能 | ⚠️ **引擎未实现** |

## 6. 文档同步

### 6.1 `docs/AGENTS.md §4` 设计模板（修改）

| 业务场景 | 推荐样板 | 关键字段 |
| --- | --- | --- |
| **比例会签（⚠️ 未实现）** | `./flows/07-countersign-ratio.json` | `performType=1, countersignType=PARALLEL`，`countersignCompletionCondition` **无效**（引擎忽略） |

### 6.2 `docs/AGENTS.md §5.8` 表（修改）

| 类型 | 完成条件 |
|---|---|
| 比例（⚠️ 未实现） | 引擎**不评估** `countersignCompletionCondition`（除非 `ONE_VOTE_VETO`）；按 PARALLEL "全员通过才流转"处理 |

### 6.3 `docs/AGENTS.md §6 #6` 约束（修改）

| 6 | `countersignCompletionCondition` 两位置：`properties` 根 或 `properties.field` | ⚠️ **两位置都不被引擎读取**（除 `ONE_VOTE_VETO`）；比例/阈值类条件**未实现** | `./docs/flow.md §3.3` |

### 6.4 `docs/known-issues.md #15`（新增）

> ⚠️ 比例会签 `countersignCompletionCondition` 字段被引擎**完全忽略**（除 `ONE_VOTE_VETO` 字符串外）。
> 详见 `tdd/test_07-countersign-ratio_20260917092200.md`

## 7. WIP 归档

- `tdd/07-countersign-ratio-fixH.json`：condition 移到 properties 根的尝试，仍无效，可作反例

## 8. 结论

07-countersign-ratio.json **设计意图无法在当前引擎中实现**：
- ❌ 比例条件（2/4 完成即流转）**无效**
- ✅ 实际行为 = 05 PARALLEL 全员通过才流转
- ⚠️ `countersignCompletionCondition` 字段引擎仅识别 `ONE_VOTE_VETO`
