# Iteration #33 · 2026-09-23 · W42 · flow-operator skill 增强：Config + FeedBack + fdep 自动验证

> **驱动**：SKILL.md v0.3 之后用户提出 3 项增强：① 配置工具（config.yaml + 验证）② 反馈流程（FeedBack 节）③ active_server 存 URL + fdep 自动验证
> **核心成果**：✅ **`ToT/skills/flow-operator/` 三件套就绪** —— `SKILL.md`（206 行 / 7 大节） + `config.py`（写入前验证 + fdep 自动捕获） + `config.yaml`（4 字段 + fdep 元信息）

---

## 1. 时间线（~30 分钟 / 5 步迭代）

| 时段 | 工作 |
|------|------|
| 0~5 min | 创建 `config.py` 工具 + `config.yaml` + SKILL.md `## Config` 节 |
| 5~10 min | 修正：`active_server` 改为 URL（不是 server 名） |
| 10~20 min | 加写入前验证（URL + user_id + role_lenses 强制默认）|
| 20~25 min | 加 `validate_fdep()` + 自动写入 config.yaml + SKILL.md 同步 |
| 25~30 min | 加 SKILL.md `## FeedBack` 节 + Iter#33 留档 |

---

## 2. 三件套架构

```
ToT/skills/flow-operator/
├── SKILL.md        ← AI agent 看到的静态文档（7 大节）
├── config.yaml     ← 持久化配置（active_server / operator / fdep）
└── config.py        ← 加载 + 验证 + 设置工具（setup / set / get_context）
```

---

## 3. config.py 工具能力（最终）

### 3.1 CLI 子命令

| 子命令 | 用途 |
|--------|------|
| `--context` | 给 AI agent 的上下文摘要（每次触发 SKILL 应展示）|
| `--setup` | 交互式首次配置（含全部验证）|
| `--set k=v` | 命令行设置单个字段（写入前自动验证）|
| `--load` | 仅加载并打印 YAML |

### 3.2 写入前验证规则

| 字段 | 验证规则 | 失败行为 |
|------|---------|---------|
| `active_server` | `curl {url}/healthz` 须返回 `{"status":"UP"}` | ❌ exit 1，不写入 |
| `operator.user_id` | 调 `{active_server}/api/spi/users` 查 uid 存在 | ❌ exit 1，不写入 |
| `operator.role_lenses` | **永远默认 `[initiator, assignee]`**，忽略任何输入 | ⚠ 警告 + exit 1，不写入 |
| `fdep` | `active_server` 验证通过后**自动**调 `getLastByName` | ⚠ 非阻塞；fdep 未部署也写入 active_server（fdep 字段记 error）|

### 3.3 验证函数

- `validate_url(url)` → `(ok, msg)`：curl healthz
- `validate_user_id(url, uid)` → `(ok, msg)`：SPI /api/spi/users 查询
- `validate_fdep(url)` → `(ok, info_dict, msg)`：调 `/wf/processDefine/getLastByName` 返回 fdep 元信息（define_id / name / display_name / version / state / type / verified_at）

---

## 4. config.yaml 最终内容

```yaml
active_server: http://127.0.0.1:8101  # API base URL（不是 server 名）
operator:
  user_id: u_fdp_pm
  role_lenses:
  - initiator
  - assignee                  # 永远默认这 2 个
fdep:                          # active_server 验证后自动写入
  define_id: '20'
  name: fdep
  display_name: jeeFlow 协作主流程 (Foundational Development & Engagement Process)
  version: 0
  state: 1
  type: collaboration
  verified_at: '2026-09-23T10:04:12'
```

---

## 5. SKILL.md 7 大节（最终结构）

```
## overview      ← 身份 + 边界
## Config        ← 强制先看：调用 config.py --context 展示上下文
## Knowledge     ← API-first 原则
## flow          ← mermaid sequenceDiagram demo
## Tools         ← 5 场景 + 系统层 endpoint
## FeedBack      ← 🆕 5 步反馈流程 + 收集数据 + 命令模板 + 字段约定
## Others        ← 安全约束
```

---

## 6. FeedBack 节（新增）

### 6.1 5 步反馈流程
1. **收集**（8 类数据：实例快照 / 审批记录 / 流转变量 / 审计日志 / 流程定义 / 本地 tdd / config 快照 / 错误堆栈）
2. **打包** `tar.gz`
3. **file-share 上传**（用 `share.json.upload_url`）→ 取件码
4. **触发 fdep**（用 `active_server` + `processDefine/startAndExecute`）
5. **等待回复**

### 6.2 fdep variable 字段约定

| 字段 | 必填 |
|------|------|
| `feedback_code`（file-share 取件码） | ✅ |
| `feedback_summary`（简短说明 < 200 字）| ✅ |
| `feedback_type`（bug / question / suggestion）| ⛔ |
| `feedback_severity`（low / medium / high）| ⛔ |
| `feedback_instance_id`（相关实例 id）| ⛔ |

---

## 7. 关键决策（ADR 风格）

### ADR-33.1 · active_server 存 URL（不是 server 名）
- **决策理由**：config 自包含，避免跨查 `servers.json`
- **代价**：与 `archive_flow.py` / `promote.py` 不再共享 server 配置（但它们仍可读 `servers.json`）

### ADR-33.2 · role_lenses 强制默认 [initiator, assignee]
- **决策理由**：第 31 圈已收口为"2 视角最小集"，询问用户无意义
- **行为**：任何输入值都被忽略并警告退出

### ADR-33.3 · fdep 自动验证非阻塞
- **决策理由**：fdep 未部署不应让 active_server 写入失败（可能是临时现象）
- **行为**：fdep 验证失败时写入 `fdep: {error: msg}`，get_context 显示 ⚠️

### ADR-33.4 · FeedBack 走 fdep 现有流程（不改 fdep）
- **决策理由**：fdep 内部已有"issue 收集 / 处理"能力，复用而非新设计

---

## 8. 度量（飞轮 33 圈累积）

| 指标 | #32 | **#33** |
|------|-----|---------|
| flow-operator 文件数 | 1 (SKILL.md) | **3 (SKILL + config.py + config.yaml)** |
| SKILL.md 节数 | 5 | **7 (+Config / +FeedBack)** |
| config 字段数 | 0 | **4 (active_server / user_id / role_lenses / fdep)** |
| 验证防线 | 0 | **3 (URL / user_id / fdep) + 1 强制 (role_lenses)** |
| §9 检查项 | 44 | **44** |
| EA roadmap 版本 | v3.8 | **v3.8** |

---

## 9. 闭环示意

```
┌── "flow-operator skill 增强 3 项" ──┐
↓                       │
建 config.py + config.yaml  │
↓                       │
active_server 改 URL      │
↓                       │
加 3 道验证 + role 强制    │
↓                       │
fdep 自动验证 + 写入       │
↓                       │
SKILL.md +FeedBack 章节   │
↓                       │
→ 飞轮第 33 圈 ✅           │
```

---

## 10. 经验沉淀

### 10.1 配置工具的最小架构
- **CLI 子命令模式**：`--load / --context / --setup / --set` 4 个足够覆盖所有用法
- **验证优先于异常**：每个 `--set` / `--setup` 写入前验证，失败退出而非回滚
- **get_context 是 AI 契约**：每次 SKILL 触发必须调用，输出给人类用户看

### 10.2 强制默认 vs 可配置
- **可配置**：active_server（业务相关 / 多环境）
- **强制默认**：role_lenses（已收口的常量）
- **不可阻塞的验证**：fdep（不应让 active_server 因 fdep 缺失失败）

### 10.3 FeedBack 设计原则
- **复用现有流程**：fdep 已经能处理 issue，复用而不新设计
- **file-share 中转**：大数据通过 file-share 分享，fdep 只传取件码
- **字段约定清晰**：必填 / 可选明确，避免歧义

---

## 11. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第三十三轮迭代 · W42 flow-operator skill 增强**：① **新建 `config.py` 工具**（4 个 CLI：load / context / setup / set）；② **新建 `config.yaml`**（active_server / operator / fdep 4 字段）；③ **SKILL.md 加 `## Config` 节**（强制 AI agent 先调 `--context` 展示上下文）；④ **active_server 改 URL 存储**（不依赖 servers.json）；⑤ **3 道写入前验证**（URL healthz / user_id SPI / fdep 自动）；⑥ **`role_lenses` 强制默认** `[initiator, assignee]`（不询问）；⑦ **`fdep` 自动验证 + 写入** config.yaml（`getLastByName` + 元信息含 verified_at）；⑧ **SKILL.md 加 `## FeedBack` 节**（5 步流程 + 收集数据 + 命令模板 + 字段约定）；⑨ **get_context() 输出**含 server / operator / fdep / 行动准则；⑩ 新增 iterations/2026-09-23_flow-operator-config.md；⑪ iterations/README.md 刷新 32 → 33 圈。 |