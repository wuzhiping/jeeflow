# 12-candidate-page 覆盖测试

- **测试时间**：2026-09-17 12:16:00
- **测试类型**：按 docs/AGENTS.md §5 完整流程
- **关联流程**：`./flows/12-candidate-page.json`
- **关联已知问题**：`./docs/known-issues.md §19`（SPI 修复后已通过）

## 1. 设计概览

```
节点：start → apply(applicant) → review(leader, candidateUsers="userA,userB", candidateGroups="finance") → end
```

## 2. 部署

reset → save (name=candidate-flow) → deploy → processDefineId=113 ✅

## 3. 启动 + 执行 + candidatePage 校验

→ instanceId=91765230201881

### 3.1 candidatePage in apply task（向后查 review 节点的候选）

```bash
curl -X POST /wf/processTask/candidatePage -d '{"processTaskId": <apply_id>, "pageNum":1, "pageSize":20}'
```

**响应**：

```
total=4
  userA     ← candidateUsers
  userB     ← candidateUsers
  leader    ← candidateGroups=finance → find_by_role("finance") → [leader, manager]
  manager   ← candidateGroups=finance
```

✅ candidateUsers + candidateGroups 合并去重，4 个候选人

### 3.2 执行 review by leader

leader execute → code:0

## 4. 校验

### 4.1 detail

```
state=20 (DONE)  active=0
  apply   state=20 actorIds=['user1']
  review  state=20 actorIds=['leader']
```

### 4.2 approvalRecord

```
apply   operator=user1
review  operator=leader
```

✅ 流程正常推进

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId
- [x] 走完所有 task，state==20
- [x] approvalRecord 节点顺序符合设计（apply→review）
- [x] candidatePage 返回正确（candidateUsers ∪ candidateGroups(finance)）
- [x] SPI data: finance role 正确加载（leader+manager）
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

**确认 §19 已修复**：
- candidatePage 在 apply 节点（向后查 review）返回 4 个候选人 = candidateUsers(userA/userB) ∪ candidateGroups(finance→leader/manager)
- SPI 数据 finance role 正确加载（见 §6 §18 修复记录）

无新发现。

## 7. 结论

✅ **PASS** — 12-candidate-page 全流程符合设计，candidatePage 双源合并正确。
