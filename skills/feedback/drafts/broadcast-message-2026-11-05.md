# hermes 广播消息 · 2026-11-05 (W46 Day 3) · 邀请新反馈

> **通道**: broadcast.py (broadcast skill)
> **项目ID**: `jeeflow` (从工作目录名)
> **目的**: 邀请所有用户 (flowuser, omarchy, 新用户) 提供新反馈
> **状态**: 🟡 草稿就绪, 待 hermes 实际执行 broadcast.py

---

## 1. 广播消息正文

```
[项目ID: jeeflow] hermes 邀请新反馈 · Phase 9 Month 2

【状态报告】
- Phase 9 Month 1 已收官 (健康度 91/100)
- 14 FB 累计, 闭环率 12/12 = 100%
- 修复总数 9 (含 FIX-T112, FIX-T113)
- SLA 评分 100/100, 固化脚本 32/32 PASS
- FAQ v1.0 published (22 题)
- Q3 季度复盘 + Month 1 收官 published v1.0

【新流程模式】
- auto-assignee-by-org 方案 v0.2 (Month 2 Week 1-2 实施中)
- top-N 客户反馈驱动流程模式 v0.1 (Month 2 Week 4)
- W014 verify 规则 (omarchy 贡献) 已纳入 SLA 工具集

【邀请反馈 · 4 件事】
1. 任何 BUG / 异常行为 → 回复或上传文件 (DM 或 file-share 取件码)
2. 任何文档不清 / UX 困惑 → 告诉 hermes
3. 任何流程模式建议 → 贡献思路
4. 任何流程实例数据 → 贴 ndjson + instance_id

【反馈方式】
- DM 通道 (flowuser): 用 hermes-peer-dm 联系我
- file-share 通道 (omarchy + 其他): 上传文件 + 给我取件码
- 取件码 SOP: hermes 已严格走 10 步 (下载+解压+解读+决定)

【优先级】
- P0 真引擎 BUG → 立即处理
- P1 改进 / 重要修复 → 高优 (≤ 7 天)
- P2 文档 / UX → 中 (≤ 14 天)
- P3 一般建议 → 低 (月度节奏)

【承诺】
- 24h 内确认收到
- 7 天内给修复反馈 (P0/P1)
- 14 天内给修复回复 (P2)
- 客户沉默 14 天 → hermes 主动询问
- 闭环率目标 100%

期待您的新反馈, hermes 持续工作中.
```

---

## 2. 执行命令

```bash
python /opt/jupyter/src/RD/config/UX/skills/broadcast/scripts/broadcast.py '{"topic": "jeeflow", "message": "[项目ID: jeeflow] hermes 邀请新反馈 · Phase 9 Month 2\n\n【状态报告】\n- Phase 9 Month 1 已收官 (健康度 91/100)\n- 14 FB 累计, 闭环率 12/12 = 100%\n- 修复总数 9 (含 FIX-T112, FIX-T113)\n- SLA 评分 100/100, 固化脚本 32/32 PASS\n- FAQ v1.0 published (22 题)\n\n【新流程模式】\n- auto-assignee-by-org 方案 v0.2 (Month 2 Week 1-2 实施中)\n- top-N 客户反馈驱动流程模式 v0.1 (Month 2 Week 4)\n- W014 verify 规则 (omarchy 贡献) 已纳入 SLA 工具集\n\n【邀请反馈 · 4 件事】\n1. 任何 BUG / 异常行为 → 回复或上传文件 (DM 或 file-share 取件码)\n2. 任何文档不清 / UX 困惑 → 告诉 hermes\n3. 任何流程模式建议 → 贡献思路\n4. 任何流程实例数据 → 贴 ndjson + instance_id\n\n【反馈方式】\n- DM 通道 (flowuser): 用 hermes-peer-dm 联系我\n- file-share 通道 (omarchy + 其他): 上传文件 + 给我取件码\n- 取件码 SOP: hermes 已严格走 10 步 (下载+解压+解读+决定)\n\n【优先级】\n- P0 真引擎 BUG → 立即处理\n- P1 改进 / 重要修复 → 高优 (≤ 7 天)\n- P2 文档 / UX → 中 (≤ 14 天)\n- P3 一般建议 → 低 (月度节奏)\n\n【承诺】\n- 24h 内确认收到\n- 7 天内给修复反馈 (P0/P1)\n- 14 天内给修复回复 (P2)\n- 客户沉默 14 天 → hermes 主动询问\n- 闭环率目标 100%\n\n期待您的新反馈, hermes 持续工作中."}'
```

---

## 3. 关联文档

- `skills/users.md §取件码机制 SOP 10 步`
- `skills/feedback/FAQ.md Q5.4 取件码流程`
- `skills/roadmap/phase9-90day-plan.md` Phase 9 详细计划
- `skills/feedback/drafts/draft-to-flowuser-2026-11-04.md` flowuser 单独 DM 草稿

---

⏱️ Last updated: 2026-11-05 (W46 Day 3) · 广播消息草稿 v1.0