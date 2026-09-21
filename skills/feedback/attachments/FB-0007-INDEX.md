# FB-0007 附件清单 · 2026-09-21

> **来源**: flowuser 通过 hermes peer dm 提供
> **目的**: BUG-2 复现 + 审计证据 + 根因分析
> **状态**: 文件已接收 (取件码 → DM 复制粘贴)

---

## 附件清单

| # | 取件码 | 原始路径 (flowuser 端) | 大小 | 接收状态 |
|---|--------|-----------------------|------|----------|
| 1 | `bug2-bro-json` | `tdd/bug2_bro_exact_repro.json` | ~3KB | ✅ 内容已 DM 接收 (2026-09-21) |
| 2 | `bug2-worklog` | `work_logs/08_bug2_repro.md` | ~5KB | ✅ 内容已 DM 接收 (2026-09-21) |
| 3 | `ndjson-232-mgr` | `audit_logs/232_92099018922273.ndjson` | 12.6KB | 🟡 路径已知, 内容按需取 |
| 4 | `ndjson-232-dir` | `audit_logs/232_92099066975525.ndjson` | 12.2KB | 🟡 路径已知, 内容按需取 |
| 5 | `ndjson-232-happy` | `audit_logs/232_92099077616937.ndjson` | 13.7KB | 🟡 路径已知, 内容按需取 |

---

## 关键事实 (来自 worklog + DM)

### 流程结构 (来自取件码 bug2-bro-json)

```
apply → decision_amount (按金额分流)
         ├─ <5000 → mgr_approve → decision_mgr
         │                          ├─ tf_mgr_decision==1 → cashier_pay
         │                          └─ tf_mgr_decision==2 → end_no  ← REJECT 路径
         └─ ≥5000 → dir_approve → decision_dir
                                    ├─ tf_dir_decision==1 → cashier_pay
                                    └─ tf_dir_decision==2 → end_no  ← REJECT 路径
```

### 实例数据

| 实例 | amount | 分支 | mgr/dir decision | 期望 instance state | 实际 | cashier_pay DOING? |
|------|--------|------|-----------------|---------------------|------|---------------------|
| 92099018922273 | 4800 | mgr | reject (2) | 45 REJECTED | **10 ❌** | **DOING ❌ BUG-2!** |
| 92099066975525 | 8000 | dir | reject (2) | 45 REJECTED | **10 ❌** | **DOING ❌ BUG-2!** |
| 92099077616937 | 999 | mgr | approve (1) | 20 DONE | 20 ✅ | DONE ✅ |

**3/3 触发**: reject 路径 BUG-2 必现, happy path 正常.

### 根因猜测 (来自 worklog)

`vendor/jeeflow/engine.py:_evaluate_decision` 遍历出边时**没有短路**,
即使第一条 expr=true, 仍继续评估后续出边.

类似 BUG-1 根因 (`engine.py:210 _follow_edges`), 但发生在 decision 节点而非 task 节点.

---

## 下一步

### 立即 (今天)
- [x] 接收文件 (取件码机制验证成功)
- [x] 写入 FB-0007
- [ ] 给 flowuser "收到确认 + 正在处理" 反馈

### 本周 (bro)
- [ ] 用本附件的 bug2_bro_exact_repro.json 在本地复现
- [ ] 定位根因 (验证 worklog 猜测)
- [ ] 起草 FIX-T112
- [ ] 修复 + BDD + 验证
- [ ] 通知 flowuser 闭环

### 改进 (本周)
- [ ] users.md 加入"取件码" 机制说明
- [ ] FEEDBACK.md §3.1 加入"附件索取" 步骤
- [ ] feedback/attachments/ 目录结构标准化

⏱️ Last updated: 2026-09-21
