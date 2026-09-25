# ToT/sop/doc-archive-snapshot.py

> **状态**：✅ 已建（2026-09-24）
> **首次快照**：ToT/sop/snapshots/2026-09-24T235123Z-v1.9.0-final-9c4cb5b1.json
> **快照内容**：40 文件 / 8486 行 / 480992 B / drift 0 / NEAR_MATCH 0

## 用途

每发版前跑一次，生成 ToT/docs 状态快照：

- 每个 .md 的行数 / 字符数 / sha256 / mtime
- doc-link-checker.py drift 报告（OK / NEAR_MATCH / NO_DEF 等计数）
- 当前 git commit + branch + 是否 dirty
- 输出：JSON 文件 + 文本汇总

## 用法

```bash
# 默认（label = "snapshot"）
python3 ToT/sop/doc-archive-snapshot.py

# 带版本标签（推荐用于发版）
python3 ToT/sop/doc-archive-snapshot.py --label v1.9.0

# 跳过 drift 检查（更快）
python3 ToT/sop/doc-archive-snapshot.py --no-checker

# 自定义输出目录
python3 ToT/sop/doc-archive-snapshot.py --out-dir /tmp/snapshots
```

## 输出格式（JSON）

```json
{
  "schema": "doc-archive-snapshot/v1",
  "timestamp": "2026-09-24T23:51:23Z",
  "label": "v1.9.0-final",
  "git": {
    "commit": "9c4cb5b1...",
    "short_sha": "9c4cb5b1",
    "branch": "dev",
    "dirty": true
  },
  "docs_root": "ToT/docs",
  "summary": {
    "file_count": 40,
    "total_lines": 8486,
    "total_bytes": 480992,
    "drift": {
      "total": 134,
      "ok": 134,
      "near_match": 0,
      "drift": 0,
      "tolerance": 5
    }
  },
  "files": {
    "ToT/docs/README.md": {
      "path": "ToT/docs/README.md",
      "size": 22373,
      "lines": 379,
      "sha256": "4980c9fe...",
      "mtime": 1727212345.67
    },
    ...
  },
  "drift_report": {
    "OK": [{"md_file": "...", "code_file": "...", "code_line": 0, ...}]
  }
}
```

## 路径约定

```
ToT/sop/snapshots/
  2026-09-24T235123Z-v1.9.0-final-9c4cb5b1.json
  2026-09-24T235200Z-v1.9.1-final-abc12345.json
  ...
```

- `TIMESTAMP` ISO 8601 UTC（`YYYY-MM-DDTHHMMSSZ`）
- `LABEL` 用户提供（默认 `snapshot`）
- `SHORT_SHA` git 短 hash（无 git 时为 `no-git`）

## 设计要点

- **无第三方依赖**（仅 Python 3.10+ 标准库）
- **子进程调用 doc-link-checker.py**：确保 drift 数实时准确（如未来 checker 逻辑变更，无需改本脚本）
- **git 元数据采集**：commit / branch / dirty 状态全部记录，便于溯源
- **per-file sha256**：未来可对比两个 snapshot 检测单文件变更
- **schema 字段**：v1 标记，未来 schema 升级可平滑迁移

## 已知限制

1. **不做 cross-snapshot diff**：仅生成单点快照，跨快照对比由 Phase 3 #3 `doc-vs-code-drift.py` 实现
2. **不缓存 git 信息**：每次调用都跑 `git status --porcelain`，大型仓库可能慢
3. **不压缩**：JSON 明文存储（无损可读，但占空间大）；如需压缩可后续加 `--gzip`

## 后续

- [ ] Phase 3 #3 `doc-vs-code-drift.py`（跨 snapshot diff）
- [ ] Phase 4 CI 集成：每次 PR 自动跑 snapshot，存 artifact
- [ ] `--gzip` 选项压缩存储
- [ ] snapshot 索引表（README 列出所有历史 snapshot）