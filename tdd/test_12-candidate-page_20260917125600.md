# 12-candidate-page PG 后端覆盖测试

- **测试时间**：2026-09-17 12:56:00
- **后端**：PG
- **关联流程**：`./flows/12-candidate-page.json`

## 1. 设计概览

```
start → apply(applicant) → review(leader, candidateUsers="userA,userB", candidateGroups="finance") → end
```

## 2. 部署

reset → save → deploy pdid=1789615419989000 ✅

## 3. 启动 + candidatePage 校验 + 执行

→ instanceId=91766190101567

### 3.1 candidatePage in apply task

```
total=4
  userA     ← candidateUsers
  userB     ← candidateUsers
  leader    ← candidateGroups=finance
  manager   ← candidateGroups=finance
```

✅ candidateUsers + candidateGroups(finance) 合并去重 = 4 个候选人

### 3.2 execute review by leader

leader execute → code=0 → state=20

## 4. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId
- [x] state==20
- [x] candidatePage 双源合并正确
- [x] SPI finance role 加载正确
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

无新发现。

## 7. 结论

✅ **PASS** — 12-candidate-page PG 全流程符合设计。
