# Iteration #12 · 2026-09-23 · W13 · actor resolver（role → user_id）

> **驱动**：W13（Iter#9 留下的 TODO：actor 是 role 名而非 user_id）
> **核心发现**：engine `_resolve_actors` 已支持 3 种 actor 解析语法（@role:/变量/applicant），**无需新代码**
> **结论**：✅ **actor 全解析为真实 user_id**，**无需 flow.auto 绕过**

---

## 1. 时间线（~1.5 小时）

| 时段 | 工作 |
|------|------|
| 0~20 min | 读 engine.py 找 actor 机制，发现 `_resolve_actors` 已支持 3 种语法 |
| 20~40 min | 改造 invoice-approval.json 用 tf_* 变量 |
| 40~60 min | e2e 验证：发现 `tf_applicant` 被错误解析为 `tf_u_alice`（substring bug） |
| 60~75 min | 改用 `applicant` 占位符 + 顶级变量传 tf_manager/tf_treasurer |
| 75~100 min | tdd-flow 加 `--top-vars` 参数 |
| 100~120 min | 文档更新 + ea-compliance + 写 iteration |

---

## 2. 核心发现：actor resolver 早就在了

`vendor/jeeflow/engine.py:759` `_resolve_actors` 已支持：

```python
# 1. @role:role_code → org_prov.find_by_role
if token.startswith("@role:"):
    role_actors = await self.org_prov.find_by_role(token[6:])
    ...

# 2. applicant 占位符 → inst.operator
if "applicant" in token:
    token = token.replace("applicant", inst.operator)

# 3. 变量 key → vars_[token]
if token in vars_:
    val = vars_[token]
    actors.append(str(val))

# 4. fallback: assignees_map[node.id] 或字面量
```

W13 不是"创造" resolver，而是"启用"已有 resolver。

---

## 3. invoice-approval v0.5 设计

| 节点 | assignee | 启动时传 | 解析结果 |
|------|----------|----------|----------|
| submit | `"applicant"` | operator="u_alice" | actor=`['u_alice']` |
| approve | `"tf_manager"` | tf_manager="u_bob_manager" | actor=`['u_bob_manager']` |
| pay | `"tf_treasurer"` | tf_treasurer="u_carol_treasurer" | actor=`['u_carol_treasurer']` |

**关键**：tf_* 变量必须放 args 顶级（不进 `variable` 嵌套），因为 `_resolve_actors` 直接查 vars_ 顶级。

---

## 4. ⚠️ 关键 Bug：`applicant` substring 替换

```python
# engine _resolve_actors 行为：
if "applicant" in token:
    token = token.replace("applicant", inst.operator)
# 当 token = "tf_applicant", inst.operator = "u_alice" 时：
# → token = "tf_u_alice"（错误！）
```

**修复**：submit task 直接用 `"applicant"`（内置占位符），其他 task 用 `tf_*` 但**避开 `applicant` 子串**。

未来工作：建议推动 engine 改成 word boundary 匹配（`token == "applicant" or token.startswith("applicant,") or ...`）。

---

## 5. tdd-flow 增强

- 新增 `--top-vars` 参数：传顶级变量（用于 tf_* actor resolver）
- run_path 接受 `top_vars` 参数
- generate_md 显示 top_vars

```bash
./ToT/bin/jf python3 ToT/sop/tdd-flow.py ToT/flows/invoice-approval.json \
    --scenarios 'small:{...}|big:{...}' \
    --top-vars '{"tf_manager":"u_bob_manager","tf_treasurer":"u_carol_treasurer"}' \
    --save-baseline
```

---

## 6. 测试结果

### 6.1 e2e 验证（用真实 user_id 不用 flow.auto）

```
Test: tf_* 顶级变量
  instance=92281787681801
  submit: actor=['u_alice']                  ← applicant 占位符
  approve: actor=['u_bob_manager']           ← tf_manager 解析
  pay: actor=['u_carol_treasurer']           ← tf_treasurer 解析

  → 用 u_alice 执行 submit → code=0 成功
  → 用 u_bob_manager 执行 approve → code=0 成功
  → 用 u_carol_treasurer 执行 pay → code=0 成功
  → FINAL state=DONE (20)
```

### 6.2 tdd-flow multi-scenario

```
[small] pay actors=['u_carol_treasurer']          ← 解析成功
[big] approve actors=['u_bob_manager']           ← 解析成功
       pay actors=['u_carol_treasurer']          ← 解析成功
[reject] approve actors=['u_bob_manager'] x2      ← 2 次到 approve 都正确
         pay actors=['u_carol_treasurer']        ← 解析成功

✅ PASSED — 3 scenarios all DONE
```

### 6.3 ea-compliance + 兼容性

- ✅ ea-compliance 43/43 PASS
- ✅ fdep 兼容性测试通过（happy+DONE, reject+REJECT）
- ✅ invoice-approval completeness 100%

---

## 7. 闭环示意

```
┌── "actor 是 role 名不是 user_id" ──┐
↓                                  │
读 engine._resolve_actors          │
↓                                  │
发现 3 种 resolver 语法已存在      │
↓                                  │
改 invoice-approval 用 tf_* 变量   │
↓                                  │
发现 tf_applicant 被 substring bug │
↓                                  │
改用 applicant + tf_manager/tf_treasurer │
↓                                  │
e2e 验证：3 actor 全部解析为 user_id │
↓                                  │
无需 flow.auto 绕过                │
↓                                  │
tdd-flow --top-vars                │
↓                                  │
→ 飞轮第 12 圈（actor resolver）✅ │
```

---

## 8. 度量（飞轮 12 圈累积）

| 指标 | Iter#9 | Iter#10 | Iter#11 | **Iter#12** |
|------|--------|---------|---------|-------------|
| §9 检查项 | 43 | 43 | 43 | **43** |
| **actor resolver** | ❌ 字面量 | ❌ 字面量 | ❌ 字面量 | **✅ user_id** |
| **无需 flow.auto** | ❌ | ❌ | ❌ | **✅** |
| tdd-flow 变量类型 | 1 | 2 | 2 | **3 (variable+top_vars+scenarios)** |

**关键变化**：从"必须 flow.auto 绕过"→"task actor 精确为真实 user_id"。

---

## 9. 经验沉淀

### 9.1 actor resolver 用法选择
| 场景 | 推荐语法 | 示例 |
|------|----------|------|
| 申请节点（发起人提交） | `"applicant"` | submit |
| 固定角色（依赖 org_prov） | `"@role:fdp_intake"` | intake（org_prov 查 role→user_ids） |
| 动态指定（实例级） | `"tf_<role>"` + 传顶级变量 | approve（tf_manager="u_bob"） |

### 9.2 顶级 vs 嵌套变量
- **嵌套**（`variable.X`）：业务变量、决策路由引用
- **顶级**（args 顶层）：actor resolver、跨节点流转变量

### 9.3 避坑清单
- ⚠️ **变量名避开 "applicant"**：用 `"applicant"` 或改 substring bug
- ⚠️ **变量名避开 Python 关键字**：如 `for` `class` `if`
- ⚠️ **测试时**：传 tf_* + flow.auto 兜底（避免 actor 解析失败时流程卡住）

---

## 10. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第十二轮迭代 · W13 actor resolver**：① **核心发现** engine `_resolve_actors` 已支持 3 种 actor resolver 语法（@role:/变量/applicant）；② **invoice-approval v0.5 启用 resolver**：submit=`applicant` / approve=`tf_manager` / pay=`tf_treasurer`；③ **传顶级变量** tf_manager / tf_treasurer 到 args 顶层；④ **发现 substring bug**（`tf_applicant` 被错误解析），改用 `applicant` 占位符；⑤ **e2e 验证**：3 actor 全部解析为真实 user_id，**无需 flow.auto**；⑥ **tdd-flow 加 `--top-vars` 参数**；⑦ **3 scenarios 全过**（actor 都正确解析）；⑧ ea-compliance 43/43 PASS + fdep 兼容；⑨ 新增 iterations/2026-09-23_actor-resolver.md。 |