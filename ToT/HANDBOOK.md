# jeeFlow · FDEP · 知识手册（Handbook）

> **读者**：其他开发者 / 协作者 / 后续 AI Agent
> **目的**：理解整套系统的架构、数据流、操作流程，能独立完成日常任务
> **维护方**：见文末「维护说明」

---

## 1. 30 秒读懂

**这是什么**：一套基于 `jeeflow` 引擎的**协作流程管理平台**，用 jeeflow 自带的 Snaker 流程定义格式描述 jeeflow 自己的协作闭环（即"吃自己狗粮"）。

**核心三件套**：

| 组件 | 文件 / 位置 | 作用 |
|------|-------------|------|
| **FDEP 流程定义** | `ToT/flows/fdep.json` + `ToT/flows/fdep/` | 6 阶段协作流程（接收→立项→设计→开发→评审→沉淀） |
| **SPI 组织数据** | `spi/dev/jsons/*.json` | 14 用户 / 14 角色 / 4 字典（人员与组织结构） |
| **jeeflow 引擎** | `main.py` / `main_pg.py` / `vendor/jeeflow/` | 流程执行引擎（memory 或 PG 后端） |

**当前生产部署**：`https://abc.feg.cn/jeeflow/`（PG 后端，fdep id=1790042780958000）

---

## 2. 系统架构图

```mermaid
graph TB
    subgraph "客户服务器 abc.feg.cn/jeeflow"
        direction TB
        JeeflowAPI[Jeeflow Facade API<br/>HTTP/HTTPS]
        MemEngine[Memory Repository<br/>或 PG Repository]
        PG[(PostgreSQL<br/>10.17.1.26:6432/litellm)]
        AutoDeploy[auto_deploy_fdep<br/>服务启动时自动部署]
        JeeflowAPI --> MemEngine
        MemEngine --> PG
        AutoDeploy -.启动触发.-> JeeflowAPI
    end

    subgraph "本地开发环境"
        LocalMain[main.py :8101<br/>memory backend]
        LocalMainPG[main_pg.py :8102<br/>PG backend]
        SPILocal[spi/dev<br/>用户/角色/部门]
        ToTDir[ToT/<br/>fdep.json + SOPs + 留档]
        LocalMain --> SPILocal
        LocalMainPG --> SPILocal
        ToTDir -.读 fdep.json.-> LocalMainPG
        ToTDir -.读 fdep.json.-> LocalMain
    end

    subgraph "SOP 脚本（ToT/sop/）"
        SPIChk[spi-verify.py]
        LintChk[flow-lint.py]
        TDDChk[tdd-flow.py]
        ResetSOP[customer-data-reset]
        DeploySOP[engine-deploy]
    end

    AI[AI Agent] -->|curl API| JeeflowAPI
    Human[人工] -->|git push + ssh restart| JeeflowAPI
    AI -.执行.-> SPIChk
    AI -.执行.-> LintChk
    AI -.执行.-> TDDChk
    AI -.执行.-> ResetSOP
```

---

## 3. 三大环境拓扑

| 环境 | 地址 | 后端 | 用途 | 谁负责 |
|------|------|------|------|--------|
| **本地 dev memory** | `127.0.0.1:8101` | 内存 | 快速调试，重启清空 | 人工（uvicorn） |
| **本地 dev PG** | `127.0.0.1:8102` | PG（共享 litellm 库） | 接近生产的行为 | 人工（uvicorn + PG DSN） |
| **客户测试服务器** | `https://abc.feg.cn/jeeflow/` | PG | 用户真实需求入口 + 协同开发 | **AI 操作 API，人工 push 引擎** |

**关键约定**（用户口头）：
- 客户服务器由 AI 通过 HTTPS API 操作（reset / deploy / healthz / 留档）
- 人工只负责：修改引擎代码 + git push + ssh 重启服务

---

## 4. 核心概念

### 4.1 FDEP 流程（6 阶段 + 驳回分支）

```
start (任何来源)
   ↓
stage_intake (R3 / fdep_intake) ←—— 决策点
   ↓
decision_intake (submitType 路由)
   ├── submitType=1 → stage_pm (R3 / fdep_rml)
   │                       ↓
   │                    stage_design (R7 / fdep_arch)
   │                       ↓
   │                    stage_dev (R2 / fdep_dev)
   │                       ↓
   │                    stage_review (R6 / fdep_review)
   │                       ↓
   │                    stage_feedback (R5 / fdep_kb)
   │                       ↓
   │                       end (协作闭环)
   └── submitType=2 → end_rejected (驳回闭环)
```

详见 `ToT/flows/fdep/README.md`

### 4.2 三层角色映射

```
抽象 R 角色    SPI 角色          占位用户（v0.6.x）
─────────    ──────────         ──────────
R3           fdep_intake         u_fdp_pm
R3           fdep_rml            u_fdp_pm
R7           fdep_arch            u_fdp_pm
R2           fdep_dev             u_fdp_pm
R6           fdep_review          u_fdp_pm
R5           fdep_kb              u_fdp_pm
```

- **抽象 R 角色**：`ToT/README.md#4-角色分工` 定义，人类可读
- **SPI 角色**：`spi/dev/jsons/ROLE_TO_USERS.json` 登记，引擎可查
- **占位用户**：`u_fdp_pm`（v0.6.x 占位，v0.7+ 多人真实分工时替换）

**当前限制**：FDEP.json 的 `assignee` 直接用 `u_fdp_pm`（不靠 SPI 角色自动解析，因为引擎未启用 assignmentHandler）。v0.7+ 计划用 assignmentHandler 让 R 角色 → 多用户。

详见 `ToT/mapping.md`

### 4.3 FDEP 部门（SPI 数据）

- dept ID：**`DFDEP`**（固定顶层根，无 parent_id）
- dept name：`FDEP协作组`
- 成员：`u_fdp_pm`（占位）
- leader / main_leader：`u_fdp_pm`（self-led）

---

## 5. 快速开始

### 5.1 拉代码后第一步

```bash
# 1. 进入项目
cd $REPO_ROOT  # 或用 ToT/bin/jf wrapper

# 2. 启动 memory 后端（开发用）
.venv/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8101

# 另一个终端：启动 PG 后端（更接近生产）
export JEEFLOW_PG_DSN="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm"
.venv/bin/python3 -m uvicorn main_pg:app --host 127.0.0.1 --port 8102

# 3. 看 healthz
curl -sf http://127.0.0.1:8101/healthz
# 期望: {"status":"UP","backend":"memory", ...}
curl -sf http://127.0.0.1:8102/healthz
# 期望: {"status":"UP","backend":"python","pg":"ok"}
```

### 5.2 跑 SOP 验证本地

```bash
cd $REPO_ROOT  # 或用 ToT/bin/jf wrapper

# 1. SPI 数据完整
SPI_FOLDER=dev python3 ToT/sop/spi-verify.py

# 2. FDEP.json 合规
python3 ToT/sop/flow-lint.py ToT/flows/fdep.json

# 3. FDEP 引擎实跑（happy + reject）
python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json
```

### 5.3 访问客户服务器（AI 视角）

```bash
TARGET="https://abc.feg.cn/jeeflow"

# 健康检查
curl -sf -o /dev/null -w "HTTP %{http_code}\n" $TARGET/healthz

# 列出已部署流程
curl -s -X POST $TARGET/wf/processDefine/page \
    -H "Content-Type: application/json" -d '{"pageNum":1,"pageSize":999}'

# 端到端冒烟（推到 DONE）
FDEP_ID=...
curl -s -X POST $TARGET/wf/processDefine/startAndExecute \
    -H "Content-Type: application/json" \
    -d "{\"processDefineId\":\"$FDEP_ID\",\"operator\":\"u_fdp_pm\"}"
# 然后循环 execute task 直到 state=DONE
```

---

## 6. 常见任务操作手册

### 6.1 修改 FDEP 流程（增删节点、改边）

```bash
# 1. 编辑 JSON
$EDITOR ToT/flows/fdep.json

# 2. 同步更新 ToT/flows/fdep/ 内 4 文件（如涉及节点/角色增删）
$EDITOR ToT/flows/fdep/{NODES.md,ROLES.md,CHANGELOG.md}

# 3. 跑 SOP 验证
python3 ToT/sop/flow-lint.py ToT/flows/fdep.json
python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json

# 4. 部署到客户服务器（AI 操作）
TARGET="https://abc.feg.cn/jeeflow"
python3 -c "
import json
content = open('ToT/flows/fdep.json').read()
print(json.dumps({'content': content, 'operator': 'system', 'name': 'fdep'}))
" | curl -s -X POST $TARGET/wf/processDefine/deploy \
    -H "Content-Type: application/json" -d @- --max-time 30

# 5. 冒烟测试推到 DONE（验证 §6.4）
# 见 customer-data-reset.md v0.3
```

### 6.2 修改 SPI 组织（加用户/改角色）

```bash
# 1. 编辑 JSON
$EDITOR spi/dev/jsons/USERS.json   # 加用户
$EDITOR spi/dev/jsons/ROLE_TO_USERS.json  # 改角色映射
$EDITOR spi/dev/jsons/DEPTS.json    # 改部门

# 2. 跑 SOP 验证
SPI_FOLDER=dev python3 ToT/sop/spi-verify.py
# 期望看到 16 条不变量检查（DFDEP 部门、u_fdp_pm、6 个 fdep_* 角色等）
```

### 6.3 修改引擎代码（main.py / main_pg.py / vendor/jeeflow/）

这是**引擎级变更**，需走 §11 流程：

```bash
# 1. 本地开发 + SOP 全跑
SPI_FOLDER=dev python3 ToT/sop/spi-verify.py
python3 ToT/sop/flow-lint.py ToT/flows/fdep.json
python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json

# 2. 人工：git push + ssh 重启客户服务器
# （AI 没有 SSH 权限）
git push origin <branch>
ssh <user>@abc.feg.cn "sudo systemctl restart jeeflow"

# 3. AI：重启后立即跑就绪检查（8 项）
# 见 ToT/customer-checks/2026-09-22_ready.md 模板
```

### 6.4 reset 客户服务器

仅在以下情况做 reset：
- 首次发布 / 重大版本升级 / 客户反馈"环境脏了"

**AI 全自动流程**（无需 SSH）：

```bash
TARGET="https://abc.feg.cn/jeeflow"

# 1. 测可达
curl -sf -o /dev/null -w "HTTP %{http_code}\n" $TARGET/healthz

# 2. 盘点
curl -s -X POST $TARGET/wf/processDefine/page \
    -H "Content-Type: application/json" -d '{"pageNum":1,"pageSize":999}'

# 3. reset
curl -s -X POST $TARGET/api/reset \
    -H "Content-Type: application/json" -d '{}' --max-time 30

# 4. 重新部署 fdep.json
python3 -c "
import json
content = open('ToT/flows/fdep.json').read()
print(json.dumps({'content': content, 'operator': 'system', 'name': 'fdep'}))
" | curl -s -X POST $TARGET/wf/processDefine/deploy \
    -H "Content-Type: application/json" -d @- --max-time 30

# 5. 冒烟推到 DONE（v0.3 强制）
FDEP_ID=...  # 从 step 2 的 page 中拿
# 循环 startAndExecute + execute 直到 state=DONE
# 完整脚本见 ToT/sop/customer-data-reset.md §6.4

# 6. 留档
# 写入 ToT/customer-resets/YYYY-MM-DD_abc.feg.cn.md
```

详见 `ToT/sop/customer-data-reset.md` v0.3

---

## 7. SOP 索引

| SOP | 脚本 | 何时跑 | 详见 |
|-----|------|--------|------|
| spi-verify | `spi-verify.py` | 修改 `spi/*/jsons/*.json` 后 | `ToT/sop/spi-verify.md` |
| flow-lint | `flow-lint.py` | 修改 `ToT/flows/*.json` 后 | `ToT/sop/flow-folder.md` |
| tdd-flow | `tdd-flow.py` | 修改 `ToT/flows/*.json` 后 | `ToT/sop/tdd-flow.md` |
| auto-deploy-fdep | （嵌 main_common） | 服务启动时 | `ToT/sop/auto-deploy-fdep.md` |
| engine-deploy | （人工） | 引擎级改动 | `ToT/sop/engine-deploy.md` v0.2 |
| customer-data-reset | （AI 全自动） | 客户服务器 reset | `ToT/sop/customer-data-reset.md` v0.3 |

---

## 8. 关键文件索引

```

├── main.py                 # memory 端入口（端口 8101）
├── main_pg.py              # PG 端入口（端口 8102）
├── main_common.py          # 共享代码 + auto_deploy_fdep
├── main_meta.py            # meta reader
├── spi/dev/                # 完整组织数据
│   └── jsons/
│       ├── USERS.json          # 14 用户
│       ├── ROLES.json          # 14 角色（含 6 fdep_*）
│       ├── ROLE_TO_USERS.json  # 角色-用户映射
│       ├── DEPTS.json          # 部门（含 DFDEP）
│       └── DICTS.json          # 字典
├── vendor/jeeflow/         # 内嵌 jeeflow 引擎（独立模块）
├── ToT/                    # ⭐ 本工作产出根目录
│   ├── README.md           # 工作规范主文档
│   ├── mapping.md          # 角色映射原理
│   ├── HANDBOOK.md         # 本文件（知识手册）
│   ├── flows/fdep.json     # FDEP 流程定义（机器版）
│   ├── flows/fdep/         # FDEP 文档（人类版）
│   │   ├── README.md
│   │   ├── ROLES.md
│   │   ├── NODES.md
│   │   └── CHANGELOG.md
│   ├── sop/                # SOP 脚本
│   │   ├── spi-verify.md/.py
│   │   ├── flow-folder.md + flow-lint.py
│   │   ├── tdd-flow.md/.py
│   │   ├── auto-deploy-fdep.md
│   │   ├── engine-deploy.md
│   │   └── customer-data-reset.md
│   ├── tdd/                # 流程实跑测试日志
│   │   ├── INDEX.md
│   │   └── test_<flow>_<ts>.{md,json}
│   ├── customer-resets/    # 客户服务器 reset 留档
│   │   └── YYYY-MM-DD_abc.feg.cn.md
│   └── customer-checks/    # 客户服务器就绪检查留档
│       └── YYYY-MM-DD_ready.md
```

---

## 9. 故障排查

| 现象 | 可能原因 | 解决方案 |
|------|----------|----------|
| healthz 返回 500 | 引擎异常 | `journalctl -u jeeflow -n 50`（人工 SSH） |
| fdep 未自动部署 | 服务未重启 / ToT/flows/fdep.json 缺失 | AI：手动 `POST /wf/processDefine/deploy`；或人工 restart |
| task actors 不含 u_fdp_pm | SPI ROLE_TO_USERS 未映射 | 跑 `spi-verify.py` 看是否 16 不变量全过 |
| `/api/reset` 返回 code != 0 | 后端异常 / 表不存在 | 看 PG_DSN 是否正确；看 `wf_process_*` 表是否存在 |
| `getLastByName` 不返回已有 define | 参数名错（`processDefineName` 不是 `name`） | 详见 `auto-deploy-fdep.md` §3 |
| 引擎 task execute 报"state=20 不可执行" | W012 bug 重现，决策节点缺 default edge | 检查 FDEP.json decision_intake 是否有 `e_decision_default` 边 |
| doingList 长期 > 0 | DOING 实例未推进 / 卡死 | reset 或手动 archive |
| 变量 `u_deptName="默认部"` | 已知 P1：引擎 dept 解析走 fallback | 不阻塞流程；v0.7+ 修复 |

---

## 10. 维护说明

- **文档归属**：本文档 (`ToT/HANDBOOK.md`) 是知识入口；详细规范见 `ToT/README.md`
- **更新触发**：以下情况需更新本文档
  - 新增环境（dev/staging/prod）
  - 新增 SOP
  - 新增故障模式
  - 关键概念变更（如角色映射规则）
- **维护者**：所有修改走 §0 meta-process（一次只改一节，双方确认）
- **版本同步**：本文档与 `ToT/README.md` 同步升级

---

## 11. 关键约定速查

| 约定 | 值 |
|------|-----|
| 默认端口（本地 dev） | memory=**8101**, PG=**8102** |
| 客户测试服务器 | `https://abc.feg.cn/jeeflow/` |
| PG DSN | `postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm` |
| SPI_FOLDER | `dev` |
| FDEP dept ID | **`DFDEP`**（顶层根，无 parent） |
| FDEP 占位用户 | `u_fdp_pm` |
| FDEP 流程名 | `fdep`（小写） |
| FDEP 文件名 | `fdep.json`（小写） |
| AI 回复语言 | 中文（用户偏好） |
| 职责分工 | AI 操作客户服务器 API，人工 push 引擎 |

---

## 12. ToT/docs/ 知识体系索引（2026-09-18+ v2 体系）

> **补充**：本文档（HANDBOOK.md）是工作规范手册；细节契约 / API / 用户手册见 `ToT/docs/`。
> **何时查这里**：设计流程时遇到术语不明、API 签名不确定、与上游约定差异 → 直接进 `ToT/docs/`。

| 主题 | 主入口 | 何时读 |
|------|--------|--------|
| **设计原理**（4.x）| `ToT/docs/concepts/`（10 文件）| 理解「为什么这样设计」 |
| **核心类型 / Row / Enum** | [`ToT/docs/concepts/09-core-types.md`](./concepts/09-core-types.md) | Engine / FlowEdge / TaskRow 等 |
| **FDEP 模块**（spi/fdep/ 8 文件 + 5 JSON）| [`ToT/docs/concepts/10-fdep.md`](./concepts/10-fdep.md) | 找人 / 找字典 |
| **API 速查**（73 公开 API）| [`ToT/CC/api-index.md`](../CC/api-index.md) | 找方法签名 |
| **用户指南**（9 文件）| `ToT/docs/guides/` | 用户视角快速开始 |
| **用户手册**（11 文件）| `ToT/docs/manual/` | 部署 / 设计 / 发布 / 审批 |
| **设计模式**（5 文件）| `ToT/docs/patterns/` | 多级 / 会签 / 驳回 / 条件分支 |
| **CC 客户中心**（15 文件）| [`ToT/CC/README.md`](../CC/README.md) | 4 persona 计划 |
| **CC 故事 001** | [`ToT/CC/_story_001_annual_leave.md`](../CC/_story_001_annual_leave.md) | 闭环自检案例 |
| **飞轮 E2E 演示** | [`ToT/CC/_flywheel_demo_e2e.md`](../CC/_flywheel_demo_e2e.md) | 飞轮机制验证 |
| **Q3 季度回顾** | [`ToT/CC/_quarterly_retrospective_2026Q3.md`](../CC/_quarterly_retrospective_2026Q3.md) | 9 月 18-25 复盘 |
| **SOP 工具链**（22 个）| [`ToT/sop/`](./sop/) | 自动化脚本 |
| **健康度门禁** | [`ToT/sop/health-check.py`](./sop/health-check.py) | 5 维度评分（当前 100/100）|
| **健康度可视化** | [`ToT/docs/REPORT.html`](../docs/REPORT.html) | 浏览器打开看 |
| **发版流水线** | [`ToT/sop/release.sh`](./sop/release.sh) | drift gate + 版本注入 |

**当前健康度**：100/100 🟢（drift 0/146 · API 73/73 · 飞轮 1 RPM）

---

## 13. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：知识手册主文档（30秒读懂 / 架构图 / 三环境拓扑 / 核心概念 / 快速开始 / 常见任务 / SOP 索引 / 文件索引 / 故障排查 / 维护 / 约定速查）；用户口头指令"use the jeeflow fdep.json, import the fdep.json, doc the knowledge"落地 |
| v0.2 | 2026-09-26 | **§12 ToT/docs/ 知识体系索引**：补全与 `ToT/docs/`、`ToT/CC/`、`ToT/sop/` 的交叉引用；新增健康度数据；旧 §12 改 §13 变更日志 | |
