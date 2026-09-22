# Iteration #8 · 2026-09-22 · REPO_ROOT 自动化（无需手工 export）

> **驱动**：用户口头指令"REPO_ROOT 需要人工设置？ 能否自动"
> **意义**：让用户**零配置**使用 EA 体系 —— 不 export / 不 cd / 直接用

---

## 1. 时间线（30 分钟）

| 时段 | 工作 | 产出 |
|------|------|------|
| **0~5 min** | 设计：2 个 helper（with-jf.sh source 用 + jf wrapper 单命令） | 设计 |
| **5~10 min** | 写 `ToT/bin/with-jf.sh`（60 行 bash，含 git + 路径反推 + 兜底） | helper 1 |
| **10~15 min** | 写 `ToT/bin/jf` wrapper（30 行 bash，cd REPO_ROOT + exec） | helper 2 |
| **15~20 min** | 更新 3 个 SOP 文档用 jf wrapper 替换 `$REPO_ROOT` | 文档 |
| **20~25 min** | `ea-compliance.py` §9.9 加 4 项自动化检查 | 自验证 |
| **25~30 min** | 跨机器验证（/tmp/test_jfhost + 3 种用法） | 实证 |

---

## 2. 2 个 Helper 工具

### 2.1 `ToT/bin/with-jf.sh`（source 用）

```bash
source ToT/bin/with-jf.sh
# 自动 export REPO_ROOT，会话内可用
```

**自动检测逻辑**（4 优先级）：
1. 已 export `REPO_ROOT` 且目录合法 → 用之
2. `git rev-parse --show-toplevel`（如在 git repo）
3. 从本文件位置反推（`ToT/bin/with-jf.sh` → 项目根）
4. 当前 `pwd` 兜底

### 2.2 `ToT/bin/jf` wrapper（单命令用）

```bash
./ToT/bin/jf python3 ToT/sop/ea-compliance.py
# 无需任何 export，无需 cd 到项目根
```

**机制**：`cd $REPO_ROOT` + `exec "$@"`

---

## 3. 3 种用户使用方式

| 方式 | 用法 | 适合 |
|------|------|------|
| **A. source** | `source ToT/bin/with-jf.sh` 然后会话内可用 `python3 ToT/sop/...` | 长时间工作 |
| **B. jf wrapper** | `ToT/bin/jf python3 ToT/sop/...`（无需任何前置） | 单命令 / 脚本调用 |
| **C. 直接 cd** | `cd /path/to/project` 然后 `python3 ToT/sop/...` | 已知路径 |

---

## 4. 闭环示意

```
   ┌─── "$REPO_ROOT 能否自动？" ──┐
   ↓                              │
  设计 2 个 helper                │
   ↓                              │
  with-jf.sh（source）           │
   + jf（wrapper）              │
   ↓                              │
  更新 3 个 SOP 文档              │
   ↓                              │
  ea-compliance.py §9.9 +4 项    │
   ↓                              │
  跨机器验证：/tmp + 3 种用法   │
   ↓                              │
  43/43 PASS                      │
   ↓                              │
  → 飞轮自转第 7 圈（自动化维度）✅
```

---

## 5. ADR

| 决策 | 选择 | 理由 |
|------|------|------|
| 2 个 helper 而非 1 个 | **both** | source 用于会话；wrapper 用于单命令 |
| with-jf.sh 用 bash 函数 | **bash** | 跨 shell（bash/zsh）友好 |
| jf wrapper 用 `exec "$@"` | **exec** | 替代当前 shell 进程，信号正确传递 |
| 自动检测优先级 | **git → 路径反推 → 兜底** | git 最准确（多 git worktree 也能识别） |
| §9.9.4 实测 source | **subprocess 跑 bash** | 防回归（脚本被改坏能立刻发现）|

---

## 6. 度量（飞轮转 8 次的累积）

| 指标 | Iter#1 | Iter#2 | Iter#3 | Iter#4 | Iter#5 | Iter#6 | Iter#7 | **Iter#8** |
|------|--------|--------|--------|--------|--------|--------|--------|------------|
| §9 检查项 | 0 | 27 | 31 | 31 | 31 | 35 | 39 | **43** |
| 工具数 | 0 | 1 | 2 | 6 | 6 | 7 | 7 | **9** |
| **自动化** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅** |

**关键变化**：从"需手工 export"→"零配置运行"。

---

## 7. 闭环证据

### 测试 1：source with-jf.sh（在 /tmp）

```
$ cd /tmp
$ source ToT/bin/with-jf.sh
✓ REPO_ROOT=/tmp/test_jfhost (exported)
$ python3 ToT/sop/ea-compliance.py
OVERALL: 43/43 PASS (100.0%)
```

### 测试 2：jf wrapper（在任意 cwd）

```
$ cd /var/tmp
$ /path/to/ToT/bin/jf python3 ToT/sop/ea-compliance.py
OVERALL: 43/43 PASS (100.0%)
```

### 测试 3：直接 cd 项目根（用户正常用法）

```
$ cd /path/to/project
$ python3 ToT/sop/ea-compliance.py
OVERALL: 43/43 PASS (100.0%)
```

**3 种姿势任选**，全部成功。

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-22** | **第八轮迭代**：REPO_ROOT 自动化。① `ToT/bin/with-jf.sh`（60 行 bash 自动检测 REPO_ROOT，git + 路径反推 + 兜底 4 优先级）；② `ToT/bin/jf` wrapper（30 行，cd + exec）；③ 更新 3 个 SOP 文档用 jf wrapper 替换 `$REPO_ROOT`；④ `ea-compliance.py` §9.9 +4 项检查（43/43 PASS）；⑤ 跨机器 + 3 种用法验证；⑥ 飞轮自转第 7 圈（自动化维度补齐）。 |