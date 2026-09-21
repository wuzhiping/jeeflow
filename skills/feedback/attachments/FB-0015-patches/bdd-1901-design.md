# BDD-1901-1905 · FIX-T114 REJECT orphan 回归测试 (5 场景) · 2026-11-10 起草

> **来源**: omarchy 第 3 次 file-share (取件码 39376) · BDD-1601 + BUG-4 + FIX-T114
> **起草日期**: 2026-11-10 (W46 Day 3)
> **状态**: 🟡 设计就绪, 等解冻后 W47 Day 3-4 实施
> **关联**: FB-0015 (omarchy) · FIX-T114

---

## 1. BDD #1901 测试列表

| # | 场景 | rejecter | 期望 (修复后) | 双端 |
|---|------|----------|---------------|------|
| #1901.1 | small branch (≤5000) | 不适用 | leader_review → manager_signoff → end_small, no orphan | mem + pg |
| #1901.2 | large branch (>5000) happy | 不适用 | leader → userA → userB → userC → end_large | mem + pg |
| #1901.3 | REJECT by userA | userA | state=45, userA task=20, userB+C task=99 ABANDONED | mem + pg |
| #1901.4 | REJECT by userB | userB | state=45, userB task=20, userA+C task=99 ABANDONED | mem + pg |
| #1901.5 | REJECT by userC | userC | state=45, userC task=20, userA+B task=99 ABANDONED | mem + pg |

---

## 2. BDD 脚本设计 (5-run + REJECT repro)

```bash
#!/bin/bash
# bdd/bdd-1901-1905-fix-t114-reject-orphan_20261110.sh
# 5 场景: REJECT orphan 回归测试
# 状态: 设计就绪, 待解冻后 W47 Day 3-4 实施

set -e
HOST=http://localhost:8101
PASS=0
FAIL=0
RESULTS=""

assert_eq() {
  local desc="$1" actual="$2" expected="$3"
  if [ "$actual" = "$expected" ]; then
    PASS=$((PASS + 1))
    RESULTS="$RESULTS\n✅ #$1 [$desc]"
  else
    FAIL=$((FAIL + 1))
    RESULTS="$RESULTS\n❌ #$1 [$desc]  expected=$expected actual=$actual"
  fi
}

# 检查 instance 详情里的 task 列表
get_task_states() {
  local inst="$1"
  curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
    -d "{\"id\":$inst}" | jq -r '.data.tasks[] | "\(.taskName):\(.taskState)"' | sort
}

get_instance_state() {
  local inst="$1"
  curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
    -d "{\"id\":$inst}" | jq -r '.data.state'
}

# 配置: 部署 expense-threshold-countersign 流程 + SPI users (userA/userB/userC)
# curl -X POST :8101/wf/processDesign/save -d @bdd/bdd-1601-expense-threshold-countersign_20260921_155448.json
# curl -X POST :8101/wf/processDesign/deploy -d '{"name":"expense-threshold-countersign"}'

curl -s -X POST $HOST/api/reset >/dev/null

# ─────────────────────────────────────────────────────────────────────
# #1901.1 small branch happy path
# ─────────────────────────────────────────────────────────────────────
echo "=== #1901.1 small branch (≤5000) happy path ==="
# 启动流程 f_amount=3000
SMALL_INST=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d '{"flow":"expense-threshold-countersign","variables":{"f_amount":3000,"f_applicant":"user1"}}' | jq -r '.data.processInstanceId')

# leader approves
curl -s -X POST $HOST/wf/task/execute -H "Content-Type: application/json" \
  -d "{\"taskName\":\"leader_review\",\"operator\":\"leader\",\"result\":\"approve\"}" >/dev/null

# manager approves
curl -s -X POST $HOST/wf/task/execute -H "Content-Type: application/json" \
  -d "{\"taskName\":\"manager_signoff\",\"operator\":\"manager\",\"result\":\"approve\"}" >/dev/null

SMALL_STATE=$(get_instance_state "$SMALL_INST")
assert_eq "#1901.1 small branch state=20 DONE" "$SMALL_STATE" "20"

# ─────────────────────────────────────────────────────────────────────
# #1901.2 large branch happy path (无 reject)
# ─────────────────────────────────────────────────────────────────────
echo "=== #1901.2 large branch (>5000) happy path ==="
curl -s -X POST $HOST/api/reset >/dev/null
LARGE_INST=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d '{"flow":"expense-threshold-countersign","variables":{"f_amount":8000,"f_applicant":"user1"}}' | jq -r '.data.processInstanceId')

curl -s -X POST $HOST/wf/task/execute -H "Content-Type: application/json" \
  -d "{\"taskName\":\"leader_review\",\"operator\":\"leader\",\"result\":\"approve\"}" >/dev/null

# userA/B/C all approve
for U in userA userB userC; do
  curl -s -X POST $HOST/wf/task/execute -H "Content-Type: application/json" \
    -d "{\"taskName\":\"countersign_finance\",\"operator\":\"$U\",\"result\":\"approve\"}" >/dev/null
done

LARGE_STATE=$(get_instance_state "$LARGE_INST")
assert_eq "#1901.2 large branch state=20 DONE" "$LARGE_STATE" "20"

# ─────────────────────────────────────────────────────────────────────
# #1901.3 REJECT by userA → orphan cleanup
# ─────────────────────────────────────────────────────────────────────
echo "=== #1901.3 REJECT by userA ==="
curl -s -X POST $HOST/api/reset >/dev/null
REJ_A_INST=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d '{"flow":"expense-threshold-countersign","variables":{"f_amount":8000,"f_applicant":"user1"}}' | jq -r '.data.processInstanceId')

curl -s -X POST $HOST/wf/task/execute -H "Content-Type: application/json" \
  -d "{\"taskName\":\"leader_review\",\"operator\":\"leader\",\"result\":\"approve\"}" >/dev/null

# userA REJECTS (submitType=2)
REJ_A_RES=$(curl -s -X POST $HOST/wf/task/execute -H "Content-Type: application/json" \
  -d "{\"taskName\":\"countersign_finance\",\"operator\":\"userA\",\"submitType\":2}")
REJ_A_STATE=$(echo "$REJ_A_RES" | jq -r '.data.state')
assert_eq "#1901.3 userA REJECT → state=45" "$REJ_A_STATE" "45"

# 验证 userB + userC 任务 ABANDONED (state=99, updateUser=userA)
REJ_A_TASKS=$(get_task_states "$REJ_A_INST")
echo "Tasks after userA REJECT:"
echo "$REJ_A_TASKS"

# userB task 应该 state=99 ABANDONED + updateUser=userA
USERA_B_ABANDONED=$(curl -s -X POST $HOST/wf/task/list -H "Content-Type: application/json" \
  -d "{\"processInstanceId\":$REJ_A_INST,\"taskName\":\"countersign_finance\",\"operator\":\"userB\"}" | jq -r '.data[0].taskState')
assert_eq "#1901.3 userB task ABANDONED (99)" "$USERA_B_ABANDONED" "99"

USERA_C_ABANDONED=$(curl -s -X POST $HOST/wf/task/list -H "Content-Type: application/json" \
  -d "{\"processInstanceId\":$REJ_A_INST,\"taskName\":\"countersign_finance\",\"operator\":\"userC\"}" | jq -r '.data[0].taskState')
assert_eq "#1901.3 userC task ABANDONED (99)" "$USERA_C_ABANDONED" "99"

# ─────────────────────────────────────────────────────────────────────
# #1901.4 REJECT by userB (同样验证)
# ─────────────────────────────────────────────────────────────────────
echo "=== #1901.4 REJECT by userB ==="
curl -s -X POST $HOST/api/reset >/dev/null
REJ_B_INST=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d '{"flow":"expense-threshold-countersign","variables":{"f_amount":8000,"f_applicant":"user1"}}' | jq -r '.data.processInstanceId')

curl -s -X POST $HOST/wf/task/execute -H "Content-Type: application/json" \
  -d "{\"taskName\":\"leader_review\",\"operator\":\"leader\",\"result\":\"approve\"}" >/dev/null

REJ_B_RES=$(curl -s -X POST $HOST/wf/task/execute -H "Content-Type: application/json" \
  -d "{\"taskName\":\"countersign_finance\",\"operator\":\"userB\",\"submitType\":2}")
REJ_B_STATE=$(echo "$REJ_B_RES" | jq -r '.data.state')
assert_eq "#1901.4 userB REJECT → state=45" "$REJ_B_STATE" "45"

USERB_A_ABANDONED=$(curl -s -X POST $HOST/wf/task/list -H "Content-Type: application/json" \
  -d "{\"processInstanceId\":$REJ_B_INST,\"taskName\":\"countersign_finance\",\"operator\":\"userA\"}" | jq -r '.data[0].taskState')
assert_eq "#1901.4 userA task ABANDONED (99)" "$USERB_A_ABANDONED" "99"

USERB_C_ABANDONED=$(curl -s -X POST $HOST/wf/task/list -H "Content-Type: application/json" \
  -d "{\"processInstanceId\":$REJ_B_INST,\"taskName\":\"countersign_finance\",\"operator\":\"userC\"}" | jq -r '.data[0].taskState')
assert_eq "#1901.4 userC task ABANDONED (99)" "$USERB_C_ABANDONED" "99"

# ─────────────────────────────────────────────────────────────────────
# #1901.5 REJECT by userC (同样验证)
# ─────────────────────────────────────────────────────────────────────
echo "=== #1901.5 REJECT by userC ==="
curl -s -X POST $HOST/api/reset >/dev/null
REJ_C_INST=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d '{"flow":"expense-threshold-countersign","variables":{"f_amount":8000,"f_applicant":"user1"}}' | jq -r '.data.processInstanceId')

curl -s -X POST $HOST/wf/task/execute -H "Content-Type: application/json" \
  -d "{\"taskName\":\"leader_review\",\"operator\":\"leader\",\"result\":\"approve\"}" >/dev/null

REJ_C_RES=$(curl -s -X POST $HOST/wf/task/execute -H "Content-Type: application/json" \
  -d "{\"taskName\":\"countersign_finance\",\"operator\":\"userC\",\"submitType\":2}")
REJ_C_STATE=$(echo "$REJ_C_RES" | jq -r '.data.state')
assert_eq "#1901.5 userC REJECT → state=45" "$REJ_C_STATE" "45"

USERC_A_ABANDONED=$(curl -s -X POST $HOST/wf/task/list -H "Content-Type: application/json" \
  -d "{\"processInstanceId\":$REJ_C_INST,\"taskName\":\"countersign_finance\",\"operator\":\"userA\"}" | jq -r '.data[0].taskState')
assert_eq "#1901.5 userA task ABANDONED (99)" "$USERC_A_ABANDONED" "99"

USERC_B_ABANDONED=$(curl -s -X POST $HOST/wf/task/list -H "Content-Type: application/json" \
  -d "{\"processInstanceId\":$REJ_C_INST,\"taskName\":\"countersign_finance\",\"operator\":\"userB\"}" | jq -r '.data[0].taskState')
assert_eq "#1901.5 userB task ABANDONED (99)" "$USERC_B_ABANDONED" "99"

# ─────────────────────────────────────────────────────────────────────
# 汇总
# ─────────────────────────────────────────────────────────────────────
echo -e "\n=== BDD #1901-#1905 Results ==="
echo -e "$RESULTS"
echo "PASS=$PASS  FAIL=$FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
```

---

## 3. 双端测试

| 端 | 端口 | 启动命令 |
|----|------|----------|
| **mem** (本地) | 8101 | `python main.py` |
| **pg** (服务端) | 8102 | `python main_pg.py` |

**双端 PASS 标准**:
- mem 端: 11/11 PASS (2 happy + 3 REJECT 各 3 断言 = 2 + 9 = 11)
- pg 端: 11/11 PASS
- 累计: 22/22 PASS

---

## 4. 实施依赖 (解冻后)

1. 修改 `vendor/jeeflow/engine.py` (`execute_and_jump_to_end` 函数 + FIX-T114 逻辑)
2. 实施本 BDD 脚本
3. mem + pg 双端测试
4. 报告 PASS/FAIL

---

## 5. 关联文档

- `feedback/archive/FB-0015.json` · omarchy 第 3 次贡献
- `skills/contrib/omarchy-bdd-1601-fix-t114/` · BUG-4 工件归档
- `roadmap/phase9-90day-plan.md` · Phase 9 详细计划
- `proposals/UNFREEZE-PROPOSAL-2026-09-22.md` · 解冻提案

---

⏱️ Last updated: 2026-11-10 (W46 Day 3) · BDD #1901-#1905 设计 v0.1