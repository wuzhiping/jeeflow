# SOP: 流程 JSON TDD 实跑 (tdd-flow)

> **所属**：组织调整 SOP 集（与 spi-verify SOP 并列）
> **脚本**：[`tdd-flow.py`](./tdd-flow.py)
> **适用**：所有 `ToT/flows/*.json` 与未来的 `flows/*.json` 流程定义

---

## 1. 何时使用

| 场景 | 是否必跑 | 期望结果 |
|------|----------|----------|
| 新增 / 修改流程 JSON | ✅ 必跑 | exit=0 (PASSED) |
| 调整流程节点 (nodes/edges) | ✅ 必跑 | exit=0 |
| 调整 `properties.assignee` | ✅ 必跑 | exit=0 |
| 调整 edge 的 `expr` (决策路由) | ✅ 必跑 | exit=0 |
| 仅修改节点 `text.value` / `note` 等展示字段 | ⏸️ 建议跑 | exit=0 或 exit=2 |
| 调整 metadata / version / rationale | ⏸️ 建议跑 | exit=0 |
| 调整 SPI 组织（DFDEP / u_fdp_pm） | ⚠️ 先跑 spi-verify.py 再跑 tdd-flow.py | exit=0 |

---

## 2. 执行步骤

### 2.1 确认前置条件

```bash
# 1. SPI 数据完整
SPI_FOLDER=dev python3 ToT/sop/spi-verify.py
echo "exit=$?"  # 期望 0 或 2

# 2. venv/ 依赖可用（项目根已有）
ls .venv/bin/python3  # 确认存在
```

### 2.2 执行 TDD 测试

```bash
# 默认参数（SPI=dev, operator=u_fdp_pm）
python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json

# 自定义
python3 ToT/sop/tdd-flow.py ToT/flows/<name>.json \
    --spi dev \
    --operator u_fdp_pm \
    --max-steps 20
```

**判定标准**：

| 退出码 | 含义 | 下一步 |
|--------|------|--------|
| **0** | PASSED：happy path DONE, 0 error | ✅ 可继续（晋升到 flows/ 或下一步改动） |
| **2** | PASSED WITH WARNINGS | ✅ 可用，但需人工复核 warnings |
| **1** | FAILED：happy path 非 DONE 或有 error | ❌ **禁止晋升**，必须修复 |

### 2.3 审阅产出物

每次跑会自动在 `ToT/tdd/` 写两份文件：

```
ToT/tdd/test_<flow>_<YYYYMMDDHHMMSS>.md     ← 人类可读摘要
ToT/tdd/test_<flow>_<YYYYMMDDHHMMSS>.json   ← 机器可读原始数据
```

**摘要内容**：静态校验结果 + 引擎 verify 警告 + happy/reject 路径最终状态 + 每 task 的 state/operator/actors

**原始数据**：deploy / startAndExecute / execute / detail 全量响应（用于深度诊断或回放）

### 2.4 出错时的处置

| 错误模式 | 典型原因 | 修复方法 |
|----------|----------|----------|
| `validate_flow` errors | JSON 截断 / 字段缺失 / id 重复 | 检查 JSON 文件末尾 `}` `]` 是否闭合 |
| `verify_flow` W012 | task 节点有 2 条出边且其中 1 条 target 是 end | 改用 snaker:decision 节点分隔（参见 `flows/03-decision-expr.json`） |
| `verify_flow` W013 | decision 节点出边全部带 expr（无默认边） | 加一条 `expr=""` 的 default edge |
| `verify_flow` W014 | 含 decision 节点 | 部署后必跑 TDD 实跑（FIX-T113 §117） |
| `startAndExecute 失败 processDefineId` | deploy 返回结构变了 | 检查脚本中 deploy 数据提取逻辑 |
| `execute 失败 state=20 不可执行` | 实例被兜底边推到了 end，但 task 还在 DOING（W012 重现） | 用 decision 节点修 W012 |
| `execute 失败 state=45` | submitType=2 (REJECT) 触发终止 | 正常 reject 路径，确认符合预期 |
| `operator 无 todo` | actors 列表不含 operator uid | assignee 改为 operator 的实际 uid，或引入 assignmentHandler |

---

## 3. 测试覆盖范围

本 SOP 对单个流程 JSON 跑 3 类测试：

### 3.1 静态校验（前置）

- `tdd/validate_flow.py` — JSON schema + 拓扑（10 节点 / 10 边均通过）
- `vendor/jeeflow/verify_flow` — 引擎内置 verify（含 W001-W014 警告码）

### 3.2 引擎实跑（动态）

- **happy path**: `startAndExecute` → submitType=1 逐 task execute → 期望 state=DONE
- **reject path**（仅当含 snaker:decision 节点）: `startAndExecute` → submitType=2 → 期望 state=REJECT

### 3.3 留档（持久化）

- 摘要 `.md` — 评审 / 沟通用
- 原始 `.json` — 回归 / 回放 / 深度诊断用

---

## 4. 与 spi-verify SOP 的关系

```
修改 SPI 数据 → 跑 spi-verify.py → exit=0
                ↓
修改流程 JSON → 跑 tdd-flow.py → exit=0
                ↓
           提交变更
```

| 检查器 | 关注点 |
|--------|--------|
| spi-verify.py | SPI 4 类校验（C1 跨表引用 / C2 tree / C3 完整性 / C4 一致性）+ FDEP 16 条不变量 |
| tdd-flow.py | 流程 JSON 静态 + 引擎动态执行 + 留档 |

**调用顺序**：先 spi 后 tdd（SPI 错则 tdd 必错）。

---

## 5. 已知 limitations（v0.1）

| 项 | 说明 |
|----|------|
| 占位用户 | 所有测试假设 `u_fdp_pm` 担当全部 6 阶段（一人分饰多角）。真实多人分工需 v0.7+ 的 assignmentHandler。 |
| reject path 语义 | 当前 reject 实际作用在 stage_pm（因 decision_intake 被 submitType=0 兜底跳过）。真正的"intake 阶段驳回"需手动 orchestration（start 而非 startAndExecute + 主动 execute stage_intake with submitType=2）。 |
| dept 解析 | `variables.u_deptName` 显示"默认部"而非"FDEP协作组"（引擎路径不走 SPI），不阻塞流程。 |
| memory backend | 仅用 memory 后端测试，与 PG 后端有差异（参见 `main.py` 注释）。生产前需 PG 后端复测。 |

---

## 6. 留档要求

按 ToT/README.md §1 第 3 条例外审批规则：

- **测试日志永久保留**（包括 FAILED 的记录，供回归）
- **原始 JSON 数据永久保留**（用于回放与深度诊断）
- **测试日志命名**：`test_<flow-name>_<YYYYMMDDHHMMSS>.{md,json}`，时间戳 `date +%Y%m%d%H%M%S` 生成
- **失败不立即删**：失败的测试日志是回归资产，保留至少 30 天

---

## 7. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：从 v0.6.2 FDEP.json 实跑沉淀。脚本 `tdd-flow.py` 支持：①静态校验 ②引擎 verify ③happy+reject 实跑 ④自动留档（.md 摘要 + .json 原始数据）；CLI 参数：`flow_json`（必填）/`--spi`/`--operator`/`--no-reject`/`--max-steps`；首次回放：FDEP v0.6.2 → PASSED |
