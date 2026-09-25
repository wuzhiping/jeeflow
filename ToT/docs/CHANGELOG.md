# ToT/docs CHANGELOG

> 自动生成（`ToT/sop/gen-changelog.py`）。基于 `doc-archive-snapshot.py` 累积快照对比。

**总快照数**：6
**时间跨度**：2026-09-24T235123Z → 2026-09-25T000416Z

---

## 起始基线

- 快照：`2026-09-24T235123Z-v1.9.0-final-9c4cb5b1.json`
- Label：`v1.9.0-final`
- 时间：`2026-09-24T235123Z`
- Git：`9c4cb5b1`
- 文件：40 · 行：8486 · 字节：480992
- Drift：✅ 134 / ⚠️ NEAR_MATCH 0 / ❌ 0

---

## `v1.9.0-postfix` — 2026-09-24T235242Z

- 快照：`2026-09-24T235242Z-v1.9.0-postfix-9c4cb5b1.json`
- Git：`9c4cb5b1`
- 上一版：`v1.9.0-final` (2026-09-24T235123Z)

### 变更摘要

- 文件：+0 added · ~1 modified
- 总行数：Δ +1
- Drift：OK Δ +0 · NEAR_MATCH Δ +0 · DRIFT Δ +0

**修改文件**（按 sha256 变化）：
- `ToT/docs/README.md` (379L → 380L, Δ +1)

---

## `v1.9.0-postfix-fixed` — 2026-09-24T235528Z

- 快照：`2026-09-24T235528Z-v1.9.0-postfix-fixed-9c4cb5b1.json`
- Git：`9c4cb5b1`
- 上一版：`v1.9.0-postfix` (2026-09-24T235242Z)

### 变更摘要

- 文件：+1 added · ~3 modified
- 总行数：Δ +42
- Drift：OK Δ -1 · NEAR_MATCH Δ +0 · DRIFT Δ +0

**新增文件**：
- `ToT/docs/CHANGELOG.md`

**修改文件**（按 sha256 变化）：
- `ToT/docs/README.md` (380L → 382L, Δ +2)
- `ToT/docs/manual/appendix-b-values.md` (191L → 190L, Δ -1)
- `ToT/docs/spec/07-metadata.md` (183L → 179L, Δ -4)

---

## `v1.9.0-moved-aware` — 2026-09-24T235825Z

- 快照：`2026-09-24T235825Z-v1.9.0-moved-aware-9c4cb5b1.json`
- Git：`9c4cb5b1`
- 上一版：`v1.9.0-postfix-fixed` (2026-09-24T235528Z)

### 变更摘要

- 文件：+0 added · ~3 modified
- 总行数：Δ +22
- Drift：OK Δ +1 · NEAR_MATCH Δ +0 · DRIFT Δ +0

**修改文件**（按 sha256 变化）：
- `ToT/docs/CHANGELOG.md` (45L → 67L, Δ +22)
- `ToT/docs/README.md` (382L → 382L, Δ +0)
- `ToT/docs/diffs.md` (282L → 282L, Δ +0)

---

## `snapshot-2026-09-25` — 2026-09-24T235932Z

- 快照：`2026-09-24T235932Z-snapshot-2026-09-25-9c4cb5b1.json`
- Git：`9c4cb5b1`
- 上一版：`v1.9.0-moved-aware` (2026-09-24T235825Z)

### 变更摘要

- 文件：+0 added · ~1 modified
- 总行数：Δ +19
- Drift：OK Δ +0 · NEAR_MATCH Δ +0 · DRIFT Δ +0

**修改文件**（按 sha256 变化）：
- `ToT/docs/CHANGELOG.md` (67L → 86L, Δ +19)

---

## `v1.10.0` — 2026-09-25T000416Z

- 快照：`2026-09-25T000416Z-v1.10.0-9c4cb5b1.json`
- Git：`9c4cb5b1`
- 上一版：`snapshot-2026-09-25` (2026-09-24T235932Z)

### 变更摘要

- 文件：+0 added · ~2 modified
- 总行数：Δ +17
- Drift：OK Δ +0 · NEAR_MATCH Δ +0 · DRIFT Δ +0

**修改文件**（按 sha256 变化）：
- `ToT/docs/CHANGELOG.md` (86L → 103L, Δ +17)
- `ToT/docs/README.md` (382L → 382L, Δ +0)

---

## 工具链

| 脚本 | 用途 | 状态 |
|---|---|---|
| `ToT/sop/doc-link-checker.py` | 扫描所有 .md 中 vendor/jeeflow/*.py 行号引用 | ✅ |
| `ToT/sop/doc-archive-snapshot.py` | 每发版打 JSON 快照 | ✅ |
| `ToT/sop/doc-vs-code-drift.py` | 跨 snapshot diff | ✅ |
| `ToT/sop/gen-changelog.py` | 从 snapshots 生成本文档 | ✅ |
