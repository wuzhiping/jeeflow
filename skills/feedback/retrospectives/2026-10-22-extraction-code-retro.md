# users.md 取件码机制复盘 · 2026-10-22 (FB-0013, shwoo)

> **复盘对象**: 取件码 77045 全流程 (收到 → 误判 → 修正 → 闭环)
> **复盘目的**: 提炼取件码机制的 hermes SOP, 避免下次再误判
> **状态**: 🟡 v0.1, 待 hermes 内化

---

## 1. 取件码机制全景

### 1.1 通道对比

| 通道 | 工具 | 用户类型 | 沟通方式 | hermes 工具 |
|------|------|----------|----------|-------------|
| **DM 通道** | hermes-peer-dm | 可双向沟通 (flowuser 等) | 同步 DM, 等回复 | `hermes peer dm` |
| **file-share 通道** | skills:file-share | 不可双向, 异步 | **取件码 + URL** | `skills:file-share` skill |

**关键**: 这两条通道**互斥**, hermes 必须先判断走哪条.

### 1.2 取件码机制工作流 (异步用户)

```
[用户] 通过 file-share 上传文件
  ↓
[file-share 服务] 返回 提取码 (取件码) + 下载 URL
  ↓
[用户] 把取件码告诉 hermes (DM 或 其他方式)
  ↓
[hermes] 用取件码 + URL 下载 tar
  ↓
[hermes] 解包 + 文件分析 + 解读
  ↓
[hermes] 登记 FB (按解读结果)
```

### 1.3 hermes SOP 第 6 步: 取件码处理 (新增)

| # | 动作 | 输出 |
|---|------|------|
| 1 | **先认领取件码 + 询问主人** | "哪个用户的取件码? user_id 是?" |
| 2 | **下载 tar (按 file-share skill)** | `/tmp/XX/issue.tar.gz` |
| 3 | **解压 + 列文件清单** | 9 个文件, 类型明确 |
| 4 | **判断文件性质** | hermes 自己的文件? 还是用户真实数据? |
| 5 | **解读 issue** | BUG / 改进 / 验证报告 / 错误 |
| 6 | **登记 FB (按解读结果)** | FB-NNNN.json 写明 user_id + 取件码 |
| 7 | **归档工件 (如适用)** | `skills/contrib/<user>-<topic>/` |
| 8 | **更新 metrics** | closed_count + 1 |
| 9 | **复盘 + 写 lessons_learned** | hermes 自反思 + 教训 |

**关键**: 第 1 步 "先认领 + 询问主人" 是 hermes 上次误判的根因 (漏了).

---

## 2. hermes 上次误判复盘 (取件码 77045)

### 2.1 时间线

| 时间 | 事件 | hermes 行为 | 正确? |
|------|------|--------------|-------|
| T0 | 用户消息: "取件码: 77045" + 贴 skills/users.md 全文 | hermes 立即分析 | ❌ 错误 (没先问主人) |
| T0+5min | hermes 假设 = flowuser | hermes 写澄清话术 | 🟡 部分对 (错认主, 但对流程) |
| T0+15min | 用户澄清: "不是 flowuser, 是另一个无法沟通的 user" | hermes 修正路径 | ✅ 修正 |
| T0+45min | 用户安装 file-share skill + 重新请求 | hermes 下载 tar | ✅ 正确路径 |
| T0+50min | hermes 解包 + 解读: 9 个 BDD 工件 | hermes 写解读 | ✅ 正确 |
| T0+60min | hermes 登记 FB-0013 closed + 归档 + 教训 | hermes 闭环 | ✅ 闭环 |

### 2.2 hermes 误判的 3 个根因

| # | 根因 | 改进 |
|---|------|------|
| 1 | **跳过第 1 步 "先问主人"** | 直接分析内容 → 错认主 |
| 2 | **混淆 DM 通道 vs file-share 通道** | 默认当 flowuser DM 处理 |
| 3 | **没意识到 hermes 自己的文件被贴** | 看到 users.md → "哦 hermes 自己的规范" → 误以为 B 选项 |

### 2.3 教训 (写进 users.md)

1. **取件码必须先认领主人** (最重要)
2. **DM 通道 vs file-share 通道必须在第一时间区分**
3. **看到 hermes 自己的文件 = 不假装分析, 立即登记 incomplete-info**
4. **file-share 用户的真实意图 = 文件内容本身**, 不靠 DM 澄清
5. **下载 + 解压后才知真实内容**, 不要在下载前猜

---

## 3. hermes SOP 决策树 (取件码处理)

```
看到 "取件码: NNNNN" + 文件 (或未贴文件)
  │
  ├─ 是否已贴文件?
  │   ├─ 否 → 问 "请用 file-share 上传文件, 然后给取件码 + 文件名清单"
  │   └─ 是 → 下载 tar + 解压 + 文件清单
  │
  ├─ 解压后文件清单性质?
  │   ├─ hermes 自己的文件 (skills/users.md, RML.md, etc.)
  │   │   └─ → 立即登记 FB-NNNN type=incomplete-info (误贴或确认)
  │   │
  │   ├─ 真实证据 (ndjson / JSON / worklog / BDD 工件)
  │   │   └─ → 严格按文件分析, 解读 issue
  │   │
  │   └─ 混合 (hermes 自己的文件 + 用户数据)
  │       └─ → 仅分析用户数据部分, hermes 自己的文件 skip
  │
  ├─ 文件性质判断后, hermes 是否能解读?
  │   ├─ 是 → 解读 issue + 登记 FB (type=bug/improve/doc/...)
  │   └─ 否 → 登记 FB type=incomplete-info (P3)
  │
  └─ 闭环方式?
      ├─ hermes 能闭环 → FB closed + 归档 + 教训
      └─ hermes 不能闭环 (异步, 无双向) → FB received (持续跟踪)
```

---

## 4. 关键判断矩阵 (取件码 vs DM)

| 场景 | 应该问什么 | hermes 应该做的 |
|------|-----------|-----------------|
| 看到"取件码: 77045" 没贴文件 | "哪个用户的取件码? 请用 file-share 上传文件" | 不分析, 等文件 |
| 看到"取件码: 77045" + 文件 | 下载 + 解压 + 列清单 | 先列清单, 不假装分析 |
| 解压后是 hermes 自己的文件 | 立即登记 incomplete-info | 不假装分析 |
| 解压后是真实证据 | 严格按文件分析 | 登记 FB + 解读 |
| 文件混合 (hermes + 用户) | 仅处理用户部分 | hermes 部分 skip |
| 用户是 flowuser (DM 通道) | 用 hermes-peer-dm | 同步 DM, 等回复 |
| 用户是 async (file-share) | 用 skills:file-share | 异步, 仅解读文件 |

---

## 5. hermes SOP (取件码机制) 完整版

### 5.1 收到取件码 (Step 1)

**动作**: 第一句话必须问 2 件事:

```
[hermes] 收到取件码 77045. 请确认:
1. 哪个用户的取件码? (user_id / 昵称)
2. 文件清单是什么? (如已上传, 请告诉我)
```

**禁止**: 直接分析内容 / 假设用户.

### 5.2 下载 + 解压 (Step 2-3)

**动作**: 用 file-share skill 下载 tar.gz, 解压到 `/tmp/opencode/<取件码>/`.

```
$ curl -L -o /tmp/opencode/77045/issue.tar "https://abc.feg.com.tw/share/select/?code=77045"
$ mv /tmp/opencode/77045/issue.tar /tmp/opencode/77045/issue.tar.gz
$ tar -xzf /tmp/opencode/77045/issue.tar.gz
$ ls -la /tmp/opencode/77045/
```

### 5.3 列文件清单 (Step 4)

**动作**: 输出 9 个文件的清单 + 大小 + 类型判断.

```
文件清单 (9 个):
- flows/01-simple.json (1708 B, 流程 JSON)
- bdd/run_10_times.py (4155 B, 测试脚本)
- ... etc
```

### 5.4 判断文件性质 (Step 5)

**检查清单**:
- [ ] 文件内容是 hermes 自己的文件吗? (skills/, docs/, README.md 等)
- [ ] 文件是真实证据吗? (ndjson / JSON / worklog / 测试报告)
- [ ] 文件有日期戳吗? (判断时效性)
- [ ] 文件路径暗示用户身份吗? (/home/shwoo/...)

### 5.5 解读 issue (Step 6)

**按文件性质分类解读**:

| 文件类型 | 解读方式 |
|----------|----------|
| 流程 JSON (flows/*.json) | 节点拓扑 + 字段 + assignees + form |
|  BDD 报告 (*.md) | 测试结果 + verify warnings + AGENTS.md compliance |
| 测试 runner (*.py) | 评估是否纳入 hermes SLA 工具集 |
| ndjson | 流程实例时间线 + 事件序列 |
| worklog | 引擎日志 + 异常堆栈 |

### 5.6 登记 FB (Step 7)

**按解读结果登记**:

| 解读结果 | FB type |
|----------|---------|
| 真 BUG | bug / P0-P2 |
| 改进建议 | improve / P1-P3 |
| 文档不清 | doc / P1-P3 |
| 验证报告 | improve / P3 (认领) |
| W009 等 warning | doc / P3 (归档备查) |
| 贡献脚本/工件 | improve / P2 (采纳) |
| hermes 自己的文件 | incomplete-info / P3 (误贴) |

### 5.7 归档 + 教训 (Step 8-9)

**归档路径**: `skills/contrib/<user_id>-<topic>/`

**教训**: hermes 自反思 + hermes 自纠错 (如: "上次我误判了, 这次要先问主人").

---

## 6. 取件码机制的反模式

| 反模式 | 后果 | 改进 |
|--------|------|------|
| 看到取件码立即分析内容 | 错认主 + 假装闭环 | 先问主人 |
| 默认当 flowuser DM 处理 | 异步用户需求未满足 | 区分通道 |
| 看到 hermes 自己的文件假装分析 | 推导出错误的 "用户意图" | 立即登记 incomplete-info |
| 不下载就解读 | 凭空猜测, 浪费精力 | 下载 + 解压后才解读 |
| 不归档工件 | 用户的贡献丢失 | 归档到 skills/contrib/ |
| 不写教训 | 同类错误再犯 | 每次都写 lessons_learned |

---

## 7. 取件码机制的扩展 (未来)

### 7.1 取件码 + 自动归档

未来 hermes SOP 可扩展:
- 取件码收到 → 自动下载 + 解压 + 归档
- 文件性质判断 → 自动分类
- 真实证据 → 自动解读 + 登记 FB
- hermes 自己的文件 → 自动 skip + 登记 incomplete-info

### 7.2 取件码 + 元数据追踪

未来可追踪: 表格存 `skills/contrib/_index.json` 记录每个取件码 + 用户 + 主题 + 闭环状态.

### 7.3 取件码 + 用户等级升级

异步用户的"主动贡献"行为 → 用户类型 L3 (升级).
- L1: 一次性 file-share
- L2: 多次 file-share (持续跟踪)
- L3: 多次 file-share + 主动贡献 (脚本/工件/报告)

---

## 8. 本次复盘结论 (关键)

| 结论 | 内容 |
|------|------|
| **取件码机制 = hermes SOP 强制流程** | 9 步, 必须按顺序 |
| **第 1 步 "先问主人" 是关键** | hermes 上次漏了 |
| **DM 通道 ≠ file-share 通道** | 必须在第一时间区分 |
| **hermes 自己的文件被贴 = 立即登记 incomplete-info** | 不假装分析 |
| **本次闭环成功 (FB-0013 closed)** | 用户需求 = 验证报告认领 + W009 解读 + 脚本评估, 已满足 |
| **用户模式新增: L3 主动贡献** | 异步用户的最高形态 |

---

⏱️ Last updated: 2026-10-22 · 取件码机制复盘 v0.1 · hermes SOP 提炼