# ToT/sop/gen-changelog.py

> **状态**：✅ 已建（2026-09-24）
> **首次输出**：CHANGELOG.md（2 个 snapshot）

## 用途

按时间顺序遍历 `ToT/sop/snapshots/*.json`，对比相邻 snapshot 的差异，输出 Markdown 格式累积变更日志。

输出包含：
- 起始基线（首个 snapshot）
- 每个后续版本 vs 上一版本的：
  - 新增 / 修改文件清单（按 sha256）
  - 总行数 delta
  - drift 计数变化（OK / NEAR_MATCH / DRIFT 增减）
- 工具链表（4 个脚本状态）

## 用法

```bash
# 输出到 stdout（预览）
python3 ToT/sop/gen-changelog.py

# 输出到仓库根 CHANGELOG.md
python3 ToT/sop/gen-changelog.py --output /path/to/CHANGELOG.md

# 只取最近 10 个 snapshot
python3 ToT/sop/gen-changelog.py --limit 10

# 自定义 snapshot 目录
python3 ToT/sop/gen-changelog.py --snap-dir ./mysnapshots
```

## 输出示例

```markdown
# ToT/docs CHANGELOG

> 自动生成（`ToT/sop/gen-changelog.py`）。
**总快照数**：2
**时间跨度**：2026-09-24T235123Z → 2026-09-24T235242Z

## 起始基线

- 快照：`2026-09-24T235123Z-v1.9.0-final-9c4cb5b1.json`
- Label：`v1.9.0-final`
- 文件：40 · 行：8486 · 字节：480992
- Drift：✅ 134 / ⚠️ NEAR_MATCH 0 / ❌ 0

## `v1.9.0-postfix` — 2026-09-24T235242Z

### 变更摘要

- 文件：+0 added · ~1 modified
- 总行数：Δ +1
- Drift：OK Δ +0 · NEAR_MATCH Δ +0 · DRIFT Δ +0

**修改文件**：
- `ToT/docs/README.md` (379L → 380L, Δ +1)

## 工具链

| 脚本 | 用途 | 状态 |
|---|---|---|
| `ToT/sop/doc-link-checker.py` | ... | ✅ |
| `ToT/sop/doc-archive-snapshot.py` | ... | ✅ |
| `ToT/sop/doc-vs-code-drift.py` | ... | ✅ |
| `ToT/sop/gen-changelog.py` | ... | ✅ |
```

## 设计要点

- **零依赖**：仅 Python 3.10+ 标准库（json / argparse / pathlib / dataclasses）
- **累积式**：所有相邻 snapshot 对比，按时间顺序遍历
- **可限定**：--limit 参数只输出最近 N 个版本
- **可重定向**：--output 直接写文件，或 stdout 预览
- **错误容忍**：单 snapshot 解析失败仅警告，不阻断整体生成

## 完整工具链

```
doc-link-checker.py ─┐
                    ├─→ doc-archive-snapshot.py ─→ doc-vs-code-drift.py ─→ gen-changelog.py
doc-archive-snapshot.py ─┘                                              (Markdown 输出)
```

4 个脚本串联：扫描 → 快照 → diff → CHANGELOG。

## 已知限制

1. **不识别 schema v2+**：若未来 snapshot schema 变更，需更新本脚本
2. **修改文件不显示具体行号变化**：仅显示文件总行数 delta（不显示每行变更）
3. **首次 snapshot 无 diff**：仅显示基线信息
4. **CHANGELOG 自动覆盖**：每次运行覆盖整个文件（不留历史 CHANGELOG 版本）

## 后续

- [ ] `--append` 模式：保留历史 CHANGELOG 版本
- [ ] 加入「每文件行级 diff」输出（用 `difflib`）
- [ ] CI 集成：每次发版自动运行，结果 commit 到仓库
- [ ] Phase 4：把 gen-changelog 接入 PR 流水线