# ToT/tdd/ — 流程 JSON TDD 测试日志

> 本目录存放 `ToT/flows/*.json` 等流程定义的引擎实跑测试日志。
> 由 `ToT/sop/tdd-flow.py` 自动生成（脚本见 ToT/sop/tdd-flow.md）。
> **不**存放项目根 `tdd/` 下的原有回归样例（那些是 jeeFlow 引擎自身的 TDD 套件）。

---

## 1. 文件命名约定

| 类型 | 命名 | 生成方式 | 内容 |
|------|------|----------|------|
| 人类摘要 | `test_<flow-name>_<YYYYMMDDHHMMSS>.md` | 自动 | 静态校验 + 引擎 verify + happy/reject 状态表 |
| 原始数据 | `test_<flow-name>_<YYYYMMDDHHMMSS>.json` | 自动 | deploy / start / execute / detail 全量响应 |

**约定**：
- 时间戳格式：`date +%Y%m%d%H%M%S`（本地时区）
- 同一次开发的多次回归会留下多份日志，靠时间戳排序追溯
- `.md` 与 `.json` 必须配对（一同生成，不可拆分）
- 失败日志**永久保留**（包含错误状态机与修复过程），供回归用

---

## 2. 当前 FDEP.json 测试日志

| 时间戳 | FDEP 版本 | 结果 | 备注 |
|--------|-----------|------|------|
| `test_FDEP_20260922081228.md` | v0.5 | ❌ FAILED | hand-written，P0 × 2 (W012 + 角色解析断裂) |
| `test_FDEP_20260922081800.md` | v0.6.2 | ✅ PASSED | hand-written，happy path 全 DONE |
| `test_FDEP_20260922082028.md` + `.json` | v0.6.2 | ✅ PASSED | **脚本生成**（基线） |

**基线**：`test_FDEP_20260922082028.{md,json}` —— 由 `tdd-flow.py` 生成，作为 v0.6.2 的标准回归锚点。

---

## 3. 用法

### 3.1 跑一次新测试

```bash
python3 ToT/sop/tdd-flow.py ToT/flows/FDEP.json
# 自动生成 test_FDEP_<新时间戳>.md + .json
```

### 3.2 查看历史日志

按时间戳排序，最新的在前：

```bash
ls -lt ToT/tdd/test_*.md | head -5
```

### 3.3 对比两次结果

```bash
# 摘要对比（用 diff / vimdiff）
diff ToT/tdd/test_FDEP_<旧>.md ToT/tdd/test_FDEP_<新>.md

# 原始数据对比（jq）
diff <(jq . ToT/tdd/test_FDEP_<旧>.json) <(jq . ToT/tdd/test_FDEP_<新>.json)
```

---

## 4. 已知 limitation（与 tdd-flow SOP 同步）

- 占位用户 u_fdp_pm 分饰多角
- reject path 仅演示机制（未做真正 intake 阶段驳回）
- memory backend（与 PG 后端有差异）

详见 `ToT/sop/tdd-flow.md#5`。

---

## 5. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初始化索引；记录 3 个 FDEP.json 测试日志（2 个 hand-written + 1 个脚本生成基线）；本目录由 `tdd-flow.py` 自动维护 |
