# FB-0007 复现验证手册 (给 bro)

> **FB**: FB-0007 (BUG-2 / cashier_pay 幽灵 DOING / P0 / engine)
> **来源**: flowuser 远程复现, 2026-09-21
> **目的**: 让 bro 在本地 100% 复现, 定位根因, 起草 FIX-T112

---

## 1. 已知信息 (来自 flowuser)

### 1.1 流程定义 (取件码 bug2-bro-json)

```
apply → decision_amount (按金额分流)
         ├─ <5000 → mgr_approve → decision_mgr
         │                          ├─ tf_mgr_decision==1 → cashier_pay
         │                          └─ tf_mgr_decision==2 → end_no  ← REJECT 路径
         └─ ≥5000 → dir_approve → decision_dir
                                    ├─ tf_dir_decision==1 → cashier_pay
                                    └─ tf_dir_decision==2 → end_no  ← REJECT 路径
```

**关键节点**: `decision_mgr` / `decision_dir` 各有 2 出边 (approve + reject)

### 1.2 现象 (3 实例 + 1 对照)

| 实例 | amount | 分支 | mgr/dir decision | 期望 state | 实际 state | cashier_pay |
|------|--------|------|-----------------|-----------|-----------|------------|
| 92099018922273 | 4800 | mgr | reject (2) | 45 | **10 ❌** | **DOING ❌** |
| 92099066975525 | 8000 | dir | reject (2) | 45 | **10 ❌** | **DOING ❌** |
| 92099077616937 | 999 | mgr | approve (1) | 20 | **20 ✅** | DONE ✅ |

**3/3 触发**: reject 路径 BUG-2 必现, happy path 正常.

### 1.3 根因猜测 (flowuser 推断)

> `vendor/jeeflow/engine.py:_evaluate_decision` 遍历出边时**没有短路**,
> 即使第一条 expr=true, 仍继续评估后续出边.

类似 BUG-1 根因 (`engine.py:210 _follow_edges`), 但发生在 decision 节点而非 task 节点.

---

## 2. 本地复现步骤 (bro 执行)

### 2.1 准备

```bash
# 1. 启动本地 memory backend
cd /opt/jupyter/src/RD/projects/jeeFlow
.venv/bin/python main.py &  # 监听 8101

# 2. 健康检查
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/stats/overview \
  -H 'Content-Type: application/json' -d '{}' | jq

# 期望: { "code": 0, "data": {...} }
```

### 2.2 部署流程定义

```bash
# 1. 从 attachments/ 取完整 JSON
# DM flowuser 取 bug2-bro-json 内容 (取件码机制, 见 FB-0007-INDEX.md)

# 2. 保存为 tdd/bug2_bro_repro.json
# 注意: processDefineId 在用户实例上是 232, 本地会从新分配

# 3. deploy + save
DESIGN_ID=$(curl -s -X POST http://127.0.0.1:8101/wf/processDesign/save \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "bug2_bro_repro",
    "displayName": "BUG-2 复现",
    "type": "approval",
    "content": '"$(cat tdd/bug2_bro_repro.json | jq -c . | sed 's/"/\\"/g')"'
  }' | jq -r .data.id)

DEFINE_ID=$(curl -s -X POST http://127.0.0.1:8101/wf/processDesign/deploy \
  -H 'Content-Type: application/json' \
  -d "{\"id\": $DESIGN_ID}" | jq -r .data.processDefineId)

echo "DESIGN_ID=$DESIGN_ID DEFINE_ID=$DEFINE_ID"
```

### 2.3 启动 3 个实例 (2 BUG + 1 对照)

```bash
# 实例 1: mgr 路径 reject (BUG)
INSTANCE_1=$(curl -s -X POST http://127.0.0.1:8101/wf/processInstance/startAndExecute \
  -H 'Content-Type: application/json' \
  -d "{
    \"processDefineId\": \"$DEFINE_ID\",
    \"operator\": \"user1\",
    \"title\": \"BUG-2-1 mgr reject\",
    \"assignees\": {\"apply\": \"user1\", \"mgr_approve\": \"manager\", \"dir_approve\": \"director\"},
    \"variables\": {
      \"submitType\": 0,
      \"f_amount\": 4800,
      \"u_userId\": \"user1\",
      \"u_realName\": \"用户1\"
    }
  }" | jq -r .data.processInstanceId)

# mgr reject
TASK_ID=$(curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -H 'Content-Type: application/json' \
  -d '{"operator": "manager", "pageNum": 1, "pageSize": 20}' | jq -r '.data[0].id')

curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -H 'Content-Type: application/json' \
  -d "{
    \"processTaskId\": \"$TASK_ID\",
    \"submitType\": 2,
    \"operator\": \"manager\",
    \"args\": {\"tf_mgr_decision\": 2}
  }" | jq

# ⚠️ 预期: instance.state=45 (BUG) 或 instance.state=10 (BUG-2 实际)

# 实例 2 + 3: 类似, 略
```

### 2.4 验证现象

```bash
# 详情
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/detail \
  -H 'Content-Type: application/json' \
  -d "{\"id\": \"$INSTANCE_1\"}" | jq

# 看:
# - .data.state (期望 45, 实际 10 = BUG)
# - .data.tasks[] (期望 cashier_pay 不存在, 实际可能 DOING)

# 高亮
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/highLight \
  -H 'Content-Type: application/json' \
  -d "{\"id\": \"$INSTANCE_1\"}" | jq
```

---

## 3. 根因定位 (bro 执行)

### 3.1 假设 1: decision 节点遍历出边未短路 (flowuser 猜测)

```bash
# 查 engine.py:_evaluate_decision
grep -n "_evaluate_decision" vendor/jeeflow/engine.py

# 看实现, 是否有短路:
# for edge in edges:
#     if eval(expr):
#         return edge.target  # ✅ 短路
#         create_tasks_for_all_evaluating_edges  # ❌ 没短路
```

### 3.2 假设 2: 类似 BUG-1 (FIX-T110) 的 task 多出边问题

```bash
# BUG-1 修的是 task 节点多出边致 end 提前遍历
# BUG-2 可能是 decision 节点多出边致 cashier_pay 提前遍历

# 对比 FIX-T110 修复
grep -n "FIX-T110\|W012" vendor/jeeflow/engine.py docs/BUGS.md
```

### 3.3 假设 3: cashier_pay task 在 reject 路径被错误创建

```bash
# 即使 _evaluate_decision 正确返回 end_no 边,
# 引擎可能在 _create_task 时把 cashier_pay 也创建了?

# 查 engine.py:_create_task 调用链
grep -n "_create_task\|_follow_edges" vendor/jeeflow/engine.py | head -20
```

---

## 4. 起草 FIX-T112 方案 (bro 写)

### 4.1 方案 A: 在 decision 节点短路 (推荐)

```python
# vendor/jeeflow/engine.py:_evaluate_decision
def _evaluate_decision(self, node, vars_):
    edges = node.outgoing
    for edge in edges:
        if self._eval_expr(edge.properties.get("expr", ""), vars_):
            return edge.target  # ✅ 短路: 只返回第一个 true 边
    return edges[0].target  # 兜底: 第一条
```

### 4.2 方案 B: 加 verify 规则 (W013)

```python
# vendor/jeeflow/verify.py (新增 W013)
def W013(workflow):
    """decision 节点出边应配显式 expr, 避免 fallback 到第一条"""
    for node in workflow.nodes:
        if node.type == "snaker:decision":
            for edge in node.outgoing:
                if not edge.properties.get("expr"):
                    warn(f"decision '{node.id}' 出边 '{edge.id}' 无 expr, fallback 风险")
```

### 4.3 修复后 BDD

```bash
# bdd/bdd-XXXX-fix-t112-decision-reject-no-cashier.sh
# 用 tdd/bug2_bro_repro.json 跑:
# 实例 1 (mgr reject): 期望 state=45, 无 cashier_pay task
# 实例 2 (dir reject): 期望 state=45, 无 cashier_pay task
# 实例 3 (mgr approve): 期望 state=20, cashier_pay DONE
```

---

## 5. 申请流程 (给 bro)

```
1. 本地复现 → 100% 触发 BUG-2
2. 定位根因 → 验证 flowuser 猜测
3. 起草 FIX-T112 (按 §4 方案 A 或自创)
4. 修改 vendor/jeeflow/engine.py
5. 加 W013 (可选, 防御性)
6. 加 BDD 回归 (bdd-XXXX-fix-t112-...)
7. 双端验证 (MEM + PG)
8. 通知 flowuser 闭环
9. 更新 FB-0007 status=closed + lessons_learned
10. 同步 README.md / weekly / metrics
```

---

## 6. 风险与注意

| 风险 | 缓解 |
|------|------|
| 决策短路影响其他场景 | 全量 BDD 回归 (P0+P1+Phase2) |
| flowuser 实例独有 (PG 后端) | 双端验证 |
| 不在本地复现 (PG vs MEM 差异) | 同步跑 PG 后端 |
| 修了 reject 路径, 影响 approve 路径 | 三个实例对照 (2 BUG + 1 happy) |

---

## 7. 涉及文件位置

- `skills/feedback/inbox/FB-0007.json` (登记)
- `skills/feedback/attachments/FB-0007-INDEX.md` (附件清单)
- `skills/feedback/retrospectives/2026-09-21-users-md-task.md` (协同复盘)
- `docs/BUGS.md §111` (BUG-1 历史, 类似 BUG 应对参考)

⏱️ Last updated: 2026-09-21 · FB-0007 / FIX-T112 起草中
