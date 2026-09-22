# SOP: SPI 组织调整 (spi-verify)

> **所属**：组织调整 SOP 集（与 §4 角色分工、ToT/mapping.md 配套）
> **脚本**：[`spi-verify.py`](./spi-verify.py)
> **适用**：所有 `spi/<folder>/jsons/*.json` 的修改（含 spi/dev / spi/fdep / 未来新增）

---

## 1. 何时使用

| 场景 | 是否必跑 | 期望结果 |
|------|----------|----------|
| 新增 / 删除 / 重命名 部门 | ✅ 必跑 | PASSED |
| 新增 / 删除 / 调动 用户 | ✅ 必跑 | PASSED |
| 新增 / 删除 / 改名 角色 | ✅ 必跑 | PASSED |
| 修改 `role_combinations` | ✅ 必跑 | PASSED |
| 修改 FDEP 部门（DFDEP）或占位用户 | ✅ 必跑 + 必检 FDEP 回归点 | PASSED |
| 仅修改用户姓名/post/email 等非引用字段 | ⏸️ 建议跑 | PASSED 或 PASSED WITH WARNINGS |
| 仅修改 description / version 等元数据 | ⏸️ 建议跑 | PASSED 或 PASSED WITH WARNINGS |

---

## 2. 执行步骤

### 2.1 修改前（基线确认）

```bash
SPI_FOLDER=dev python3 ToT/sop/spi-verify.py
echo "exit=$?"
# 期望: exit=0 (PASSED) 或 exit=2 (PASSED WITH WARNINGS)
# 若已 FAILED，先别动 JSON，先排查现有问题
```

### 2.2 修改 JSON

按需编辑 `spi/<folder>/jsons/{USERS,DEPTS,ROLES,ROLE_TO_USERS,DICTS}.json`。

**修改规范**（来自 ToT/mapping.md 永久约束）：

- 🔒 FDEP 部门 ID 固定为 **`DFDEP`**，不得改为 `D05` 等数字编号
- 🔒 FDEP 部门 `parent_id` 必须为 `null`（顶层根）
- 🔒 FDEP 部门 `main_leader` 与 `leader` 必须一致
- 新增 SPI 角色时必须**同时**登记到 `ROLES.json`（C1 跨表引用校验）
- 新增用户时必须设置 `deptId`（避免 C3 完整性警告）

### 2.3 修改后（回归验证）

```bash
SPI_FOLDER=dev python3 ToT/sop/spi-verify.py
echo "exit=$?"
```

**判定标准**：

| 退出码 | 含义 | 下一步 |
|--------|------|--------|
| **0** | PASSED，无任何 issue | ✅ 可继续 |
| **2** | PASSED WITH WARNINGS，有 warning 无 error | ✅ 可用，但需人工复核 warning 内容 |
| **1** | FAILED，有 error | ❌ **禁止**继续，必须修复 |

### 2.4 出错时的处置

| 错误模式 | 典型原因 | 修复方法 |
|----------|----------|----------|
| `ROLE_TO_USERS[X] 不在 SPI_ROLES` | 加了 role 但忘了在 ROLES.json 登记 | 在 ROLES.json 同步加 |
| `USERS[X].deptId=Y 不在 DEPTS` | 加了用户但部门不存在 | 先建部门，或改 deptId |
| `DEPTS[X].leader=Y 不在 SPI_USERS` | leader 引用了不存在的 uid | 先建用户，或改 leader |
| `ROLE_TO_USERS[X] 缺失用户 (按 DEPTS 应有)` | DEPTS.role_combinations 与 ROLE_TO_USERS 不一致 | 同步两边（详见 SOP §3） |
| `DEPTS[X] 存在 parent_id 循环` | parent 链形成环 | 检查 parent_id 链 |
| FDEP 回归点失败 | 修改破坏了 DFDEP / u_fdp_pm 不变量 | 回滚或修正 |

---

## 3. ROLE_TO_USERS vs DEPTS.role_combinations 一致性

SPI 内置的 C4 校验会自动比对这两边。本 SOP 的常规处理顺序：

```
修改前先确认两边结构对齐：
1. DEPTS.json 中 Dxx.role_combinations: {role_code: [uids]}
2. ROLE_TO_USERS.json 中 role_to_users: {role_code: [uids]}
两者对同一 role_code 的 uid 列表必须一致（除非刻意"分散"角色）
```

**若 DEPTS 有但 ROLE_TO_USERS 缺失** → error（用户应拥有但未登记）
**若 DEPTS 无但 ROLE_TO_USERS 多余** → warning（角色分配与部门定义不符，需人工判断）

---

## 4. FDEP 专属回归点（spi/dev 必检）

spi-verify.py 在 `SPI_FOLDER=dev` 时自动执行以下 16 条不变量检查：

| # | 检查项 | 期望 |
|---|--------|------|
| 1 | DFDEP 部门存在 | tree keys 含 DFDEP |
| 2 | DFDEP.parent_id = null | 顶层根 |
| 3 | DFDEP.leader = u_fdp_pm | self-led |
| 4 | DFDEP.main_leader = u_fdp_pm | self-led |
| 5 | u_fdp_pm.deptId = DFDEP | 占位用户挂在 DFDEP |
| 6 | u_fdp_pm.dept_chain = [DFDEP] | 单元素链（顶层叶子） |
| 7–18 | 6 个 fdep_* 角色存在 + ROLE_TO_USERS 映射 | 全部 → [u_fdp_pm] |

**任一不变量失败 = FAILED，禁止继续。**

---

## 5. 留档要求

按 ToT/README.md §1 第 3 条例外审批规则：

- 每次跑 spi-verify.py **FAILED → PASSED** 的修复过程，需在本 SOP 的 `变更日志` 加一行
- 涉及 FDEP 部门 / 占位用户的调整，需同步更新 `ToT/mapping.md`
- 跑测试时不留中间文件（脚本是无状态的）

---

## 6. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：spi-verify.py 配套 SOP；定义 6 步流程 + FDEP 16 条不变量；首次回放成功（spi/dev 修复 ROLES.json 漏登记后 PASSED） |
| v0.2 | 2026-09-22 | 脚本增强：① spi/fdep 等无 `verify()` 的 SPI_FOLDER 优雅降级（warning + 继续），不崩溃；② 负向测试通过：故意把 DFDEP 改名为 D05，脚本抓到 3 条违规（DFDEP 不存在 / u_fdp_pm.deptId 错 / dept_chain 错），exit=1 FAILED；恢复后 exit=0 PASSED |
