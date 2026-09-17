# 08-countersign-sequential-approve 覆盖测试

- **测试时间**：2026-09-17 12:04:00
- **测试类型**：按 docs/AGENTS.md §5 完整流程
- **关联流程**：`./flows/08-countersign-sequential-approve.json`

## 1. 设计概览

```
节点：start → apply(applicant) → task1(SEQUENTIAL [userA,userB]) → approve(leader) → end
会签配置：task1 performType=1, countersignType=SEQUENTIAL
```

## 2. 部署

reset → save (name=cs-seq-approve) → deploy → processDefineId=113 ✅

## 3. 启动 + 执行

→ instanceId=91764966562244

启动后 active=1（SEQUENTIAL 仅 userA）：
- task1(userA) DOING

执行 userA → userB → leader，全部 code:0

## 4. 校验

### 4.1 detail

```
state=20 (DONE)  active=0
  apply   state=20 actorIds=['user1']
  task1   state=20 actorIds=['userA']
  task1   state=20 actorIds=['userB']
  approve state=20 actorIds=['leader']
```

### 4.2 approvalRecord

```
apply   operator=user1
task1   operator=userA
task1   operator=userB
approve operator=leader
```

✅ 串行会签完成后流转到 approve 节点（leader），leader 通过后 state=20

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId
- [x] 走完所有 task，state==20
- [x] approvalRecord 节点顺序符合设计（apply→task1(2x)→approve）
- [x] SEQUENTIAL 行为正确
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

无新发现。复合场景「SEQUENTIAL 会签 + 单人 approve」行为符合设计：
- task1 SEQUENTIAL：userA → userB 依次审批
- approve：单 leader 审批
- 顺序衔接正确，无 active=0 中断

## 7. 结论

✅ **PASS** — 08-countersign-sequential-approve 全流程符合设计。
