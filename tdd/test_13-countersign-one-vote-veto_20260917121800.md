# 13-countersign-one-vote-veto 覆盖测试

- **测试时间**：2026-09-17 12:18:00
- **测试类型**：按 docs/AGENTS.md §5 完整流程
- **关联流程**：`./flows/13-countersign-one-vote-veto.json`

## 1. 设计概览

```
节点：start → apply(applicant) → task1(PARALLEL [userA,userB,userC], ONE_VOTE_VETO) → end
会签配置：performType=1, countersignType=PARALLEL,
         countersignCompletionCondition="ONE_VOTE_VETO"
```

## 2. 部署

reset → save (name=countersign-one-vote-veto) → deploy → processDefineId=113 ✅

## 3. 启动 + 执行

→ instanceId=91765261724795

启动后并行 active=3：
- task1(userA/B/C) DOING

执行 userA DISAGREE (submitType=20) → code:0 → ONE_VOTE_VETO 触发，流转到 end

## 4. 校验

### 4.1 detail

```
state=20 (DONE)  active=0
  apply  state=20 actorIds=['user1']
  task1  state=20 actorIds=['userA']    ← DISAGREE 完成
  task1  state=99 actorIds=['userB']    ← ABANDON（veto 后未执行的子任务）
  task1  state=99 actorIds=['userC']    ← ABANDON
```

### 4.2 approvalRecord

```
apply  operator=user1
task1  operator=userA
task1  operator=
task1  operator=
```

✅ ONE_VOTE_VETO 行为正确：任一用户 reject → 立即流转，剩余子任务 ABANDON

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId
- [x] 走完所有 task，state==20
- [x] approvalRecord 节点顺序符合设计
- [x] ONE_VOTE_VETO 字符串条件正确识别
- [x] submitType=20 (DISAGREE) 触发 veto
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

**确认 §7 / §8 引擎行为**：ONE_VOTE_VETO 字符串条件由 `engine.py` 识别（`cs_cond.upper() == "ONE_VOTE_VETO"`）。DISAGREE 时：
1. 当前 task 标记 DONE
2. ONE_VOTE_VETO 触发，立即流转到下一节点
3. 其他 doing 子任务设为 ABANDON (state=99)
4. 实例 state=20 DONE

与 07-countersign-ratio 同源（剩余 ABANDON 行为），但触发条件不同（veto vs ratio）。

无新发现。

## 7. 结论

✅ **PASS** — 13-one-vote-veto 全流程符合设计，veto 行为正确，剩余子任务 ABANDON。
