# 14-decision-submitType 覆盖测试

- **测试时间**：2026-09-17 12:20:00
- **测试类型**：按 docs/AGENTS.md §5 完整流程（双场景）
- **关联流程**：`./flows/14-decision-submitType.json`
- **关联已知问题**：`./docs/known-issues.md §20`

## 1. 设计概览

```
节点：start → apply(user1) → task1(user2) → decision1 → {end (submitType∈{0,1,5,20}) | apply (submitType∈{2,3,6})}
决策 expr:
  decision1→end expr='submitType==0 || submitType==1 || submitType==5 || submitType==20'
  decision1→apply expr='submitType==2 || submitType==3 || submitType==6'
```

## 2. 部署

reset → save (name=14-decision-submitType) → deploy → processDefineId=113 ✅

## 3. 启动 + 执行（双场景）

### Test A: submitType=0 happy path

→ instanceId=91765293264095

执行 user2 submitType=0 → code:0

### Test B: submitType=2 REJECT

→ instanceId=91765294251234

执行 user2 submitType=2 → code:0

## 4. 校验

### 4.1 Test A detail

```
state=20 (DONE)  active=0
  apply  state=20
  task1  state=20
```

approvalRecord: apply(user1) → task1(user2) ✅

→ 因 decision expr `||` 不支持 SimpleExprEvaluator，所有 expr 评估 False → fallback edges[0]=end → state=20（实测与设计目标巧合一致）

### 4.2 Test B detail

```
state=45 (REJECT)  active=0
  apply  state=20
  task1  state=20
```

→ submitType=2 由 facade `_processTask_execute` 拦截，直接走 `execute_and_jump_to_end` → state=45（**不走 decision 节点**）

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId（2 次）
- [x] A: state==20；B: state==45
- [x] submitType=2 触发 REJECT（facade 拦截）
- [x] submitType=0 fallback 到 end（decision expr `||` 不支持）
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

**确认 §20 已记录的设计意图不可实现**：
- `SimpleExprEvaluator` regex `^\s*(#?\w+)\s*(>=|<=|!=|==|>|<)\s*(\d+(?:\.\d+)?)\s*$` 不支持复合 expr (`||`/`&&`)
- submitType∈{2,3,6} 由 facade `_processTask_execute` 拦截直接走 `execute_and_jump_to_end/jump_task/jump_to_first_task_node`，**不走 decision**
- 因此 decision 节点路由 submitType 在该引擎下不可实现

**实测 A 测试**：decision expr `submitType==0 || ...` 不被识别 → fallback edges[0]=end → state=20（**与设计目标一致仅为巧合**）。

**实测 B 测试**：submitType=2 走 facade REJECT → state=45（不匹配 design 期望的"回退到 apply"）。

无新发现。**本流程设计意图不可实现**，应避免使用。

## 7. 结论

✅/❌ **设计意图不可实现**，但引擎 fallback 行为兼容了 happy path（state=20）。
- submitType=0: 实际 state=20 (与设计"走 end"巧合一致) ✅
- submitType=2: 实际 state=45 REJECT (与设计"回退到 apply"不一致) ❌

设计建议：避免在 decision 节点用 expr 路由 submitType∈{2,3,6}；submitType∈{0,1,5,20} 走正常决策或 fallback 即可。
