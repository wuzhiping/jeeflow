# issue-from-share-file-flow SOP · 从 file-share 取件码建立 issue 跟踪

> **用户原话**：*「先建立 issure-from-share_file-flow sop，通过 file 取件码获取文件，tmp 文件夹内解压，预览，查看，确认需求，给出初步报告，建立 issues/ 以取件码+日期为文件名的 issue 记录并同名用子文件夹存放 raw 文件，取件码重复，只出报告，不动作，等待用户指令，期间不得自行设计，修改其他未经授权的文档和代码」*
>
> **命名映射**：`issure-from-share_file-flow` → **`issue-from-share-file-flow.md`**（拼写 `issure` → `issue`；`_` → `-`，符合现有 13 个 SOP 命名约定）
>
> **核心安全约束**：本 SOP 执行期间**严禁**自行设计、修改任何 SOP / 脚本 / 配置 / 留档；只读必要文件，**只创建** `ToT/issues/<code>_<date>.md` + `<code>_<date>/` 子目录；其他动作需用户明确指令。

---

## 1. 目的与适用场景

### 1.1 目的
接收外部 **file-share 取件码**（来自 file-share skill 上传产物），自动下载 + 解压 + 预览，给出初步报告，并在 `ToT/issues/` 建立可追踪的 issue 记录（含 raw 文件存档），供后续需求确认与实施。

### 1.2 适用场景
| 场景 | 描述 |
|------|------|
| **客户/同事传文件** | "我上传了，请你看看，提个 issue" |
| **跨环境迁移** | 从 customer-test 取回测试数据快照分析 |
| **外部 QA 报告** | QA 上传 BUG 复现包，要求建立可追踪 issue |
| **历史快照对比** | 从 archive 旧取件码回溯历史版本 |

### 1.3 不适用
- ❌ 需要直接对接流程引擎的操作（用 `tdd-flow.py`）
- ❌ 需要修改流程/引擎代码（用 `flow-design.md` / `engine-deploy.md`）
- ❌ 需要上传新文件（用 `archive-flow.md`）

---

## 2. 前置准备

| 项 | 来源 |
|----|------|
| **取件码 `<code>`** | 用户提供（file-share skill 上传后返回） |
| **下载 URL 模板** | `ToT/config/share.json` `share.download_url_template`（即 `https://abc.feg.com.tw/share/select/?code={code}`） |
| **本机工具** | `curl`（带 `-L` follow redirect） + `tar` + `file` + `du` + `head` |
| **`ToT/issues/` 目录** | 首次执行前需初始化（`mkdir -p ToT/issues`） |

---

## 3. 6 步流程

```
Step 1: 输入取件码
  ↓
Step 2: 重复检测 ← 核心安全点（取件码已存在则停止）
  ↓
Step 3: 下载文件（curl -L 到 /tmp）
  ↓
Step 4: tmp 解压 + 预览（不解压到 ToT/）
  ↓
Step 5: 确认需求（与用户对话）
  ↓
Step 6: 初步报告 + 建立 issues/<code>_<date>.md + <code>_<date>/ 子目录
```

---

### Step 1 · 输入取件码

```bash
# 用户口头/消息提供
CODE="<用户给的 6 位数字>"
DATE=$(date +%Y%m%d)
echo "取件码: $CODE, 日期: $DATE"
```

**不做任何动作**，仅记录到本地变量。

---

### Step 2 · 重复检测（核心规则）

```bash
# 检测 ToT/issues/ 是否已有该取件码的记录
EXISTING=$(ls ToT/issues/${CODE}_*.md 2>/dev/null)
if [ -n "$EXISTING" ]; then
    echo "⚠️  取件码 $CODE 已存在 issue 记录："
    echo "    $EXISTING"
    echo ""
    echo "按 SOP 规则：只出报告，不动作，等待用户指令。"
    # → 仅生成"重复报告"，不下载不解压不创建新 issue
    # → 见 §5「重复取件码处理」
fi
```

**规则**：
- ✅ **不下载**、**不解压**、**不创建新 issues/**
- ✅ 仅生成"重复报告"展示历史记录
- ⏸ **等待用户明确指令**（新建 / 续接 / 跳过）

---

### Step 3 · 下载文件

```bash
# 从 share.json 读下载 URL 模板（不要硬编码）
DOWNLOAD_URL=$(jq -r '.share.download_url_template' ToT/config/share.json | sed "s/{code}/$CODE/")
echo "下载: $DOWNLOAD_URL"

# 下载到 /tmp（不进 ToT/）
TMP_DIR=/tmp/issue_${CODE}_${DATE}
mkdir -p "$TMP_DIR"
curl -sS -L --max-time 60 "$DOWNLOAD_URL" -o "$TMP_DIR/file.bin" 2>&1 | tail -3

# 验证
file "$TMP_DIR/file.bin"
ls -la "$TMP_DIR/file.bin"
```

**容错**：
- HTTP 4xx/5xx → 报告错误，**不创建** issue（疑似取件码无效/过期）
- 文件 < 100 bytes → 报告异常（疑似错误页）

---

### Step 4 · tmp 解压 + 预览

```bash
# 自动检测类型并解压（tar.gz / zip / 裸文件）
case "$(file -b "$TMP_DIR/file.bin")" in
    *"gzip compressed"*) tar -xzf "$TMP_DIR/file.bin" -C "$TMP_DIR/extracted" ;;
    *"Zip archive"*)     unzip "$TMP_DIR/file.bin" -d "$TMP_DIR/extracted" ;;
    *)                  mkdir -p "$TMP_DIR/extracted" && cp "$TMP_DIR/file.bin" "$TMP_DIR/extracted/" ;;
esac
mkdir -p "$TMP_DIR/extracted"

# 预览：列出前 30 个文件
echo "=== 文件清单（前 30） ==="
find "$TMP_DIR/extracted" -type f | head -30
echo
echo "=== 目录结构（tree-like，深度 3）==="
find "$TMP_DIR/extracted" -maxdepth 3 -type d

# 关键文件抽样
for f in README.md report.md *.json; do
    [ -f "$TMP_DIR/extracted/$f" ] && {
        echo
        echo "=== $f (前 50 行) ==="
        head -50 "$TMP_DIR/extracted/$f"
    }
done
```

**重要**：预览**仅在 /tmp/**，**不进 ToT/**；用户确认前不复制任何文件到仓库。

---

### Step 5 · 确认需求

**与用户对话，**询问：
1. 这个 issue 是什么类型？（BUG / 需求 / 咨询 / 数据迁移）
2. 需要我做什么？（分析 / 修复 / 设计 / 仅归档）
3. 涉及哪个流程？（fdep / invoice-approval / 其他 / 不涉及）
4. 是否需要写入 `ToT/customer-checks/` 或其他目录？

**约束**：
- ⏸ **不主动设计**任何修复方案
- ⏸ **不修改**任何 SOP / 脚本 / 流程定义
- ⏸ 等用户明确指令后，才能进入 Step 6

---

### Step 6 · 初步报告 + 建立 issue 记录

#### 6.1 创建 issue 文件

```bash
# 命名格式：<取件码>_<日期>.md
ISSUE_FILE="ToT/issues/${CODE}_${DATE}.md"
RAW_DIR="ToT/issues/${CODE}_${DATE}"

# 仅在用户明确"建立 issue"指令后才执行
mkdir -p "$RAW_DIR"
```

**命名示例**：
- `ToT/issues/75829_20260923.md`（取件码 75829, 2026-09-23 处理）
- `ToT/issues/654321_20260925.md`

#### 6.2 issue 模板（`${CODE}_${DATE}.md`）

```markdown
# Issue · 取件码 ${CODE} · ${DATE}

> **创建时间**：${DATE_HUMAN}
> **取件码来源**：${SOURCE_DESC}（如：用户口头 / archive_flow.py / 外部上传）
> **raw 文件**：[`./${CODE}_${DATE}/`](./${CODE}_${DATE}/)
> **状态**：🟡 待用户确认需求

---

## 1. 取件码元信息

- **取件码**: \`${CODE}\`
- **下载 URL**: \`${DOWNLOAD_URL}\`
- **文件名**: \`${ORIG_FILENAME}\`
- **文件大小**: ${SIZE} bytes
- **MIME/类型**: \`${FILE_TYPE}\`
- **有效期**: ${EXPIRE_INFO}（来自 file-share 服务）

---

## 2. 初步预览（来自 tmp 解压）

### 2.1 文件清单
\`\`\`
${FILE_LISTING}
\`\`\`

### 2.2 关键文件摘要
${KEY_FILE_SUMMARIES}

### 2.3 推测意图
- **文件类型**: ${GUESS_TYPE}
- **可能用途**: ${GUESS_PURPOSE}
- **风险信号**: ${RISK_FLAGS:-无}

---

## 3. 确认需求（待用户回复）

| # | 问题 | 用户回复 |
|---|------|----------|
| 1 | Issue 类型？（BUG/需求/咨询/迁移） | |
| 2 | 需要做什么？（分析/修复/设计/归档） | |
| 3 | 涉及哪个流程？ | |
| 4 | 是否需写入 customer-checks/？ | |

---

## 4. 后续行动（用户确认后填写）

| 日期 | 动作 | 涉及文件 | 结果 |
|------|------|----------|------|
| | | | |

---

## 5. 关联文档

${RELATED_DOCS:-（暂无）}

---

## 6. raw 文件说明

子目录 \`./${CODE}_${DATE}/\` 包含从 file-share 下载的原始文件 + 解压产物。
**禁止**修改 raw 内容（只读）；如需修改请在新文件中派生。
```

#### 6.3 复制 raw 到 issues/

```bash
# 仅复制，不修改
cp -r "$TMP_DIR/extracted/." "$RAW_DIR/"
# 或者如果是裸文件：
# cp "$TMP_DIR/file.bin" "$RAW_DIR/${ORIG_FILENAME}"

ls -la "$RAW_DIR/"
```

---

## 4. 安全约束（严格执行）

### 4.1 不允许的动作
| # | 动作 | 原因 |
|---|------|------|
| 1 | **自行设计**修复方案 / 新功能 | 用户未授权 |
| 2 | **修改**任何 SOP（`ToT/sop/*.md`） | 需 SOP 例外审批 |
| 3 | **修改**任何脚本（`ToT/sop/*.py`） | 需 SOP 例外审批 |
| 4 | **修改**任何配置（`ToT/config/*.json`） | 需 SOP 例外审批 |
| 5 | **修改**任何流程定义（`ToT/flows/*.json`） | 需 promote.py |
| 6 | **修改**任何留档（`ToT/customer-checks/` / `iterations/`） | 飞轮原则 |
| 7 | **跨目录**写入（`/tmp` 之外的任何地方除非 `ToT/issues/`） | 安全 |
| 8 | **上传**到 file-share | 用 `archive-flow.md` SOP |

### 4.2 允许的动作
- ✅ 读所有 `ToT/` 下文件（不含 vendor/jeeflow/）
- ✅ 调用 `curl` / `tar` / `file` 等标准工具（系统命令，不修改仓库）
- ✅ 在 `ToT/issues/${CODE}_${DATE}/` 下创建文件（issue 记录 + raw 存档）
- ✅ 在 `/tmp/` 下创建临时文件（自动清理）

---

## 5. 取件码重复处理（核心规则）

### 5.1 检测方式

```bash
EXISTING=$(ls ToT/issues/${CODE}_*.md 2>/dev/null)
```

### 5.2 重复时的行为

```
┌── 检测到取件码已存在 ─────────────────┐
│                                      │
│  1. 停止下载                          │
│  2. 停止解压                          │
│  3. 停止创建新 issue                  │
│  4. 仅生成「重复报告」：              │
│     - 列出已有 issue 文件             │
│     - 列出已有 raw 目录               │
│     - 比对时间戳                      │
│  5. 等待用户指令：                    │
│     - 新建？→ 确认取件码无误后用新日期│
│     - 续接？→ 编辑已有 issue         │
│     - 跳过？→ 直接退出                │
└──────────────────────────────────────┘
```

### 5.3 重复报告模板

```markdown
# ⚠️ 重复取件码报告 · ${CODE} · ${DATE}

> **状态**：取件码已存在，**未执行**任何下载/解压/创建动作。
> **等待**：用户明确指令（新建/续接/跳过）。

## 已有记录

| 文件 | 创建日期 | 大小 | 状态 |
|------|----------|------|------|
${EXISTING_ISSUES_TABLE}

## 比对建议

请用户提供以下信息之一：
1. **确认新建**：是否用更新日期重新建立（`${CODE}_$(date +%Y%m%d).md`）
2. **续接现有**：在已有 issue 上追加新内容
3. **跳过**：本取件码不处理
```

---

## 6. 完整 CLI 示例

### 6.1 手动执行（首次使用）

```bash
#!/usr/bin/env bash
# 用法：./issue-from-share-file-flow.sh <CODE>
set -euo pipefail

CODE="${1:?Usage: $0 <取件码>}"
DATE=$(date +%Y%m%d)
DATE_HUMAN=$(date +"%Y-%m-%d %H:%M:%S")
TMP_DIR=/tmp/issue_${CODE}_${DATE}

# Step 2: 重复检测
EXISTING=$(ls ToT/issues/${CODE}_*.md 2>/dev/null || true)
if [ -n "$EXISTING" ]; then
    echo "⚠️  取件码 $CODE 已存在：$EXISTING"
    echo "只出报告，等待用户指令（新建/续接/跳过）"
    exit 0
fi

# Step 3: 下载
DOWNLOAD_URL=$(jq -r '.share.download_url_template' ToT/config/share.json | sed "s/{code}/$CODE/")
mkdir -p "$TMP_DIR"
curl -sS -L --max-time 60 "$DOWNLOAD_URL" -o "$TMP_DIR/file.bin"

# Step 4: 解压 + 预览
mkdir -p "$TMP_DIR/extracted"
case "$(file -b "$TMP_DIR/file.bin")" in
    *"gzip"*) tar -xzf "$TMP_DIR/file.bin" -C "$TMP_DIR/extracted" ;;
    *"Zip"*)  unzip -q "$TMP_DIR/file.bin" -d "$TMP_DIR/extracted" ;;
    *)        cp "$TMP_DIR/file.bin" "$TMP_DIR/extracted/original" ;;
esac
echo "文件清单："
find "$TMP_DIR/extracted" -type f | head -30

# Step 5: 与用户确认需求（手动对话）

# Step 6: 用户确认后建立 issue
# mkdir -p "ToT/issues/${CODE}_${DATE}"
# cp -r "$TMP_DIR/extracted/." "ToT/issues/${CODE}_${DATE}/"
# 写入 issue markdown 文件...
```

### 6.2 tmp 清理（执行后必做）

```bash
rm -rf /tmp/issue_${CODE}_${DATE}
```

---

## 7. 与其他 SOP 的关系

| SOP | 关系 |
|-----|------|
| **`archive-flow.md`** | 互补：本 SOP 是 `archive-flow` 上传产物的"反向接收"端 |
| **`new-trip.md`** | 新会话开始时可同时清点 `ToT/issues/`（不删除，仅列出） |
| **`flow-design.md`** | 用户确认需求后，若涉及新流程，转入此 SOP |
| **`customer-data-reset.md`** | 若是 customer 数据迁移问题，转入此 SOP |

---

## 8. 检查清单（执行前 + 执行后）

### 8.1 执行前自检

- [ ] 取件码已从用户处获得（不猜测）
- [ ] 已确认 ToT/issues/ 目录存在
- [ ] 已读 `ToT/config/share.json`（确认 download_url_template）
- [ ] **未**携带任何"修改仓库"的预谋

### 8.2 执行后自检

- [ ] **只**创建了 `ToT/issues/${CODE}_${DATE}.md`（如适用）
- [ ] **只**创建了 `ToT/issues/${CODE}_${DATE}/` 子目录（如适用）
- [ ] **未**修改任何其他文件（`git diff --stat` 应只有新增）
- [ ] /tmp 临时文件已清理
- [ ] 等用户确认需求后，issue 状态更新为 ✅

---

## 9. 关联文档

- `ToT/config/share.json` — download URL 模板真相源
- `ToT/issues/` — issue 跟踪根目录
- `ToT/sop/archive-flow.md` — 对称的上传端 SOP
- `ToT/sop/new-trip.md` — 新会话起点（含 issues 清点）

---

## 10. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **初稿**（用户口头指令"先建立 issure-from-share_file-flow sop"）：① 6 步流程（取件码 → 重复检测 → 下载 → 解压 → 确认 → 报告+issue）；② **重复取件码规则**（只报告不动作，等指令）；③ **安全约束**（不修改其他文件）；④ `ToT/issues/<code>_<date>.md` 模板 + `<code>_<date>/` 子目录存放 raw；⑤ CLI 手动示例 + tmp 自动清理；⑥ 与 `archive-flow.md` / `new-trip.md` / `flow-design.md` 关系说明。 |