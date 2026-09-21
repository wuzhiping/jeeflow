# File-share 持续反馈渠道 SOP · 2026-10-22 (取件码 77045 复盘)

> **来源**: FB-0013 (omarchy 取件码 77045)
> **状态**: ✅ published v1.0 (持续渠道 SOP)
> **关键洞察**: chat 里贴的内容 ≠ 取件码对应文件内容, **必须下载取件码才能解读**

---

## 1. File-share = 持续反馈渠道 (不是一次性)

### 1.1 与 DM 通道对比

| 维度 | DM 通道 (hermes-peer-dm) | file-share 通道 (skills:file-share) |
|------|--------------------------|-----------------------------|
| **实时性** | 实时, 双向 | **异步, 单向** (用户上传, hermes 下载) |
| **持续性** | 按需 DM | **持续渠道** (用户可随时上传新文件) |
| **文件大小** | 限制 | **无大小限制** (tar.gz 打包) |
| **取件码** | 不适用 | **必须** (用户给取件码 + URL) |
| **沟通方式** | DM 文本 | **文件内容** (唯一) |
| **适用用户** | flowuser (双向) | omarchy 等无法 DM 的用户 |

### 1.2 持续渠道的核心原则

```
1. chat 里贴的内容 ≠ 取件码对应的文件内容
2. 必须先下载取件码对应文件, 才能解读内容
3. 用户用取件码 = 唯一反馈入口, 不需要 DM
4. hermes 应该持续监控取件码 (用户可能多次上传)
5. 每次上传 = 1 个新 FB (按内容解读)
```

---

## 2. 完整工作流 (10 步)

```
[用户] 通过 file-share 上传文件
  ↓
[file-share 服务] 返回 提取码 (取件码) + 下载 URL
  ↓
[用户] 把取件码告诉 hermes (chat 或任何方式)
  ↓
[hermes] Step 1: 先问主人 (哪个用户的取件码?)
  ↓
[用户] 回答: omarchy (或其他 user_id)
  ↓
[hermes] Step 2-3: 用取件码 + URL 下载 tar.gz, 解压到 /tmp/opencode/<取件码>/
  ↓
[hermes] Step 4: 列文件清单 (文件名 + 大小 + 类型判断)
  ↓
[hermes] Step 5: 判断文件性质
  ├─ hermes 自己的文件? → incomplete-info
  ├─ 真实证据? → 严格按文件分析
  └─ 混合? → 仅处理用户数据部分
  ↓
[hermes] Step 6: 解读 issue (按文件类型)
  ↓
[hermes] Step 7: 登记 FB-NNNN (按解读结果)
  ↓
[hermes] Step 8: 归档工件 + 更新索引 (skills/contrib/_index.json)
  ↓
[hermes] Step 9: 写 lessons_learned + hermes 自反思
  ↓
[hermes] Step 10: 通知用户 (DM 通道, 如有) 或 仅内部归档 (异步用户)
```

---

## 3. 取件码处理决策矩阵

### 3.1 第一步 (必须): 区分 chat 内容 vs 取件码内容

| 来源 | 内容 | 处理 |
|------|------|------|
| **chat 贴** | 任何文件 | **仅供参考** (可能是 hermes 自己的规范, 误贴, 测试) |
| **取件码 77045** | tar.gz 文件 | **必须下载 + 解读** (唯一真实反馈) |

**关键**: hermes 看到 chat 里贴文件时, 必须先问"这是您上传的吗? 取件码是什么?", 再下载.

### 3.2 第二步 (按内容分类)

| 内容类型 | hermes 操作 |
|----------|-----------|
| **hermes 自己的文件** (users.md, RML.md, docs/) | 登记 incomplete-info, 不假装分析 |
| **真实证据** (流程 JSON / ndjson / 测试报告 / 脚本) | 严格按文件分析, 解读 issue |
| **贡献脚本 / 工件** | 评估是否纳入 hermes 工具集 |
| **W009 等 warning** | 列入 docs/known-issues.md 候选 |
| **混合** (hermes 自己的 + 用户数据) | 仅处理用户数据部分 |

---

## 4. 持续监控 SOP (file-share 用户)

### 4.1 监控频率

| 用户类型 | 监控频率 |
|----------|----------|
| **L1** (1 次 file-share) | 不主动监控, 等用户上传 |
| **L2** (2+ 次 file-share) | 每周 1 次检查新取件码 |
| **L3** (3+ 次 file-share + 主动贡献) | 每天 1 次检查新取件码 |

### 4.2 索引表 (skills/contrib/_index.json)

```json
{
  "users": [
    {
      "user_id": "C-omarchy",
      "first_seen": "2026-10-22",
      "level": "L3",
      "extraction_codes": ["77045"],
      "fb_archived": ["FB-0013"],
      "monitoring_frequency": "daily"
    }
  ]
}
```

---

## 5. 反模式 (持续渠道)

| 反模式 | 后果 | 改进 |
|--------|------|------|
| ❌ **看到 chat 贴文件 → 假装解读** | 错认主 + 假装闭环 | 先下载取件码, 再解读 |
| ❌ **默认当 DM 用户处理** | 异步用户需求未满足 | 区分 DM vs file-share |
| ❌ **看到 hermes 自己的文件假装分析** | 推导出错误的"用户意图" | 立即登记 incomplete-info |
| ❌ **用错取件码下载** | 把别人的文件当用户的贡献 | 下载后核对内容 vs 用户告知 |
| ❌ **不维护索引表** | 取件码来源不可追溯 | 每次登记后更新 _index.json |
| ❌ **不持续监控** | 错过新上传 | 按用户等级定期检查 |

---

## 6. 本次案例 (omarchy + 取件码 77045) 的 SOP 应用

### 6.1 hermes 之前犯的错

| 时间 | hermes 行为 | 错误 |
|------|--------------|------|
| T0 | 看到 chat 贴 `skills/users.md` | ❌ 立即分析, 假设 = flowuser |
| T0+5min | 误判为 flowuser | ❌ 默认 DM 通道 |
| T0+15min | 用户澄清: 不是 flowuser, 是 async 用户 | 修正路径 |
| T0+45min | 下载取件码 77045 → 9 个 BDD 文件 | ✅ 正确下载 |
| T0+50min | 解读 BDD 工件 | ✅ 正确解读 |
| T0+60min | 假设主人 = shwoo | ❌ **用错主** (用户从未说 shwoo) |
| T0+75min | 用户告知: 77045 from omarchy | 修正主人 |
| T0+90min | 重写 FB-0013 master = omarchy | ✅ 修正完成 |

### 6.2 改进后的 SOP (本次应用)

1. ✅ chat 贴 `skills/users.md` → 不立即分析, 先问主人
2. ✅ 用户告知 omarchy → Step 5 判断文件 = hermes 自己规范 → incomplete-info
3. ✅ 用户反馈: 必须下载取件码 → 重新下载 77045 → 9 个 BDD 文件 (真实内容)
4. ✅ 解读 BDD 工件 → 10/10 PASS + W009 + run_10_times.py
5. ✅ 重写 FB-0013 master = omarchy (纠正之前 shwoo 误判)
6. ✅ 归档到 `skills/contrib/omarchy-bdd-10run/` (从 shwoo 重命名)
7. ✅ 删除 FB-0014 (不需要, 因为 FB-0013 已闭环)

---

## 7. 关键决策表

| 场景 | hermes 应该做的 |
|------|-----------------|
| **chat 贴文件, 没取件码** | 问"取件码是什么?" + 不假装分析 |
| **chat 贴文件 + 取件码** | 先下载取件码, 不看 chat 贴的 |
| **取件码主人未知** | 立即问"哪个用户的取件码?" |
| **取件码主人在索引表** | 按用户等级监控 (L1/L2/L3) |
| **下载的文件 ≠ chat 贴的** | 以下载文件为准, chat 内容忽略 |
| **hermes 自己的文件被贴** | 立即登记 incomplete-info, 不假装分析 |
| **真实证据** | 严格按文件分析, 解读 issue |
| **W009 warning** | 列入 docs/known-issues.md 候选 |

---

## 8. 关键修正 (这次的关键)

### 8.1 chat 内容 vs 取件码内容

| 之前的 hermes 行为 | 现在的 hermes 行为 |
|---------------------|---------------------|
| 看到 chat 贴 `skills/users.md` → 假装解读 | **忽略 chat 贴, 直接下载取件码** |
| 假设 chat 贴的就是用户上传 | **下载后才能确认** |
| chat 内容 = 用户意图 | **取件码内容 = 用户意图** |

### 8.2 主人识别

| 之前的 hermes 行为 | 现在的 hermes 行为 |
|---------------------|---------------------|
| 假设主人 = flowuser (默认 DM) | **必须问"哪个用户的取件码?"** |
| 假设主人 = shwoo (来自 zip 路径) | **必须用户明确告知** |
| 主人 = 文件路径暗示 (`/home/shwoo/`) | **不可靠, 必须问** |

### 8.3 内容解读

| 之前的 hermes 行为 | 现在的 hermes 行为 |
|---------------------|---------------------|
| 假装解读 hermes 自己的文件 | **不假装, 立即登记 incomplete-info** |
| 推导出错误的"用户意图" | **只解读真实证据** |
| 闭环 = hermes 假装完成 | **闭环 = hermes 真的完成任务** |

---

## 9. 索引表 (示例 · 本次更新后)

```json
{
  "users": [
    {
      "user_id": "C-omarchy",
      "first_seen": "2026-10-22",
      "last_seen": "2026-10-22",
      "level": "L3",
      "extraction_codes": ["77045"],
      "fb_archived": ["FB-0013"],
      "monitoring_frequency": "daily",
      "note": "主动贡献 10-run BDD 工件, run_10_times.py 脚本"
    }
  ]
}
```

---

## 10. 未来扩展 (Month 2 Week 4+)

- W45 Day 2: 评估 run_10_times.py 纳入 hermes SLA 工具集
- W46 Day 1: 起草 docs/known-issues.md §117 (W009)
- W47 Day 1: 起草取件码监控工具 (hermes file-share check)

---

⏱️ Last updated: 2026-10-22 · file-share 持续渠道 SOP v1.0 published