# Phase 4 延展：/healthz 版本元数据增强

> **状态**：✅ 已实现（2026-09-25）
> **目标**：客户支持时 `curl /healthz` 一行即可确认运行版本，与 ToT/docs CHANGELOG.md 自动对齐

## 设计要点

### 1. 单一来源：`vendor/jeeflow/__init__.py`

```python
__version__ = "1.10.0"             # semver：major.minor.patch
__version_full__ = "1.10.0+9c4cb5b"  # 含 git sha 后缀
__git_sha__ = "9c4cb5b"           # 8 字符短 hash
__build_time__ = "2026-09-25T00:04:11Z"  # ISO 8601 UTC
```

**4 个字段**：
- `__version__` — semver（运维对客户版本对齐用）
- `__version_full__` — semver + git sha（issue 排查用）
- `__git_sha__` — 8 字符短 hash（精确 commit 用）
- `__build_time__` — ISO 8601（构建时间审计用）

### 2. healthz 端点返回格式

```bash
$ curl http://localhost:8101/healthz
{
    "status": "UP",
    "backend": "python",
    "version": "1.10.0",
    "version_full": "1.10.0+9c4cb5b",
    "git_sha": "9c4cb5b",
    "build_time": "2026-09-25T00:04:11Z",
    "pg": "ok"
}
```

**4 个版本字段替代 1 个硬编码字符串**：
- 旧版：`{"version": "v1.9.0+"}` （admin_health 硬编码）
- 新版：`{version, version_full, git_sha, build_time}`（healthz + admin_health 都读 `__init__.py`）

### 3. release.sh 自动同步

```bash
$ bash ToT/sop/release.sh v1.10.0
==========================================
  ToT/docs Release Check
  Label: v1.10.0
  Version: 1.10.0
  Git SHA: 9c4cb5b
==========================================

▶ Step 1: doc-link-checker.py → 0 drift ✅
▶ Step 2: 更新 vendor/jeeflow/__init__.py:__version__
  ✅ vendor/jeeflow/__init__.py 已更新
▶ Step 3: doc-archive-snapshot.py → snapshot 打成功
▶ Step 4: doc-vs-code-drift.py --latest → 显示变化
▶ Step 5: CHANGELOG.md → 总快照数 6
==========================================
  ✅ Release check 通过
```

**Step 2 自动 sed 更新**：
- `__version__ = "1.10.0"`（从 label `v1.10.0` 提取）
- `__version_full__ = "1.10.0+9c4cb5b"`（semver + git sha）
- `__git_sha__ = "9c4cb5b"`（8 字符短 hash）
- `__build_time__ = "2026-09-25T00:04:11Z"`（ISO 8601 UTC）

### 4. 与客户版本对齐流程

```
开发 release v1.10.0
    ↓
bash release.sh v1.10.0   ← 自动更新 __version__
    ↓
git commit + tag v1.10.0
    ↓
部署到客户环境
    ↓
客户支持时：
  curl http://<host>:8101/healthz
    ↓
  看到 version=1.10.0, git_sha=9c4cb5b
    ↓
  对照 ToT/docs/CHANGELOG.md v1.10.0 条目
    ↓
  快速定位是哪个 commit 的问题
```

### 5. 端点应用层

| 端点 | 来源 | 字段 | 用途 |
|---|---|---|---|
| `GET /version` | `main_common.py:848` | 4 字段（仅版本元数据） | 客户支持快速确认版本 |
| `GET /healthz` | `main_common.py:829` | 4 字段 + status + pg | 完整健康检查 |
| `GET /api/admin/health` | `main_common.py:864` | 同上 + 详细 checks | 运维详细监控 |
| `GET /api/admin/trace` | `main_common.py` | 可加 version 字段 | 链路追踪 |

### 6. 设计决策记录

| 选项 | 决定 | 理由 |
|---|---|---|
| 用 `__version__` 而非 `VERSION` 文件 | ✅ | Python 惯例，无需额外文件读取 |
| 自动 sed vs git describe | 自动 sed | git tag 可能丢失（如未 push），sed 更可靠 |
| 4 字段 vs 1 字段 | 4 字段 | 不同场景需要不同粒度（运维/sha/时间）|
| healthz + admin_health 都改 | ✅ | 单一来源 |

### 7. 与 ToT/docs 工具链集成

```
release.sh v1.10.0
    ├─→ 更新 __version__ (sed)
    ├─→ doc-link-checker.py (drift gate)
    ├─→ doc-archive-snapshot.py (存档)
    ├─→ doc-vs-code-drift.py (变化报告)
    └─→ gen-changelog.py (CHANGELOG.md)
            ↓
    客户环境 curl /version → 4 字段
    或     curl /healthz → 4 字段 + status + pg
            ↓
    对照 CHANGELOG.md 确认 commit
```

### 8. 后续

- [ ] release.sh 增强：自动 `git commit` + `git tag`
- [x] `/version` 独立端点（仅返回 version 元数据，不含 status/pg） — ✅ 2026-09-25
- [ ] 在 healthz 增加 `uptime_seconds` / `process_count` 字段
- [ ] `--rollback VERSION` 模式：回滚 __version__ 到指定版本
- [ ] ~~远程 CI：GitHub Actions 跑 release.sh 自动发版~~ — **取消 2026-09-25**（本地 release.sh 已足）