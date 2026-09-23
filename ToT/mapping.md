# FDEP 角色 → SPI 映射计划（Mapping Plan）

> 本文档是 **ToT/ 内的提案**，尚未生效到任何 SPI 数据文件。
> 落地修改需你确认。

---

## 1. 映射原则

FDEP.json 的 `assignee` 字段使用**抽象角色编码**（R3 / R6 / R7 等，定义见 `ToT/README.md#4-角色分工`）。
抽象角色最终要落到**具体执行人**，映射链为：

```
FDEP.json assignee (R3)
   ↓ 通过 SPI 角色名
spi/dev  ROLE_TO_USERS (e.g., "fdep_pm")
   ↓ 解析为 uid 列表
spi/dev  USERS.json (u_fdp_xxx)
```

---

## 2. FDEP 节点 → SPI 角色映射（v1.1 实测落地）

| FDEP 节点 | 阶段 | 抽象 R | SPI 角色名 | assignee 实际值 | TDD 实测 |
|-----------|------|--------|------------|----------------|----------|
| `stage_intake` | 0. 接收/登记 | R3 | `fdep_intake` | `u_fdp_pm`（v0.6.2 起直接） | ✅ DONE |
| `stage_pm` | 1. RML 立项 | R3 | `fdep_rml` | `u_fdp_pm` | ✅ DONE |
| `stage_design` | 2. 架构/接口设计 | R7 | `fdep_arch` | `u_fdp_pm` | ✅ DONE |
| `stage_dev` | 3. 开发实现 | R2 | `fdep_dev` | `u_fdp_pm` | ✅ DONE |
| `stage_review` | 4. 评审/验收/发布 | R6 | `fdep_review` | `u_fdp_pm` | ✅ DONE |
| `stage_feedback` | 5. 反馈/知识沉淀 | R5 | `fdep_kb` | `u_fdp_pm` | ✅ DONE |
| `end_rejected` | 驳回 | R3 | — | — | ⏳ 手动 orchestration |

**v0.6.2 重大变更**：
- assignee 从抽象 R 角色 (R3/R6/R7) → 直接 `u_fdp_pm`（占位场景）
- SPI 角色名 (fdep_*) 保留为**语义标签**（写在 `text.value` 与 `metadata`）
- **原因**：TDD 实跑发现引擎不会自动通过 SPI 把 `fdep_rml` 解析到 `u_fdp_pm`（需要 `assignmentHandler`，v0.7+ 引入）
- **占位**：本版本所有 FDEP 节点由 `u_fdp_pm` 担当（一人分饰 6 角），流程可跑通但不满足真实分工

---

## 3. spi/dev 组织扩展

### 3.0 永久约束（FDEP 部门定义，2026-09-22 用户确认）

> 🔒 **FDEP 部门是顶层固定 ID，无上级部门。**

- 部门 ID：**`DFDEP`**（固定，永不改为 `D05` 等数字编号）
- `parent_id`：**`null`**（与 D99 总经办同级，不挂任何部门）
- `main_leader` 与 `leader` 一致（自领，无上级主领导）
- 该规则适用于 **所有 SPI 数据集**（spi/dev / spi/fdep / 未来新增）

### 3.1 新增部门 `DFDEP FDEP协作组`（顶层，无 parent）

```jsonc
"DFDEP": {
  "name": "FDEP协作组",
  "parent_id": null,
  "leader": "u_fdp_pm",
  "main_leader": "u_fdp_pm",
  "role_combinations": {
    "fdep_intake":   ["u_fdp_pm"],
    "fdep_rml":      ["u_fdp_pm"],
    "fdep_arch":     ["u_fdp_pm"],
    "fdep_dev":      ["u_fdp_pm"],
    "fdep_review":   ["u_fdp_pm"],
    "fdep_kb":       ["u_fdp_pm"]
  }
}
```

### 3.2 新增占位用户 `u_fdp_pm`

```jsonc
"u_fdp_pm": {
  "name": "占位·待分配",      // 真实姓名待定
  "post": "FDEP 流程占位",
  "deptId": "DFDEP",
  "level": "P5",
  "email": "fdp-pm@flowmatrix.io"
}
```

### 3.3 ROLE_TO_USERS.json 新增 6 个 SPI 节点角色

```jsonc
{
  "fdep_intake":   ["u_fdp_pm"],
  "fdep_rml":      ["u_fdp_pm"],
  "fdep_arch":     ["u_fdp_pm"],
  "fdep_dev":      ["u_fdp_pm"],
  "fdep_review":   ["u_fdp_pm"],
  "fdep_kb":       ["u_fdp_pm"]
}
```

---

## 4. 待决（v0.2 候选改进）

| Q# | 问题 | 默认值 | 状态 |
|----|------|--------|------|
| Q1 | FDEP 部门 ID | `DFDEP`（顶层、无 parent） | ✅ 已锁定（用户 2026-09-22 确认） |
| Q2 | 占位用户 uid | `u_fdp_pm` | ✅ 已确认 |
| Q3 | 占位用户 `name` | `占位·待分配` | ✅ 已确认 |
| Q4 | SPI 角色命名风格 | `fdep_*` | ✅ 已确认 |
| Q5 | 是否落地到 spi/dev/jsons/*.json | 是（v0.7 落地） | ✅ 已完成 |
| Q6 | 是否同步修改 spi/fdep | 否（仅 spi/dev） | ✅ 已决定 |

### 4.1 仍待决

| Q# | 问题 | 备注 |
|----|------|------|
| Q7 | 占位用户 `u_fdp_pm` 何时由真实人员替换？ | 待业务侧招聘/分配 |
| Q8 | 6 个 SPI 角色何时拆给不同真实人员？ | 与 Q7 同步 |

---

## 5. 关联文档

- `ToT/README.md#4-角色分工` — 抽象角色定义
- `ToT/README.md#1-读写边界规则` — §1.3 例外审批流程（本提案走例外审批）
- `ToT/flows/fdep.json` — 流程定义
- `spi/dev/jsons/DEPTS.json` — ✅ 已修改（v1.3.0）
- `spi/dev/jsons/USERS.json` — ✅ 已修改（v1.1.0）
- `spi/dev/jsons/ROLE_TO_USERS.json` — ✅ 已修改（v1.1.0）

---

## 6. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：FDEP→SPI→用户 三层映射；spi/dev 扩展提案；6 个待决 Q |
| v0.6 | 2026-09-22 | 用户确认为基线 |
| v0.7 | 2026-09-22 | **已落地** spi/dev 三个 JSON（依据 ToT/README.md §1 例外审批，正当事由：FDEP 流程需要可执行的占位用户）：①USERS.json 加 `u_fdp_pm`（v1.0.0→v1.1.0）；②DEPTS.json 加 `D05 FDEP协作组`（v1.1.0→v1.2.0）；③ROLE_TO_USERS.json 加 6 个 FDEP 节点角色（v1.0.0→v1.1.0）；JSON 校验通过 |
| v0.8 | 2026-09-22 | **修正命名不一致**：ROLE_TO_USERS / D05.role_combinations 统一为 `fdep_*` 前缀（之前混入 `fdp_*`）；删除 D05 中的 `fdep_pm`（与 ROLE_TO_USERS 不存在对应，改用 `fdep_intake`/`fdep_rml` 两个 R3 子角色）；当前 6 个角色：fdep_intake / fdep_rml / fdep_arch / fdep_dev / fdep_review / fdep_kb，全部指向 `u_fdp_pm` |
| v0.9 | 2026-09-22 | **用户永久规则**：FDEP 部门 ID 固定为 `DFDEP`（顶层，parent_id=null，与 D99 同级）；从 `D05 FDEP协作组` 迁移到 `DFDEP FDEP协作组`；`main_leader` 与 `leader` 一致（`u_fdp_pm`）；同步更新 `spi/dev/jsons/USERS.json`（u_fdp_pm.deptId）与 `DEPTS.json`（v1.2.0→v1.3.0，新增"双顶层根"结构说明）；§3.0 新增永久约束 |
| v1.0 | 2026-09-22 | **关联 SOP 落地**：新增 `ToT/sop/spi-verify.md`（v0.2）+ `ToT/sop/spi-verify.py`，封装组织调整的必跑流程。**发现并修复回归问题**：本轮 SOP 首次回放 spi/dev `verify()` 抓到 6 条 error —— 我此前把 6 个 `fdep_*` 加进 `ROLE_TO_USERS.json` 但漏加进 `ROLES.json`，SPI C1 跨表引用校验立刻报错。已在 `spi/dev/jsons/ROLES.json` 同步登记（v1.0.0→v1.1.0，角色数 8→14），再次回放 PASSED。**负向测试通过**：故意 DFDEP→D05 改名，脚本抓到 3 条违规，exit=1；恢复后 exit=0。 |
| v1.1 | 2026-09-22 | **FDEP.json v0.5 TDD 实跑落地反馈**：assignee 列从抽象 R 角色改为 `u_fdp_pm` 直接赋值；SPI 角色名 (fdep_*) 降级为语义标签。原因：实跑发现引擎不自动通过 SPI 把 `fdep_rml` 解析到 `u_fdp_pm`，需 `assignmentHandler`（v0.7+ 引入）。happy path 实测：6 阶段全 DONE，state=20。 |
