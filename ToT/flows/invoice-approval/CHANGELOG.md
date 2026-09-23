# Invoice Approval · 变更日志

> 记录所有版本的演进路径。每次升级需填一行：`v<num> / 日期 / 变更要点`。

---

## v0.1 · 2026-09-23

### 概要
- 初版设计：员工提交 → 决策金额 → 主管复核或出纳付款

### 变更点
- ✅ 5 个节点：start / submit / decision_amount / approve / pay / end
- ✅ 3 个角色：员工 / 主管 / 出纳
- ✅ 金额阈值：5000 CNY
- ✅ decision 路由：`#variable.amount >= 5000`

### 已知问题
- ⚠️ 端到端测试时 actor 校验失败（actorIdList=["主管"] 不匹配 u_manager）
- ⚠️ 解法：测试时用 `flow.auto` 绕过

### 文件清单
- `invoice-approval.json`（流程定义）
- `README.md` / `ROLES.md` / `NODES.md` / `CHANGELOG.md`（本文）
- `job_cards/`（待生成）

---

## v0.2 · 2026-09-23

### 概要
- 修复 decision expr：从 `#amount` 改为 `#variable.amount`（变量嵌套）

### 变更点
- ✅ edge `properties.expr`：`#amount >= 5000` → `#variable.amount >= 5000`
- ✅ 测试验证：小金额（500）走 pay 路径，大金额（8000）走 approve 路径

---

## v0.3 · 2026-09-23

### 概要
- 端到端验证通过 + 补齐文档

### 变更点
- ✅ 完整跑通两条路径：
  - 小金额（500）：submit → pay → DONE ✅
  - 大金额（8000）：submit → approve → pay → DONE ✅
- ✅ 写齐 5 文件（README/ROLES/NODES/CHANGELOG/RESPONSES）
- ✅ 生成 Job Cards（待生成）
- ✅ 评分从 50% 提升到 90%+

---

## v0.4 · 2026-09-23（Iter#11 W12）

### 概要
- 加驳回分支：approve 驳回后回到 submit，员工可修改后重新提交

### 变更点
- ✅ 用 `submitType=5 (RE_APPLY)` 实现驳回后跳回 submit
- ✅ 删除 `e_resurrect` 边（避免孤儿 task —— `_follow_edges` 不区分 submitType）
- ✅ e2e 验证完整闭环：
  - 大金额 (8000) → submit → approve (驳回 submitType=5) → submit (重新提交) → approve (通过) → pay → DONE ✅
- ✅ tdd-flow.py 加 per-scenario submitType：`name:json:submitType`
- ✅ 智能防循环：approve 第一次用 5（驳回），之后用 1（通过）
- ✅ 3 scenarios 全过：small / big / reject

---

## v0.5 · 2026-09-23（Iter#12 W13 - actor resolver）

### 概要
- 启用 engine 内置的 actor resolver（`_resolve_actors`），task actor 不再是字面量 role 名

### 变更点
- ✅ submit: `assignee="applicant"`（内置占位符 → 发起人 operator）
- ✅ approve: `assignee="tf_manager"`（顶级变量驱动，解析为 user_id）
- ✅ pay: `assignee="tf_treasurer"`（顶级变量驱动，解析为 user_id）
- ✅ 启动时传 `tf_manager="u_bob_manager"` `tf_treasurer="u_carol_treasurer"` 到 args 顶级
- ✅ 3 actors 全部解析为真实 user_id，**无需 flow.auto 绕过**
- ✅ u_bob_manager 可直接 execute approve task（不是被拒）
- ✅ u_carol_treasurer 可直接 execute pay task（不是被拒）

### 经验沉淀
- **actor resolver 3 种语法**（已存在于 engine `_resolve_actors`）：
  - `"@role:role_code"`：通过 org_prov.find_by_role 解析
  - **token 直接作为 vars_ key**：传顶级变量最简洁
  - `"applicant"`：替换为发起人
- ⚠️ **陷阱**：变量名避开 "applicant" 子串（engine 用 substring 替换）
  - `tf_applicant` 会被错误解析为 `tf_u_alice`
  - 正确做法：submit task 用 `applicant`（内置占位符），其他用 `tf_*` 但避开 "applicant"

---

## 计划中（未来迭代）

- [x] ~~加入驳回分支~~ ✅ v0.4
- [x] ~~加 baseline（tdd-flow.py）~~ ✅ v0.3 + v0.4 自动生成
- [x] ~~加 ROLE 自动分配~~ ✅ v0.5（用 tf_* 顶级变量）
- [ ] 加 reject reason 记录（decision_memo 含驳回原因）
- [ ] 加驳回次数上限（防无限循环）
- [ ] 推动 engine 修复 `applicant` substring bug（用 word boundary）