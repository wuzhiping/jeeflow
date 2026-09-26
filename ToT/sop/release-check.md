# ToT/sop/release.sh + .git/hooks/pre-commit — Phase 4 CI 集成

> **状态**：✅ 已建（2026-09-24）

## 两件套设计

| 脚本 | 触发点 | 行为 |
|---|---|---|
| `.git/hooks/pre-commit` | 每次 `git commit` | 自动跑 `doc-link-checker.py`；若发现 drift 阻止 commit |
| `ToT/sop/release.sh` | 每次发版前 | 跑 4 步检查（drift check → snapshot → diff → changelog preview）|

## pre-commit hook

### 安装

```bash
chmod +x .git/hooks/pre-commit   # 已在 2026-09-24 安装
```

### 行为

1. 检查是否有 staged `ToT/docs/*.md` 文件
2. 若有，跑 `doc-link-checker.py`
3. 若发现 DRIFT → 阻止 commit + 输出 drift 报告 + 提示修复选项
4. 若全部 OK → 正常 commit
5. 若无 staged docs → 跳过（节省时间）

### 跳过方式

```bash
git commit --no-verify   # 紧急情况下
```

⚠️ 仅紧急时使用——跳过 hook = 跳过 drift 检查 = 可能引入未来 drift。

## release.sh

### 用法

```bash
# 默认（自动日期标签）
bash ToT/sop/release.sh

# 指定版本标签
bash ToT/sop/release.sh v1.10.0
```

### 4 步流程

1. **doc-link-checker.py** — 必须 0 drift 才能继续
2. **doc-archive-snapshot.py --label <label>** — 打 snapshot
3. **doc-vs-code-drift.py --latest** — 显示 vs 上一版变化
4. **CHANGELOG.md 状态** — 显示当前快照总数

### 输出示例

```
▶ Step 1: doc-link-checker.py
扫描 134 条引用 → ✅ OK 134 · ⚠️ NEAR_MATCH 0 · ❌ DRIFT 0
✅ 无 drift：所有行号引用与代码一致。

▶ Step 2: doc-archive-snapshot.py
✅ Snapshot saved: ToT/sop/snapshots/2026-09-24T235825Z-v1.9.0-moved-aware-9c4cb5b1.json
   Label: v1.9.0-moved-aware
   Git: 9c4cb5b1 (dev) [dirty]
   Files: 41 · Total lines: 8551 · Total bytes: 483253

▶ Step 3: doc-vs-code-drift.py --latest
... (diff 输出)

▶ Step 4: CHANGELOG.md 累积状态
  总快照数：4

==========================================
  ✅ Release check 通过
  建议：
    1. git add ToT/sop/snapshots/ ToT/docs/CHANGELOG.md
    2. git commit -m 'release: v1.10.0'
    3. git tag -a v1.10.0 -m 'release v1.10.0'
==========================================
```

## CI 集成路线图

| 阶段 | 状态 |
|---|---|
| 本地 pre-commit hook | ✅ 已建（2026-09-24） |
| 本地 release 脚本 | ✅ 已建（2026-09-24） |
| 远程 CI（GitHub Actions / GitLab CI）| ~~⏳ 待建~~ **✗ 取消（2026-09-25）**（本地 release.sh 已足）|
| PR 自动跑 doc-link-checker | ~~⏳ 待建~~ **✗ 取消**（本地 pre-commit 已覆盖）|

## 与现有工具链的关系

```
doc-link-checker.py ─┐
                    ├─→ doc-archive-snapshot.py ─→ doc-vs-code-drift.py ─→ gen-changelog.py
                    │                                                        ↑
                    └────────── release.sh（集成调用）                       │
pre-commit hook ─────┘                                                       │
                                                                              ↓
                                                                          CHANGELOG.md
```

`release.sh` 是 4 个工具的**集成入口**：
- 调用 checker（门禁）
- 调用 snapshot（存档）
- 调用 diff（报告）
- 调用 gen-changelog（自动 CHANGELOG，可选）

## 后续

- ~~[ ] 远程 CI：GitHub Actions YAML（每次 PR 自动跑 checker）~~ **取消 2026-09-25**
- [ ] release.sh 增强：自动 commit snapshot + tag
- [ ] pre-commit hook 增强：同时跑 snapshot 或 diff（更重量级）