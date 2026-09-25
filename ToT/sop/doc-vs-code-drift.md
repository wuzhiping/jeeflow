# ToT/sop/doc-vs-code-drift.py

> **状态**：✅ 已建（2026-09-24）
> **首次运行**：对比 v1.9.0-final → v1.9.0-postfix（无 drift 变化）

## 用途

对比两个 `doc-archive-snapshot.json`（base / head），输出 4 类变更：

1. **文件级**：added / removed / modified / unchanged（基于 sha256）
2. **数量级**：总行数 / 字节数 delta
3. **drift 状态变化**：OK / NEAR_MATCH / NO_DEF / FILE_NOT_FOUND / LINE_OUT_OF_RANGE 增减
4. **drift 项级**：
   - 新增 drift（head 中出现，base 中没有）
   - 已修复 drift（base 中有，head 中没有）

## 用法

```bash
# 自动取最近 2 个 snapshot
python3 ToT/sop/doc-vs-code-drift.py --latest

# 显式指定
python3 ToT/sop/doc-vs-code-drift.py base.json head.json

# JSON 输出（供 CI 集成）
python3 ToT/sop/doc-vs-code-drift.py --latest --json

# 自定义 snapshot 目录
python3 ToT/sop/doc-vs-code-drift.py --snap-dir ./snapshots --latest
```

## 示例输出

```
Snapshot 对比：v1.9.0-final (9c4cb5b1) → v1.9.0-postfix (9c4cb5b1)
时间：2026-09-24T235123Z → 2026-09-24T235242Z

文件变更：
  + 0 added · - 0 removed · ~ 1 modified · = 39 unchanged
  ~ Modified: ToT/docs/README.md

数量：lines Δ +1 · bytes Δ +214

Drift 状态变化：
  ok: 134 → 134 (Δ +0)
  near_match: 0 → 0 (Δ +0)
  drift: 0 → 0 (Δ +0)
  total: 134 → 134 (Δ +0)

✅ 无新增 / 已修复 drift。
```

## 设计要点

- **基于 sha256 的文件级指纹**：同一文件 sha 一致 → unchanged；不同 → modified
- **drift 项级 key**：`（md_file, md_line, code_file, code_line）` 4 元组 → 唯一标识一条引用
- **drift 状态独立比较**：每个 status（OK / NEAR_MATCH / NO_DEF 等）独立 diff，不混淆
- **无第三方依赖**（仅 Python 3.10+ 标准库）

## 与 doc-link-checker / doc-archive-snapshot 的关系

```
doc-link-checker.py ─┐
                    ├─→ doc-archive-snapshot.py ─→ doc-vs-code-drift.py
doc-archive-snapshot.py ─┘    (snapshot JSON)           (跨 snapshot diff)
```

- `doc-link-checker.py`：扫描 → 报告当前 drift 状态
- `doc-archive-snapshot.py`：把当前 drift 状态打包到 JSON
- `doc-vs-code-drift.py`：对比两个 snapshot，输出变化趋势

## 已知限制

1. **drift 项级 false-positive 已修复**：使用 `logical_key = (md_file, code_file, code_line)` 而非 `(md_file, md_line, code_file, code_line)`，避免 MD 行号变化被误报为新增/删除。位置漂移现在归类为 `moved_drift`（informational）。
2. **不处理 reorder**：两个文件内容相同但顺序变化 → 仍显示为 unchanged（因 sha256 一致）
3. **不识别 snapshot schema 升级**：当前只认 schema `v1`

## 后续

- [ ] `--base HEAD~1` 支持 git ref（不用手动选 snapshot）
- [ ] 输出 markdown 报告（PR 评论用）
- [ ] 加入「首份 snapshot」特例（base 不存在时输出全部新增）
- [ ] Phase 4 CI：PR 自动跑 snapshot diff，超阈值即拒绝合并