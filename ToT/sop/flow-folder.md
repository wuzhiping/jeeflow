# SOP: 流程定义组织规范 (flow-folder)

> **所属**：组织 SOP 集（与 spi-verify / tdd-flow 并列）
> **永久规则**：见 `ToT/README.md#10-流程定义组织规范`
> **适用**：所有 `ToT/flows/<name>.json`

---

## 1. 强制约束（来自 §10 永久规则）

| # | 规则 | 验证方式 |
|---|------|----------|
| 1 | 流程 JSON 放在 `ToT/flows/<name>.json` | `flow-lint.py` 检查路径前缀 |
| 2 | **文件名必须全小写**（如 `fdep.json`，不允许 `FDEP.json`） | `flow-lint.py` 检查 `stem == stem.lower()` |
| 3 | JSON 顶层 `name` 字段 == 文件名（去掉 `.json` 后，因 #2 已确保全小写） | `flow-lint.py` 比对 |
| 4 | 同名文件夹 `ToT/flows/<name>/` 必须存在（小写，与文件名一致） | `flow-lint.py` 检查目录 |
| 5 | 同名文件夹内必须含 4 个文件：`README.md` `ROLES.md` `NODES.md` `CHANGELOG.md` | `flow-lint.py` 检查文件存在 |
| 6 | `NODES.md` 必须包含 JSON 中所有 `node.id` 的工作说明 | `flow-lint.py` 比对 ID 集合 |
| 7 | `ROLES.md` 必须包含 JSON 中所有非空 `properties.assignee` 的角色清单 | `flow-lint.py` 比对 |

---

## 2. 文件职责矩阵

| 文件 | 职责 | 内容要求 |
|------|------|----------|
| `README.md` | 流程总览 | 用途 / 适用场景 / 高层说明 / 节点列表索引 / 角色清单索引 / 变更索引 |
| `ROLES.md` | 角色清单 | 抽象 R 角色 + SPI 角色 + 具体用户 + 在本流程中的职责 |
| `NODES.md` | 节点工作手册 | 每个 node.id 一节，含：节点说明 / 输入 / 输出 / 工作步骤 / 注意事项 |
| `CHANGELOG.md` | 变更记录 | 版本号 / 日期 / 改动 / 测试结果 / 关联 commit |

---

## 3. 模板

### 3.1 `README.md` 模板

```markdown
# <流程名>（<流程 displayName>）

> JSON 定义：`<NAME>.json` (version: x.y.z)
> 适用场景：<一句话>
> 发起者：<R1a / 任何来源>

## 概览

<2-3 段流程说明>

## 节点清单

详见 [NODES.md](./NODES.md)

| 节点 ID | 类型 | 阶段 | 角色 |
|---------|------|------|------|
| ... | ... | ... | ... |

## 角色清单

详见 [ROLES.md](./ROLES.md)

## 变更记录

详见 [CHANGELOG.md](./CHANGELOG.md)
```

### 3.2 `ROLES.md` 模板

```markdown
# 角色清单（Roles）

| 抽象 R | SPI 角色 | 实际用户 | 流程节点 | 备注 |
|--------|----------|----------|----------|------|
| R1a | — | 任意 | start | 流程发起 |
| R3 | fdep_intake | u_fdp_pm | stage_intake | PM 接收窗口 |
| ... | ... | ... | ... | ... |
```

### 3.3 `NODES.md` 模板

```markdown
# 节点工作手册（Node Manual）

## start（snaker:start）

- **说明**：任何来源的请求入口
- **输入**：用户/Agent 提交
- **输出**：触发 stage_intake
- **工作步骤**：
  1. 接收请求
  2. 不做内容判定
- **注意事项**：
  - 不限制提交者角色
  - 不写实现代码

## stage_intake（snaker:task）

- **说明**：PM 接收窗口
- **输入**：start 触发
- **输出**：登记记录 → decision_intake
- **工作步骤**：
  1. 读取请求
  2. 决定立项（submitType=1）或驳回（submitType=2）
  3. 落档到 `ToT/pm/intake/`
- **注意事项**：
  - 决策结果必须显式记录
  - 驳回必须写理由
- **关联角色**：R3 / fdep_intake / u_fdp_pm

## decision_intake（snaker:decision）

- **说明**：决策路由
- **输入**：stage_intake 完成
- **输出**：submitType=1 → stage_pm; submitType=2 → end_rejected; 其他 → stage_pm（默认）
- **工作步骤**：
  - 引擎自动根据 submitType 评估 expr
- **注意事项**：
  - 默认边兜底，避免孤儿 task（W013 警告）
```

### 3.4 `CHANGELOG.md` 模板

```markdown
# 变更记录（CHANGELOG）

| 版本 | 日期 | 改动 | 引擎测试 | 备注 |
|------|------|------|----------|------|
| v0.1 | 2026-09-22 | 初始骨架 | tdd-flow.py: PASSED | — |
| v0.6.2 | 2026-09-22 | 修 W012 + 改 assignee 为 u_fdp_pm | tdd-flow.py: PASSED | happy path 全 DONE |
```

---

## 4. 验证流程

### 4.1 新增流程时

```bash
# 1. 创建 JSON
$EDITOR ToT/flows/<NAME>.json
#   - 顶层 name 字段 == "<name>.lower()"
#   - 顶层 version 字段

# 2. 创建同名文件夹
mkdir ToT/flows/<NAME>

# 3. 创建 4 个文件（按 §3 模板）
touch ToT/flows/<NAME>/{README.md,ROLES.md,NODES.md,CHANGELOG.md}

# 4. 跑 lint
python3 ToT/sop/flow-lint.py ToT/flows/<NAME>.json

# 5. 跑 TDD 实跑
python3 ToT/sop/tdd-flow.py ToT/flows/<NAME>.json
```

### 4.2 修改现有流程时

```bash
# 1. 修改 JSON
$EDITOR ToT/flows/<NAME>.json

# 2. 同步更新 <NAME>/NODES.md（如有节点增删）
# 3. 同步更新 <NAME>/ROLES.md（如有角色增删）
# 4. 在 <NAME>/CHANGELOG.md 加一行

# 5. 跑双轨
python3 ToT/sop/flow-lint.py ToT/flows/<NAME>.json
python3 ToT/sop/tdd-flow.py ToT/flows/<NAME>.json
```

---

## 5. 错误处置

| lint 错误 | 修复 |
|-----------|------|
| `name 不等于 toLower(文件名)` | 改 JSON 的 name 字段，或改文件名 |
| `同名文件夹缺失` | `mkdir ToT/flows/<NAME>` |
| `必备文件缺失 (README/ROLES/NODES/CHANGELOG)` | 按 §3 模板补 |
| `NODES.md 缺节点 ID` | 在 NODES.md 加对应章节 |
| `ROLES.md 缺角色` | 在 ROLES.md 加对应行 |

---

## 6. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：定义 6 条强制约束 + 4 文件模板 + 验证流程；从 FDEP v0.6.2 改造沉淀 |
| v0.2 | 2026-09-22 | **配套脚本落地**：`flow-lint.py`（v0.1）。自动检查 ① 路径在 ToT/flows/ ② name 与文件名 toLower 一致 ③ 同名文件夹存在 ④ 4 文件齐全 ⑤ NODES.md 覆盖所有 node.id ⑥ ROLES.md 覆盖所有非空 assignee。CLI：`flow-lint.py <flow.json> [...]`。负向测试通过：name 错配 → exit=1；文件夹缺失 → exit=1；正常 FDEP → exit=0。 |
| v0.3 | 2026-09-22 | **文件名小写强制规则**：用户口头授权 FDEP.json → fdep.json（立即执行）。§10 新增约束 #2「文件名必须全小写」；flow-lint.py 加 `stem == stem.lower()` 检查；7 条强制约束整体更新。本 SOP 同步：error table 增加「文件名非小写」条目；验证流程更新为 lowercase 路径示例；与 README §10 v1.3 / ToT 实际状态一致。 |
