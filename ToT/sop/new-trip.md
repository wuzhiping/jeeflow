# SOP: 新行程启动清场 (new-trip)

> **所属**：组织 SOP 集（与 spi-verify / tdd-flow / engine-deploy / customer-data-reset 并列）
> **目的**：每次新会话 / 新项目开始前的标准化清场，让起点轻装
> **触发**：用户口头指令"for a new start, lite for the next trip" 类场景

---

## 1. 适用场景

| ✅ 适用 | ❌ 不适用 |
|--------|-----------|
| 新会话开始，想清掉上次积累的测试日志 | 项目首次启动（无历史可清） |
| 重大版本切换前的轻装起步 | 正在排查问题时（保留所有数据） |
| 完成一个里程碑，想"打包存档"后重新开始 | reset 客户服务器数据（那是 customer-data-reset SOP） |
| 用户口头说"new trip" / "lite" / "fresh start" | 备份/迁移（那是 backup-then-reset，待设计） |

## 2. 清理原则

- **保留**：永久规则、基线证据、留档、用户显式要求保留的
- **清理**：临时测试日志、可重新生成的中间产物、过期版本文件
- **备份**：删除前**必先**备份到 `/tmp/opencode/`（安全网，至少保留到下次会话）

## 3. 清理清单（v0.1）

| 路径 | 动作 | 说明 |
|------|------|------|
| `ToT/tdd/test_<flow>_<ts>.{md,json}` | **删除** | 常规测试日志（重复 PASSED 快照） |
| `ToT/tdd/test_<flow>_baseline_v<X.Y.Z>.{md,json}` | **保留** | 基线（升级里程碑证据） |
| `ToT/tdd/INDEX.md` | **保留** | 索引（含命名约定 + 清理策略） |
| `ToT/customer-resets/` | **保留** | 客户服务器操作留档（合规要求） |
| `ToT/customer-checks/` | **保留** | 就绪检查报告 |
| `ToT/sop/` | **保留** | SOP 脚本本身 |
| `ToT/flows/` | **保留** | 流程定义（业务资产） |
| `ToT/{README,HANDBOOK,mapping}.md` | **保留** | 永久规则文档 |
| 项目根 `tdd/` | **不动** | 那是 jeeFlow 引擎自身的 TDD 套件，不属于 ToT/ |
| 项目根 `/tmp/opencode/` | **不动** | 临时文件目录，下次会话前可清 |

## 4. 执行步骤

### Step 1 · 备份安全网

```bash
# 创建本次清场的备份（保留到下次会话）
TS=$(date +%Y%m%d%H%M%S)
mkdir -p /tmp/opencode/new_trip_backup_$TS
cp -r ToT/tdd/ /tmp/opencode/new_trip_backup_$TS/tdd/
echo "备份到 /tmp/opencode/new_trip_backup_$TS/"
```

### Step 2 · 把"最新"测试标记为 baseline

```bash
# 找 ToT/tdd/ 下时间戳最新的 test_<flow>_<ts>.{md,json}
cd ToT/tdd/
LATEST=$(ls -t test_<flow>_*.* 2>/dev/null | head -2)  # .md + .json
# 重命名为 baseline（按当前 flow.json 的 version）
FLOW_VERSION=$(python3 -c "import json; print(json.load(open('../flows/<flow>.json'))['version'])")
for f in $LATEST; do
    ext="${f##*.}"
    base="${f%.*}"
    # 去掉时间戳，保留 <flow>
    flow="${base%%_*}_$(echo $base | cut -d_ -f2)"
    # 注：实际命名规则见下方
    new_name="test_${flow%_*}_baseline_v${FLOW_VERSION}.${ext}"
    mv "$f" "$new_name"
done
```

### Step 3 · 删除常规测试日志

```bash
# 只保留 baseline_* 和 INDEX.md
cd ToT/tdd/
find . -maxdepth 1 -name "test_*_*.*" ! -name "*baseline*" -delete
```

### Step 4 · 更新 INDEX.md

```bash
# 同步基线条目 + 清理策略章节
$EDITOR ToT/tdd/INDEX.md
```

### Step 5 · 验证轻装成功

```bash
# 5.1 三轨 SOP 仍 PASSED
SPI_FOLDER=dev python3 ToT/sop/spi-verify.py
python3 ToT/sop/flow-lint.py ToT/flows/fdep.json

# 5.2 ToT 目录树清爽
find ToT/ -type f | sort
echo "总文件数: $(find ToT/ -type f | wc -l)"
```

### Step 6 · 留档本次 new_trip 操作（可选）

如需追溯历史 new_trip 操作，写 `ToT/customer-checks/new-trip_<ts>.md`：

```markdown
# New Trip 清场 · YYYY-MM-DD HH:MM

## 清场前
- tdd/ 文件数: N
- tdd/ 总大小: Nk

## 清场后
- tdd/ 文件数: M (M ≤ N)
- tdd/ 总大小: Mk
- 保留基线: test_<flow>_baseline_v<X.Y.Z>.{md,json}

## 备份位置
/tmp/opencode/new_trip_backup_<ts>/
```

## 5. 实测案例

### 2026-09-22 第一次 new_trip

| 维度 | 前 | 后 |
|------|-----|-----|
| ToT/tdd/ 文件数 | 29 | 3 |
| ToT/tdd/ 总大小 | 440K | 36K |
| 保留 | INDEX + 全部 28 个 test_* | INDEX + baseline_v0.6.2 |
| 备份 | — | `/tmp/opencode/tdd_backup/`（29 文件） |
| 三轨 SOP | PASSED | PASSED |

## 6. 与其他 SOP 的关系

| SOP | 关系 |
|-----|------|
| `customer-data-reset` | new_trip 是**本地轻装**；customer-data-reset 是**远程数据清空**。两者都"清"，但目标和对象不同 |
| `tdd-flow` | new_trip 清理 tdd-flow 产生的常规日志；tdd-flow 仍可继续运行 |
| `engine-deploy` | new_trip 不涉及引擎代码改动；engine-deploy 是引擎级变更流程 |
| `spi-verify` / `flow-lint` | new_trip 后必跑，确保轻装未破坏核心 |

## 7. 关联文档

- `ToT/HANDBOOK.md` — 知识手册（含 new_trip 在内的所有 SOP 索引）
- `ToT/tdd/INDEX.md` — TDD 测试日志目录的命名约定 + 清理策略

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：用户口头指令"for a new start, let clear tdd/ hisotry data, lite for the next trip" 沉淀为 SOP。6 节：场景 / 原则 / 清单 / 步骤 / 实测 / 关联。包含 5 步执行流程 + 备份安全网 + 留档模板。首次应用：tdd/ 从 29 文件 / 440K 精简到 3 文件 / 36K（保留 baseline_v0.6.2）。 |
