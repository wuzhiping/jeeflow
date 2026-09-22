# ToT/tdd/ — 流程 JSON TDD 测试日志

> 本目录存放 `ToT/flows/*.json` 等流程定义的引擎实跑测试日志。
> 由 `ToT/sop/tdd-flow.py` 自动生成（脚本见 `ToT/sop/tdd-flow.md`）。
> **不**存放项目根 `tdd/` 下的原有回归样例（那些是 jeeFlow 引擎自身的 TDD 套件）。

---

## 1. 文件命名约定

| 类型 | 命名 | 生成方式 | 内容 |
|------|------|----------|------|
| **基线** | `test_<flow-name>_baseline_v<X.Y.Z>.{md,json}` | 手工重命名（升级里程碑） | 当前 fdep 版本 PASSED 的基线证据 |
| 人类摘要 | `test_<flow>_<YYYYMMDDHHMMSS>.md` | 自动 | 静态校验 + 引擎 verify + happy/reject 状态表 |
| 原始数据 | `test_<flow>_<YYYYMMDDHHMMSS>.json` | 自动 | deploy / start / execute / detail 全量响应 |

**约定**：
- 时间戳格式：`date +%Y%m%d%H%M%S`（本地时区）
- 每次 `tdd-flow.py` 跑都生成新一份
- 失败日志永久保留；成功日志可定期清理
- `.md` 与 `.json` 必须配对（一同生成，不可拆分）
- **基线命名**：用 `baseline_v<version>` 标识（替代时间戳），方便按版本回归比对

## 2. 当前基线

| 流程 | 版本 | 结果 | 文件 |
|------|------|------|------|
| fdep | v0.6.2 | ✅ PASSED (happy + reject) | `test_fdep_baseline_v0.6.2.{md,json}` |

**重跑生成新基线**：当 `ToT/flows/fdep.json` 升级到 v0.7 时，跑 `tdd-flow.py` 生成新时间戳文件，验证 PASSED 后手工改名为 `test_fdep_baseline_v0.7.{md,json}`。

## 3. 用法

### 3.1 跑一次新测试

```bash
python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json
# 自动生成 test_fdep_<新时间戳>.md + .json
```

### 3.2 查看历史日志

按时间戳排序，最新的在前：

```bash
ls -lt ToT/tdd/test_*.md | head -5
```

### 3.3 对比基线 vs 当前

```bash
# 摘要对比
diff ToT/tdd/test_fdep_baseline_v0.6.2.md <(python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json 2>&1 | grep -A 30 "Happy path")
```

## 4. 清理策略

- **保留**：基线文件（命名带 `baseline_v<X.Y.Z>`）
- **删除**：普通 `test_<flow>_<ts>.{md,json}`（重复 PASSED 快照）
- **频率**：每次新版本基线确立前清理一次
- **备份**：删除前先 `cp -r ToT/tdd/ /tmp/opencode/tdd_backup/`（安全网）

## 5. 关联

- `ToT/sop/tdd-flow.md` — TDD SOP
- `ToT/sop/tdd-flow.py` — 脚本
- `ToT/flows/fdep.json` — 当前流程定义

## 6. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初版（29 个文件，含手写+脚本生成） |
| v0.2 | 2026-09-22 | **精简为基线模式**：26 个重复/历史文件删除，保留最新一份作为 `test_fdep_baseline_v0.6.2.{md,json}`；总大小 440K → 36K；备份在 `/tmp/opencode/tdd_backup/` |
