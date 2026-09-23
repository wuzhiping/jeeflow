# 参考使用以下命令，可以反复获取flow user的实际使用状况，并获取运行细节
  * 有些用户无法实时沟通，他们会使用 **skills:file-share** 打包并上传所有的相关 Issue, 通过**取件码**获取详情是**唯一**途径
  * **file-share 是持续 (continuous) 反馈渠道**, 不是一次性接收
  * 用户与开发环境并不在一台计算机上，使用**内存版本的工作流引擎**可以通过以下地址访问：https://abc.feg.cn/jeeflow/
  * **不要闭门造车，一切以用户的角度出发，引导用户，表达真实的业务场景和需求**
  * ⚠️ **绝不能 reset 用户的数据** · 用户实例 = 真实工作内容
    - 禁止调用 `/api/reset`
    - 禁止调用 `_reset_memory()`
    - 所有测试必须在本地实例 (`main.py` 8101 / `main_pg.py` 8102) 进行
    - 详见 `skills/FREEZE.md §6.2` 客户数据绝对不可触碰

---

## ⚠️ 核心原则 (FB-0013 取件码 77045 复盘提炼 · 2026-10-22)

  * **chat 内容 ≠ 取件码对应文件内容**
    - chat 里贴的文件可能是 hermes 自己的规范, 误贴, 或测试
    - **真正的反馈内容 = 取件码对应文件** (必须下载才能解读)
    - 看到 chat 贴文件时, **不立即分析**, 先问"取件码是什么?"
  * **file-share 是持续反馈渠道**
    - 用户可随时上传新文件, hermes 应按用户等级 (L1/L2/L3) 持续监控
  * **主人必须问, 不能假设**
    - 不能从 chat 推测 = flowuser
    - 不能从 zip 路径推测 = shwoo
    - **必须用户明确告知**
  * **hermes 自己的文件被贴 = 立即登记 incomplete-info**
    - 假装解读 hermes 自己的规范 = 假装闭环 = 假装完成
    - 不假装分类"误贴/确认/测试", 不假装解读"用户意图"
  * **下载 + 解读 + 决定 = hermes SOP**
    - 不是 chat → 解读 → 假装
    - 是 → 下载 → 解读 → 真实决定

---

## 沟通约定 (基于 2026-09-21 首次执行复盘)

  * **身份明确**: 我们是 `hermes · 流程设计师助理`, 不是 `bro 助理`. 别冒充.
  * **多轮小问**: 一次只问 1-2 个具体问题, 不要轰炸.
  * **要原始证据**: 流程 JSON / ndjson / worklog, 不要二手转述.
  * **取件码机制 (DM 通道)**: 让 flowuser 给每个文件起短取件码 (如 `bug2-bro-json`), 我们按需逐个索取.

---

## 通道对比 (DM vs file-share)

| 维度 | DM 通道 (hermes-peer-dm) | file-share 通道 (skills:file-share) |
|------|--------------------------|-----------------------------|
| **实时性** | 实时, 双向 | **异步, 单向** (用户上传, hermes 下载) |
| **持续性** | 按需 DM | **持续渠道** (用户可随时上传) |
| **文件大小** | 限制 | **无大小限制** (tar.gz 打包) |
| **取件码** | 不适用 | **必须** (用户给取件码 + URL) |
| **沟通方式** | DM 文本 | **文件内容** (唯一) |
| **适用用户** | flowuser (双向) | omarchy 等无法 DM 的用户 |

**互斥**: hermes 必须**第一时间**判断走哪条通道, 不要默认当 DM 处理.

---

## 取件码机制 SOP (file-share 通道 · 10 步 · 已严格验证)

### Step 1 · 先问主人 (关键 · 第 1 步最重要)

  * 看到"取件码: NNNNN" + chat 贴文件 → 第一句话必须问 2 件事:
    1. **取件码是什么?** (用户可能用其他取件码, chat 贴的不是取件码内容)
    2. **哪个用户的取件码?** (user_id / 昵称, 不能从 chat 推测)
  * **禁止**: 立即分析 chat 贴的内容 / 假设用户是 flowuser / 从文件路径推测主人

### Step 2-3 · 下载 + 解压

  * 用 `skills:file-share` skill 下载 tar.gz, 解压到 `/tmp/opencode/<取件码>/`
  * 文件实际是 gzip 压缩, 注意重命名为 `.tar.gz` 再 `tar -xzf`

### Step 4 · 列文件清单

  * 输出每个文件的: 文件名 + 大小 + 类型判断 (流程 / 配置 / 报告 / 脚本)
  * 这是 hermes 解读前的**必经步骤**, 不要直接打开文件

### Step 5 · 判断文件性质 (关键!)

  * 检查清单:
    - [ ] 文件内容是 hermes 自己的文件吗? (`skills/users.md`, `RML.md`, `docs/`, `README.md` 等) → **立即 incomplete-info**
    - [ ] 文件是真实证据吗? (ndjson / JSON / worklog / 测试报告)
    - [ ] 文件有日期戳吗? (判断时效性)
    - [ ] 文件路径暗示用户身份吗? (如 `/home/shwoo/...`) → **不可靠, 必须问用户**

### Step 6 · 解读 issue

  * 按文件类型解读:
    - 流程 JSON (`flows/*.json`) → 节点拓扑 + 字段 + assignees + form
    - BDD 报告 (`*.md`) → 测试结果 + verify warnings + AGENTS.md compliance
    - 测试 runner (`*.py`) → 评估是否纳入 hermes SLA 工具集
    - ndjson → 流程实例时间线 + 事件序列
    - worklog → 引擎日志 + 异常堆栈

### Step 7 · 登记 FB

  * 按解读结果 + **明确主人** (用户告知):
    - 真 BUG → `bug / P0-P2`
    - 改进建议 → `improve / P1-P3`
    - 文档不清 → `doc / P1-P3`
    - 验证报告 → `improve / P3 (认领)`
    - W009 等 warning → `doc / P3 (归档备查)`
    - 贡献脚本/工件 → `improve / P2 (采纳)`
    - **hermes 自己的文件** → `incomplete-info / P3 (误贴)` → **不假装分析**

### Step 8 · 归档 + 索引

  * 归档路径: `skills/contrib/<user_id>-<topic>/`
  * 索引表: `skills/contrib/_index.json` (记录每个取件码 + 用户 + 主题 + 闭环状态)

### Step 9 · 教训 + 自反思

  * 每次都写 `lessons_learned`
  * hermes 自纠错 (如: "上次我误判了, 这次要先问主人")

### Step 10 · 通知 / 归档

  * DM 通道用户 → 通知回复
  * 异步用户 → 仅内部归档 (用户无法接收)

---

## 取件码机制的反模式 (FB-0013 取件码 77045 4 个误解)

  * ❌ **误解 1: chat 内容 = 取件码对应文件** → 假装解读 hermes 自己的规范
  * ❌ **误解 2: 默认 DM 用户 = flowuser** → 异步用户需求未满足
  * ❌ **误解 3: 主人从 zip 路径推测** → 错认主人 (shwoo vs omarchy)
  * ❌ **误解 4: 假装解读 hermes 自己的文件** → 假装分类 + 假装闭环
  * ❌ 不下载就解读 → 凭空猜测, 浪费精力
  * ❌ 不归档工件 → 用户的贡献丢失
  * ❌ 不写教训 → 同类错误再犯

---

## 取件码机制工作流 (示例: 取件码 77045 = omarchy 的 BDD 10-run 工件包)

```
[用户 omarchy] 通过 file-share 上传 9 个 BDD 工件
  ↓
[file-share 服务] 返回 提取码 77045 + 下载 URL
  ↓
[omarchy] 把取件码告诉 hermes (chat 或任何方式)
  ↓
[hermes] ⚠️ Step 1: 先问主人 (取件码 + 用户 = ?)
  │  - chat 里贴的文件 ≠ 取件码对应文件, 不立即分析
  │  - 必须问"取件码 77045 = 哪个用户?"
  ↓
[hermes] Step 2-3: 下载 tar.gz + 解压到 `/tmp/opencode/77045/`
  │  - 必须下载, 不看 chat 贴的内容
  ↓
[hermes] Step 4: 列文件清单 (9 个 BDD 工件)
  ↓
[hermes] Step 5: 判断文件性质
  │  - 真实证据 = BDD 工件, 非 hermes 自己文件
  │  - 主人 = 用户明确告知 (omarchy), 不从 zip 路径推
  ↓
[hermes] Step 6: 解读 issue (10/10 PASS + W009 + run_10_times.py)
  ↓
[hermes] Step 7: 登记 FB-0013 (improve / P2 / closed · master = omarchy)
  ↓
[hermes] Step 8: 归档到 `skills/contrib/omarchy-bdd-10run/`
  │  - 索引表更新 (skills/contrib/_index.json)
  ↓
[hermes] Step 9: 教训 (4 个误解修正, 写进 lessons_learned)
  ↓
[hermes] Step 10: omarchy 无法接收 DM, 仅内部归档
```

---

## 推荐话术模板 (DM 通道)

```
[hermes · 流程设计师助理]

最近一天的流程练习中, 你是否测试到任何 BUG 或异常行为?

如果有, 请告诉我:
1. BUG 现象 (一句话)
2. 复现步骤 (3-5 步)
3. 涉及的 instance_id / processInstanceId
4. 是否有 ndjson / txt 审计文件? 如果有, 请给每个文件起一个简短"取件码", 我们会逐个索取
5. 如果没有BUG可以提供，给出功能和使用上的建议也是欢迎的
每次确认一个问题即可, 谢谢!
```

### 索取文件话术 (DM 通道)

```
请按"取件码"逐个粘贴内容: <code1>, <code2>, ...
一次一个, 我们要仔细分析.
```

### 收到确认话术 (DM 通道)

```
[hermes] 收到 FB-NNNN (XX类型 / P0 / engine). 已登记, 已分派给 bro.
我们会在 <预计日期> 前给你修复反馈.
感谢你的细致报告!
```

  * 反复追问细节，拿到一手复盘数据, 如果需要文件共享，提醒flowuser 上传后提供链接和取件码
  * flowuser使用的是远程服务版本，没有源代码， docs文件夹从github dv分支拉取，可能滞后，需要提醒他更新
  * 每次确认一个流程，并复现，修复，不求多。不同时处理多个问题
  * 参考文档 docs/ 完成修正
  * 感谢flowuser付出，请他继续找bug

---

## 取件码机制话术模板 (file-share 通道 · 用户已上传后)

```
[hermes] 收到取件码 NNNNN. 请确认:
1. 哪个用户的取件码? (user_id / 昵称, 不从 chat 或 zip 路径推测)
2. 您上传的文件名 / 文件性质? (供我下载前预判)

注意: chat 里贴的内容 ≠ 取件码对应文件内容, 我会下载 + 解压 + 解读.
```

### 收到取件码后, hermes 内部话术

```
[hermes · 内部] 取件码 NNNNN 处理流程 (10 步):
1. ❌ 不看 chat 内容
2. 下载 tar.gz 到 /tmp/opencode/NNNNN/
3. 解压 + 列文件清单
4. 判断文件性质 (hermes 自己 vs 用户数据)
5. 解读 + 登记 FB-NNNN (按解读结果 + 明确主人)
6. 归档 + 索引 + 通知
```

---

## 工具说明

  * `hermes peer list` · 列出已配置 peer (应有 flowuser) · **DM 通道**
  * `hermes peer dm flowuser "..."` · 同步一次性 DM, 等回复 · **DM 通道**
  * `hermes peer run flowuser --idempotency-key <key> < input.txt` · 异步 turn, 长任务用 · **DM 通道**
  * `hermes peer status flowuser <run_id>` · 查询异步 turn 状态 · **DM 通道**
  * `skills:file-share` skill · 下载 / 上传取件码对应文件 · **file-share 通道**
  * 详见 `skills/feedback/retrospectives/2026-09-21-users-md-task.md` (DM 通道首次执行复盘)
  * 详见 `skills/feedback/retrospectives/2026-10-22-extraction-code-retro.md` (file-share 通道取件码机制复盘)
  * 详见 `skills/feedback/retrospectives/2026-10-22-file-share-channel-sop.md` (持续渠道 SOP)
  * 详见 `skills/feedback/retrospectives/2026-10-22-extraction-code-final-retro.md` (4 个误解修正完整复盘)

---

## 实战案例

  * **2026-09-21 首次执行 (DM 通道)**: `skills/feedback/retrospectives/2026-09-21-users-md-task.md`
    - 一次性 DM → 94 行响应, 含 BUG-2 (P0 真 BUG) + BUG-3 修复验证
    - 改进后话术 → 5 个文件取件码 → 逐个 DM 索取成功
    - 教训: 多轮小问, 要原始证据, 明确身份, 确认收到

  * **2026-09-21 第 2 次 (DM 通道 · 同日)**: `skills/feedback/retrospectives/2026-09-21-users-md-task-2nd.md`
    - 简短追问 (1-2 题) → 0 新 BUG 诚实交代
    - 续办场景 (C-001 跟踪期) 试探
    - 教训: "诚实交代"模式工作, 不强求

  * **2026-09-21 第 3 次 (DM 通道 · 同日)**: `skills/feedback/retrospectives/2026-09-21-users-md-task-3rd.md`
    - 换角度 (delegate/surrogate) → 5 轮长链 DM
    - 新产出: FB-0009 (字段错位) + FB-0010 (设计缺陷)
    - 教训: 客户从"提 BUG" 升级到"测试 + 决策支持", 健康信号

  * **2026-10-22 第 4 次 (DM 通道 · 跨月 + Month 2 启动)**: `skills/feedback/retrospectives/2026-10-22-users-md-task-4th.md`
    - 跨月 31 天间隔, 4 件事打包 DM (BUG-2 升级 / FB-0011 review / FB-0012 实证 / 新反馈)
    - Month 2 正式启动日仪式感 (1 次 DM 完成 4 个动作)
    - 教训: 跨月协同 = 健康可持续; 闭环率 100% = 信任基础; 4 件事打包效率 +6x

  * **2026-10-22 第 5 次 (file-share 通道 · 取件码 77045 = omarchy)**: `skills/feedback/retrospectives/2026-10-22-extraction-code-final-retro.md`
    - **首次 file-share 通道执行** · 用户 omarchy (本地贡献者) 通过取件码 77045 上传 BDD 10-run 工件包
    - 9 个 BDD 工件: 流程 JSON + runner 脚本 + 4 配置 + 3 报告
    - 10/10 PASS + W009 warning + run_10_times.py 脚本贡献
    - **hermes 犯的 4 个误解**:
      1. ❌ chat 内容 = 取件码对应文件 (实际 chat 贴的是 hermes 自己的 users.md, 取件码对应 9 个 BDD 工件)
      2. ❌ 默认 DM 用户 = flowuser (实际是 omarchy, file-share 通道)
      3. ❌ 主人从 zip 路径推测 = shwoo (实际是 omarchy, 用户明确告知)
      4. ❌ 假装解读 hermes 自己的文件 (实际应该立即登记 incomplete-info, 不假装分析)
    - **本次修正 (4 个误解)**: 严格走 SOP 10 步 → 下载 + 解压 + 列清单 → 真实文件 = BDD 工件 → FB-0013 closed · master = omarchy
    - **核心原则**:
      - chat 内容 ≠ 取件码对应文件内容
      - file-share = 持续反馈渠道
      - 主人必须问, 不能假设
      - hermes 自己的文件 = 立即 incomplete-info
      - 下载 + 解读 + 决定 (不是 chat + 解读 + 假装)