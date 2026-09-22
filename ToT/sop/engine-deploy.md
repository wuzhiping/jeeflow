# SOP: 引擎级更新与人工审核 (engine-deploy)

> **所属**：组织 SOP 集（与 spi-verify / tdd-flow / flow-folder / auto-deploy-fdep 并列）
> **永久规则**：见 `ToT/README.md#11-引擎部署规范`
> **适用**：所有 `main.py / main_pg.py / main_common.py / main_meta.py / vendor/jeeflow/` 下的变更

---

## 1. 环境拓扑

| 环境 | URL / 地址 | 端口 | 用途 | 部署方式 |
|------|-----------|------|------|----------|
| **本地 dev（memory）** | `127.0.0.1` | **8101** | 开发者本机调试，memory 后端 | `python -m uvicorn main:app --port 8101` |
| **本地 dev（PG）** | `127.0.0.1` | **8102** | 开发者本机调试，PG 后端 | `python -m uvicorn main_pg:app --port 8102` |
| **用户测试服务器** | `https://abc.feg.cn/jeeflow/` | 443（反代） | 用户真实需求入口 + 测试 | **人工部署 + 确认**（走 Jira） |

> 🔒 **永久约束**：本地 dev 默认端口 = **8101 (memory) / 8102 (PG)**；不再使用 8101/8102（已弃用）。
> 用户真实需求入口 = `https://abc.feg.cn/jeeflow/`（即"测试服务器"承载生产前的实际用户需求）。

---

## 2. 引擎级 vs 非引擎级变更

### 2.1 引擎级变更（走本 SOP）

任何对以下文件的修改都属**引擎级**，必须人工审核：

- `main.py`
- `main_pg.py`
- `main_common.py`
- `main_meta.py`
- `vendor/jeeflow/**`（内嵌 jeeflow 引擎）

**触发原因**：这些文件改动直接影响引擎启动行为、API 路由、流程执行逻辑、状态机。

### 2.2 非引擎级变更（无需走本 SOP）

以下文件修改**不**视为引擎级，可走 ToT/sop 自身的回归：

- `spi/<folder>/jsons/*.json` → 走 `spi-verify.py`
- `ToT/flows/*.json` → 走 `flow-lint.py` + `tdd-flow.py`
- `ToT/sop/*` 脚本自身 → 走脚本本身的测试
- `flows/`、`sla/`、`bdd/`、`tdd/` 等演示样例

---

## 3. 引擎级更新 SOP（5 步）

### Step 1 · 本地开发（127.0.0.1:8101/8102）

```bash
# Memory 端（默认端口 8101）
.venv/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8101

# PG 端（默认端口 8102）
export PORT=8102
export JEEFLOW_PG_DSN="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm"
.venv/bin/python3 -m uvicorn main_pg:app --host 127.0.0.1 --port 8102
```

### Step 2 · 本地 SOP 全跑（4 项）

```bash
# 2.1 SPI 数据完整性
SPI_FOLDER=dev python3 ToT/sop/spi-verify.py
# 期望: ✅ PASSED

# 2.2 流程定义组织合规
python3 ToT/sop/flow-lint.py ToT/flows/fdep.json
# 期望: ✅ 通过

# 2.3 流程定义引擎实跑
python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json
# 期望: happy=DONE, reject=REJECT

# 2.4 auto-deploy-fdep 端到端（重启服务看日志）
# memory: 应看到 [auto-deploy-fdep] 部署或跳过日志
# pg:     应看到同样日志，重启不重复部署
```

**任一失败 → 回到 Step 1 修复，不可进入 Step 3。**

### Step 3 · Jira 工单申请审核

到 Jira 创建 `Engine Update` 类型工单，模板：

```markdown
## Engine Update Request

**Title**: [Engine] <一句话总结>

**Files Changed**:
- main.py (diff: <link>)
- main_common.py (diff: <link>)
- vendor/jeeflow/facade.py (diff: <link>)
- ...

**Local SOP Results**:
- [x] spi-verify.py: ✅ PASSED (paste output)
- [x] flow-lint.py: ✅ PASSED (paste output)
- [x] tdd-flow.py: ✅ PASSED (paste output)
- [x] auto-deploy-fdep 双端: ✅ (memory + PG logs)

**Risk Assessment**:
- 影响范围: <哪些 API / 哪些用户>
- 向后兼容: <是 / 否 / 需 migration>
- 数据库 schema 变化: <是 / 否；若是，附 migration 脚本>

**Rollback Plan**:
- 代码层: `git revert <commit>` 或回滚到上一个 tag
- 数据层: <若有 schema 变更，需 backup + restore>

**Reviewer**: @<uid>
**Approver**: @<uid>（需独立 reviewer 之外的人）

**Deploy Window**: <建议时间窗>
```

### Step 4 · 人工部署到 `https://abc.feg.cn/jeeflow/`

> ⚠️ **不允许自动部署**。任何代码 push 到生产前必须人工执行。

人工操作清单（按团队实际工具调整）：

```bash
# 1. SSH 到测试服务器
ssh <user>@abc.feg.cn

# 2. 备份当前部署（具体路径按团队约定）
cp -r /opt/jeeflow /opt/jeeflow.backup.$(date +%Y%m%d%H%M%S)

# 3. 拉取新代码（具体方式按团队约定）
cd /opt/jeeflow && git pull origin <branch>

# 4. 重启服务（具体方式按团队约定）
# 例如: systemctl restart jeeflow / docker compose restart / k8s rollout

# 5. 等待服务就绪
sleep 10
```

### Step 5 · 健康检查（curl healthz）

```bash
# 5.1 HTTP 状态码（期望 200）
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://abc.feg.cn/jeeflow/healthz
# 期望输出: HTTP 200

# 5.2 响应体（期望含 status: ok）
curl -s https://abc.feg.cn/jeeflow/healthz
# 期望输出: {"status":"ok", ...}

# 5.3 auto-deploy-fdep 启动日志（在服务器日志中检查）
# 期望: 看到 [auto-deploy-fdep] 行（部署成功 或 跳过已部署）
ssh <user>@abc.feg.cn 'journalctl -u jeeflow --since "5 minutes ago" | grep auto-deploy-fdep'
# 或: docker logs / k8s logs 对应命令

# 5.4 fdep 流程可达性（验证核心 API）
curl -s -X POST https://abc.feg.cn/jeeflow/wf/processDefine/page \
    -H "Content-Type: application/json" \
    -d '{"pageNum":1,"pageSize":999}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); fdep=[r for r in d['data']['rows'] if r['name']=='fdep']; assert fdep, 'fdep not deployed'; print(f'✅ fdep deployed: id={fdep[0][\"id\"]}')"
```

**任一健康检查失败 → 立即回滚到 Step 4 的备份。**

---

## 4. 回滚流程

| 级别 | 操作 | 命令示例 |
|------|------|----------|
| 代码层 | 还原到备份目录 | `rm -rf /opt/jeeflow && mv /opt/jeeflow.backup.<ts> /opt/jeeflow` |
| 服务层 | 重启 | `systemctl restart jeeflow` |
| 数据层 | 还原 schema（仅当本次有 schema 变更） | `psql ... < backup.sql` |

回滚后在 Jira 工单中标注 `ROLLED BACK` + 时间 + 原因。

---

## 5. 跳过审核的例外

以下情况可豁免人工审核（但仍需 Jira 留档）：

| 例外 | 条件 | 限制 |
|------|------|------|
| 注释 / typo 修正 | 仅改 `.py` 文件的注释或字符串 | 无逻辑改动 |
| 紧急 hotfix | 生产已故障 + 影响核心功能 | 需 24h 内补 Jira + reviewer 补签 |

**任何其他改动都必须走完 5 步流程。**

---

## 6. 健康检查快速参考

```bash
# 单行 smoke test（最常用）
curl -sf https://abc.feg.cn/jeeflow/healthz && echo "✅ 服务正常" || echo "❌ 服务异常"

# 完整检查（部署后必跑）
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://abc.feg.cn/jeeflow/healthz
curl -s https://abc.feg.cn/jeeflow/healthz
```

---

## 7. 关联文档

- `ToT/sop/spi-verify.md` — 数据完整性（Step 2.1）
- `ToT/sop/flow-folder.md` — 流程组织合规（Step 2.2）
- `ToT/sop/tdd-flow.md` — 流程实跑（Step 2.3）
- `ToT/sop/auto-deploy-fdep.md` — 自动部署（Step 2.4）
- `ToT/README.md#11-引擎部署规范` — 永久规则

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：5 步流程（本地开发 → SOP → Jira → 人工部署 → healthz）；引擎级范围 5 文件；默认端口 8101/8102（弃用 8101/8102）；用户测试服务器 https://abc.feg.cn/jeeflow/ |
