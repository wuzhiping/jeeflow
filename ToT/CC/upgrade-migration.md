# Upgrade Migration Guide · v1.0 → v1.11

> **读者**：01 引擎开发（郭开发类角色）
> **目的**：升级前知道哪些字段 / API / 配置变了

---

## 1. 升级 checklist（每次必跑）

```bash
# 1. 跑测试
pytest tests/

# 2. 跑 doc-link-checker
python3 ToT/sop/doc-link-checker.py
# 必须 0 drift

# 3. 跑 health-check（综合门禁，Step 0）
python3 ToT/sop/health-check.py --json | jq '.overall_score'
# 必须 ≥ 100

# 4. 打 snapshot
bash ToT/sop/release.sh vX.Y.Z

# 5. 升级后验证
curl http://localhost:8101/healthz  # status=UP
curl http://localhost:8101/version   # version=X.Y.Z
```

---

## 2. v1.0 → v1.10 字段演进清单

### 2.1 id 类型变化（v1.0 → v1.2，重大）

**Before (v1.0)**：
```python
# PG 表
id BIGINT
```

**After (v1.2+)**：
```python
# PG 表（仍是 BIGINT 但导出按字符串）
# facade 层自动 _stringify_ids（facade.py:2444 _stringify_ids）
```

**影响**：
- 前端 JS Number `> 2^53` 会丢精度（雪花 ID 19 位超）
- **必须按字符串处理**（跨进程）

**修复**：facade.py:2444 `_stringify_ids` 实现（issues/38 E9）

### 2.2 taskType / performType 枚举值（v1.3 → v1.5）

**Before (v1.3)**：
- PG 列：`INTEGER`（用 int 表示 enum）

**After (v1.5+)**：
- PG 列：`VARCHAR(64)`（用字符串）
- 写入时 int → str 强转

**影响**：
- 老的 SQL `WHERE taskType = 1` 必须改成 `WHERE taskType = '1'`
- 老的 ORM 模型 `Integer` → `String`

**修复位置**：`facade.py` `_safe_save_task/_save_instance`

### 2.3 processSurrogate.enabled（v1.6 → v1.8）

**Before**：PG 列 `INTEGER`（0/1）
**After**：PG 列 `BOOLEAN`

**影响**：所有 `enabled=1` 必须改成 `enabled=true`

### 2.4 processDesign.isDeployed（v1.6 → v1.8）

同 2.3（int → bool）

### 2.5 PG INTERVAL → Python timedelta（v1.7 → v1.9）

**Before**：直接读 PG INTERVAL 报错
**After**：必须 `total_seconds()`

**影响**：
```python
# 老的
duration = row.duration  # 直接用 → 报错
# 新的
duration = row.duration.total_seconds()
```

### 2.6 performType=1 字面量（v1.10）

**问题**：PG 端需要字符串 `'1'`，代码里直接用 `1`

**Before**：
```python
if task.perform_type == 1:  # PG 端是 '1'
```

**After**：
```python
if task.perform_type == '1':  # 字符串
```

**修复**：`facade.py` `_fixed_stats_avg_dur` + `_fixed_stats_task_agg`

---

## 3. breaking change 风险表

| 风险等级 | 改动类型 | 例子 |
|---|---|---|
| 🔴 P0 | id 类型变化 | int → string |
| 🔴 P0 | 删 SPI 方法 | `ProcessRepository.find_xxx` 删除 |
| 🟠 P1 | 枚举值字符串化 | int → str |
| 🟠 P1 | 列类型变化 | INTEGER → BOOLEAN |
| 🟡 P2 | 字段名 rename | `assignee` → `targetUserId` |
| 🟢 P3 | 新增可选参数 | `execute(args: dict = None)` |

---

## 4. 已修的 BUG（升级时确认这些 fix 包含在新版本）

| BUG ID | 描述 | 修复版本 |
|---|---|---|
| FB-0009 | `processTask/delegate` 字段名 `assignee` → `targetUserId` | v1.4 |
| BDD #1201 FIX-T79 | `/api/admin/health` 详细监控 | v1.10 |
| BDD #1201 FIX-T82 | `/version` 端点 | v1.11 |
| BDD #1201 FIX-T74 | `processTask/delegateHistory` | v1.9 |
| BDD #1201 FIX-T系列 | 27 FIX-T 已应用 | v1.10 |

详见 [`ToT/docs/diffs.md`](../../docs/diffs.md)

---

## 5. 升级模式

### 5.1 平滑升级（推荐）

```bash
# 1. 拉新代码
git pull

# 2. 检查 release notes
cat ToT/docs/CHANGELOG.md | head -50

# 3. 跑迁移脚本（如果有 schema 变更）
python3 scripts/migrate_v1.10_to_v1.11.py

# 4. graceful shutdown
kill -TERM <pid>

# 5. 启动新版本
python3 -m uvicorn main_pg:app --port 8102

# 6. 验证
curl /version
curl /healthz

# 7. 看 trace 5 分钟确认无 error spike
curl /api/admin/trace?limit=10
```

### 5.2 回滚

```bash
git checkout <prev-tag>
python3 -m uvicorn main_pg:app --port 8102
```

---

## 6. 升级后必做的回归

- [ ] 创建 1 个新实例（验证 startProcess）
- [ ] 完成 1 个 task（验证 execute）
- [ ] 委派 1 个 task（验证 delegate）
- [ ] 驳回 1 个 task（验证 reject）
- [ ] 撤回 1 个 instance（验证 withdraw）
- [ ] 看 `/api/admin/trace` 0 error span
- [ ] 看 `/api/admin/stats/overview` 数字正常

---

## 7. 新版本验证

升级完成后 24h 内：
- [ ] 0 P0 工单
- [ ] error rate < 1%
- [ ] P95 时长 ≤ 升级前 1.5 倍

---

**版本**：v1.11.1 · **来源**：故事 001（郭开发想升级 v1.12.0）→ 01 persona review