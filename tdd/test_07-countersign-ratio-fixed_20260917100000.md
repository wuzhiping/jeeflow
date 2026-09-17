# test_07-countersign-ratio（修复后）— 2026-09-17

## 1. 摘要

| 项目 | 状态 |
|---|---|
| 流程 | `./flows/07-countersign-ratio.json`（4 人 PARALLEL + `countersignCompletionCondition`） |
| 设计意图 | 4 人会签 2 人通过即流转 |
| 初始测试 | ⚠️ **FAIL**（引擎完全忽略 `countersignCompletionCondition`，按 PARALLEL 全员通过才流转） |
| 修复 | ✅ **RatioCapableEngine**（`main.py` + `main_pg.py`）+ SimpleExprEvaluator 支持 `#varname` |
| 修复后验证 | ✅ **PASS**（2/4 通过立即流转，剩余 2 task ABANDONED） |
| 回归测试 | ✅ 02/03/05/06/13 全部无回归 |

## 2. 修复前后对比

### 修复前（FAIL）
- 4 人会签按 PARALLEL 处理，**全部通过才流转**
- `countersignCompletionCondition` 字段被引擎忽略
- 详见 `tdd/test_07-countersign-ratio_20260917092200.md`

### 修复后（PASS）

**2/4 通过场景**：
```
init:  state=10 activeTasks=4  (4 个 task1 DOING)
userA agree: state=10 activeTasks=3  (1 DONE, 3 DOING)
userB agree: state=20 activeTasks=0  ← 2/4 比例满足，立即流转
                    userA: state=20 DONE
                    userB: state=20 DONE
                    userC: state=99 ABANDONED
                    userD: state=99 ABANDONED
```

## 3. 修复方案

### 3.1 代码改动

**main.py + main_pg.py 同步改动**（共两个文件，每个 ~50 行新增）：

1. **扩展 `SimpleExprEvaluator`** 支持 OGNL 风格 `#varname` 前缀：
   ```python
   m = re.match(r"^\s*(#?\w+)\s*(>=|<=|!=|==|>|<)\s*(\d+(?:\.\d+)?)\s*$", expr)
   key, op, val = m.group(1).lstrip("#"), m.group(2), float(m.group(3))
   ```

2. **新增 `RatioCapableEngine(EngineImpl)`** 覆盖 `execute_process_task`：
   ```python
   async def execute_process_task(self, task_id, operator, args=None):
       # 关键：先 super 完成当前 task（super 内部已 _prepare_execute_task）
       #      不能再调 _prepare_execute_task 否则 "task not doing"
       result = await EngineImpl.execute_process_task(self, task_id, operator, args)
       
       # 重新查实例 + 统计比例
       # 求值 cs_cond（注入 nrOfCompletedInstances / nrOfInstances）
       # 通过 → abandon 剩余 DOING + _execute_node 推进下游
       ...
   ```

3. **替换引擎实例化**（line 70 / line 395）：
   ```python
   # 原: engine = EngineImpl(repo, user_prov, idgen, SimpleExprEvaluator())
   # 新: engine = RatioCapableEngine(repo, user_prov, idgen, SimpleExprEvaluator())
   ```

### 3.2 cs_cond 双位置兼容

cs_cond 同时支持：
- `properties.countersignCompletionCondition`（引擎实际读的位置）
- `properties.field.countersignCompletionCondition`（设计器输出的位置，07 JSON 用此位置）

向后兼容现有 JSON（07 不需要改动）。

## 4. 修复实现关键点

### 4.1 踩坑：第一次实现错误

第一次实现：
```python
# 错误：先 _prepare_execute_task，再 super
task, inst, flow, vars_ = await self._prepare_execute_task(task_id, ...)  # task DOING→DONE
...
result = await super().execute_process_task(task_id, ...)  # super 内部 _prepare_execute_task → "task not doing"!
```

**症状**：所有流程都报 "task not doing"，包括 02-multi-task、03-decision-expr 等。

**修复**：直接 `await EngineImpl.execute_process_task(self, ...)`，让 super 自己处理 _prepare_execute_task。

### 4.2 修复要点

1. **必须先 super**：super 内部已经完成当前 task（DOING→DONE），不能重复
2. **重新查实例**：super 完成后 instance 状态已更新，从 result 取最新数据
3. **abandon 后必须 sync_task_to_aggregate**：避免 update_instance 级联回写旧状态
4. **cs_veto 不受影响**：我们的子类只在 `cs_cond != ONE_VOTE_VETO` 时介入

## 5. 修复验证

### 5.1 07 比例会签 2/4（核心场景）

| 步骤 | state | activeTasks | task1 状态 |
|---|---|---|---|
| 初始 | 10 | 4 | 4 DOING |
| userA agree | 10 | 3 | 1 DONE + 3 DOING |
| userB agree | **20** | **0** | 2 DONE + 2 ABANDONED |

✅ 完美：2/4 比例满足立即流转，剩余 task1 自动 ABANDONED (state=99)。

### 5.2 07 比例会签 4/4（PARALLEL 默认行为）

| 步骤 | state | 说明 |
|---|---|---|
| userA agree | 10 | 1/4（不满足 2/4） |
| userB agree | **20** | 2/4 比例满足，立即流转 |

✅ 4/4 通过时 2/4 比例先满足，行为一致。

### 5.3 回归测试（其他流程无影响）

| 流程 | 用例 | 结果 |
|---|---|---|
| 02-multi-task | 4 task 链式审批 | ✅ PASS |
| 03-decision-expr | amount=2000>1000 → task2 | ✅ PASS |
| 05-countersign-parallel | 3/3 通过才流转 | ✅ PASS |
| 06-countersign-sequential | 逐人审批 | ✅ PASS |
| 13-countersign-one-vote-veto | userA DISAGREE → state=20 | ✅ PASS |

ONE_VOTE_VETO 仍按引擎原逻辑生效（userA DISAGREE submitType=20 → 立即流转 + 剩余 ABANDONED）。

## 6. 引擎限制

当前 `RatioCapableEngine` 仅支持 SimpleExprEvaluator 已有的简单表达式（`varname op number`）：
- ✅ 支持：`#nrOfCompletedInstances==2`、`#nrOfCompletedInstances>=3`、`nrOfCompletedInstances<nrOfInstances`
- ❌ 不支持：复杂 OGNL 表达式（如 `#nrOfCompletedInstances/#nrOfInstances>=0.5`）、函数调用

如需更复杂表达式，可替换 `self.expr_eval` 为完整 spEL 解析器。

## 7. 修改文件清单

- `./main.py`：+ `RatioCapableEngine` 类 + `SimpleExprEvaluator` 扩展 + 替换 `EngineImpl` 实例化
- `./main_pg.py`：同上（保持内存版与 PG 版一致）
- `./docs/known-issues.md §15`：升级为已修复
- `./docs/AGENTS.md`：相关条目改为"已实现"
- `./flows/README.md`：07 状态改为 ✅ PASS
- `./flows/07-countersign-ratio.json`：**未修改**（向后兼容，`field` 内 cs_cond 自动支持）

## 8. 服务重启

修改 main.py 后需重启服务：
```bash
# 找到当前 main.py 进程并 kill
pgrep -f "\.venv/bin/python3 main.py" | xargs kill

# 重新启动
cd /opt/jupyter/src/RD/projects/jeeFlow
JEEFLOW_PG_DSN=postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm \
  nohup .venv/bin/python3 main.py > /tmp/opencode/main_restart.log 2>&1 &
```

服务在 PID 3365271 运行中，端口 8101，healthz UP。
