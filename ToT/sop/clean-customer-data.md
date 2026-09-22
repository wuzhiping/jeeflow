# SOP: 清理客户私有数据 (clean-customer-data)

> **所属**：组织 SOP 集（与 `customer-data-reset` 互补）
> **场景**：清理 `ToT/customer-checks/` + `ToT/customer-resets/` 中的客户操作留档
> **永久规则**：见 `ToT/README.md` §1 + §11
> **与 customer-data-reset 的区别**：
>   - `customer-data-reset` 清**远程数据库**（PG TRUNCATE wf_process_*）
>   - `clean-customer-data` 清**本地留档目录**（删除/归档历史操作记录）
>   - 两者都"清"，但对象不同：前者清**客户运行时数据**，后者清**本地对客户操作的审计痕迹**

---

## 1. 适用场景

| ✅ 适用 | ❌ 不适用 |
|--------|-----------|
| 客户测试服务器实例 ID 泄露风险（留存档被外部访问） | 远程数据库本身的数据（用 customer-data-reset） |
| 留档目录膨胀（>50 文件 / >1MB）需要清理 | 备份文件（备份保留独立策略） |
| 项目移交 / 客户关系结束 | 当前会话调试中的文件（保留 N 份供回看） |
| 合规要求（GDPR / 客户数据最小化原则） | — |

## 2. 清理原则（v0.1）

| 维度 | 默认策略 | 可调整 |
|------|----------|--------|
| **保留份数** | 每个目录保留**最近 3 份**（按 mtime 倒序） | `--keep N` |
| **剩余处理** | 归档到 `/tmp/opencode/customer_data_archive_<ts>/` | `--delete`（直接删，不归档） |
| **备份位置** | `/tmp/opencode/customer_data_archive_<ts>/` | 任意路径 |
| **触发** | 按需（人工触发）+ 每次 `customer-data-reset` 后建议 | — |

## 3. 清理清单

| 目录 | 内容 | 是否含客户私有数据 |
|------|------|---------------------|
| `ToT/customer-checks/*.md` | 就绪检查报告、新清场留档 | ⚠️ 是（instanceId / defineId / operator） |
| `ToT/customer-resets/*.md` | 远程 reset 操作留档 | ⚠️ 是（实例 ID + 操作时间 + 健康状态） |
| `ToT/customer-debugs/*.md`（未来可能） | 远程调试留档 | ⚠️ 是 |

**不清理的目录**：

| 目录 | 原因 |
|------|------|
| `ToT/tdd/` | 是测试基线（按 `new-trip.md` SOP 管理） |
| `ToT/customer-data-resets-backup/`（未来可能） | 备份目录独立保留策略 |
| `/tmp/opencode/customer_data_archive_*/` | 已归档目录保留 30 天 |

## 4. 执行步骤

### Step 1 · 备份到归档目录

```bash
# 备份整个目录（不区分新旧）
TS=$(date +%Y%m%d%H%M%S)
mkdir -p /tmp/opencode/customer_data_archive_$TS
cp -r ToT/customer-checks/ /tmp/opencode/customer_data_archive_$TS/customer-checks/
cp -r ToT/customer-resets/ /tmp/opencode/customer_data_archive_$TS/customer-resets/
echo "归档到 /tmp/opencode/customer_data_archive_$TS/"
```

### Step 2 · 保留最近 N 份，删除其余

```bash
KEEP=3  # 默认保留最近 3 份，可改为 5 / 10 等

for DIR in ToT/customer-checks ToT/customer-resets; do
    cd $DIR
    # 按 mtime 倒序排列，跳过前 KEEP 个，其余删除
    ls -t *.md | tail -n +$((KEEP + 1)) | xargs -r rm -f
    cd ../..
done
```

**判断依据**：按文件**修改时间**（mtime）排序，保留最新 KEEP 份。

### Step 3 · 验证清理结果

```bash
# 3.1 两个目录现状
echo "=== ToT/customer-checks/ ==="
ls -la ToT/customer-checks/

echo "=== ToT/customer-resets/ ==="
ls -la ToT/customer-resets/

# 3.2 总大小
echo "总大小:"
du -sh ToT/customer-checks/ ToT/customer-resets/

# 3.3 归档仍在
echo "归档:"
ls -d /tmp/opencode/customer_data_archive_*/
```

### Step 4 · 留档本次操作

```bash
# 在归档目录写 README 说明本次清理
TS=$(date +%Y%m%d%H%M%S)
cat > /tmp/opencode/customer_data_archive_$TS/README.md << EOF
# Customer Data Archive · 2026-09-22 HH:MM

## 触发
- 用户口头指令 "clean customer-checks, customer-resets"
- 或 customer-data-reset 后的建议清理

## 清理范围
- customer-checks/: N → M 文件
- customer-resets/: N → M 文件
- 保留: 最新 3 份 (按 mtime)
- 删除: 其余文件

## 恢复方法
如需恢复某文件，从本归档目录 cp 回去即可。
EOF
```

### 完整一键命令（默认 KEEP=3）

```bash
TS=$(date +%Y%m%d%H%M%S)
KEEP=${1:-3}

set -e
cd $REPO_ROOT  # 或用 ToT/bin/jf wrapper

# Step 1: 归档
mkdir -p /tmp/opencode/customer_data_archive_$TS
cp -r ToT/customer-checks/ /tmp/opencode/customer_data_archive_$TS/customer-checks/
cp -r ToT/customer-resets/ /tmp/opencode/customer_data_archive_$TS/customer-resets/

# Step 2: 删除
for DIR in ToT/customer-checks ToT/customer-resets; do
    cd $REPO_ROOT/$DIR  # 或 ToT/bin/jf
    ls -t *.md 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f
done

# Step 3: 验证
echo "[verify]"
echo "  customer-checks: $(ls ToT/customer-checks/ | wc -l) 文件"
echo "  customer-resets: $(ls ToT/customer-resets/ | wc -l) 文件"
echo "  归档: /tmp/opencode/customer_data_archive_$TS/"

# Step 4: 归档 README
cat > /tmp/opencode/customer_data_archive_$TS/README.md << EOF2
# Customer Data Archive · $(date +%Y-%m-%d\ %H:%M)

## 清理
- KEEP=$KEEP
- customer-checks: $(ls /tmp/opencode/customer_data_archive_$TS/customer-checks/ | wc -l) → $(ls ToT/customer-checks/ | wc -l)
- customer-resets: $(ls /tmp/opencode/customer_data_archive_$TS/customer-resets/ | wc -l) → $(ls ToT/customer-resets/ | wc -l)

## 恢复
cp /tmp/opencode/customer_data_archive_$TS/{customer-checks,customer-resets}/*.md ToT/{customer-checks,customer-resets}/
EOF2
```

## 5. 风险与回滚

| 风险 | 缓解 |
|------|------|
| 误删重要留档 | Step 1 全量归档到 `/tmp/opencode/`（不删原始，先归档） |
| 归档目录本身膨胀 | 归档目录保留 30 天（建议），到时再清理 |
| 误用 `--delete` 直接删 | 当前 SOP 默认归档，`--delete` 需显式传参 |
| mtime 误判（git pull 重置 mtime） | 按文件名排序作为备选（KEEP +1 列表式）：`ls -1tr` |

**回滚**：
```bash
# 从最近一次归档恢复
LATEST=$(ls -td /tmp/opencode/customer_data_archive_*/ | head -1)
cp $LATEST/customer-checks/*.md ToT/customer-checks/
cp $LATEST/customer-resets/*.md ToT/customer-resets/
```

## 6. 与其他 SOP 的关系

| SOP | 关系 |
|-----|------|
| `customer-data-reset` | **互补**：reset 清远程数据库；clean 清本地留档。建议每次 reset 后跑一次 clean |
| `new-trip` | new-trip 清 `ToT/tdd/`（测试日志）；clean 清 `ToT/customer-checks` + `customer-resets`（运营留档）。两类目录分开清理 |
| `engine-deploy` | 互不影响（engine-deploy 改代码，不改留档） |
| `tdd-flow` | 互不影响（tdd-flow 写 ToT/tdd/，clean 不碰） |

## 7. 关联文档

- `ToT/sop/customer-data-reset.md` — 远程数据 reset
- `ToT/sop/new-trip.md` — 本地测试日志清理
- `ToT/README.md §1` — 例外审批留档
- `ToT/README.md §11` — 客户测试服务器 + 留档策略

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：默认保留最近 3 份 + 归档到 `/tmp/opencode/customer_data_archive_<ts>/`；互补于 customer-data-reset；适用范围限定 customer-checks + customer-resets |