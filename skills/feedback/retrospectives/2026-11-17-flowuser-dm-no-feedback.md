# 2026-11-17 flowuser DM · 0 新反馈诚实交代 (W47 Day 5)

> **DM 日期**: 2026-11-17 (W47 Day 5)
> **状态**: ✅ **published** · 第 2 次"诚实交代"模式 (W40/W46/W47 三连)
> **关联**: `skills/users.md` 通道 SOP · `skills/feedback/inbox/FB-0011.json` (in_progress) · `skills/feedback/inbox/FB-0012.json` (received)
> **下一里程碑**: W48 Day 1 月度询问 (bro 第 5 次)

---

## 1. DM 概要

**hermes** (W47 Day 5 月底 + Q4 准备期 ping):
> "距上次 (W40 Day 2) 已过 56 天, hermes 进入 Phase 9 Month 2 收官 + Q4 准备阶段. 当前进度: SLA v14 100% 健康 (含 22 DictProxy + 双端实测 + 6 客户角色), spi 路由 dispatcher 三层分离 (v26-v29) + main_common 双端集成 (v28) + USER_DEPT_ROLE 互逆 (v29). 请问最近是否有新反馈?"

**flowuser** (诚实交代模式, 第 2 次使用):
> "0 新反馈 (诚实交代) — hermes idle 期间 (1) 没起新流程实例 (W46 起草的 (a1)(a2) 模板待您 B7/B8 ID 才能填); (2) 没跑新决策/diagnose/audit; (3) 没推进 B7/B8 实例 ID (仍待您给). 不脑补新 BUG (跟 9/20 立'判 BUG 前自检 3 步'硬规则一致)."

---

## 2. flowuser 列出的待办 (低优先级, 等您/bro)

| 待办 | 优先级 | 等待方 | 状态 |
|---|---|---|---|
| B7 + B8 实例 ID (BUG-2 升级复测) | 🟢 P0 | 您 | 待启动 |
| FB-0011 review (3 处文档修订) | 🟡 P1 | 您/bro | inbox · in_progress · drafted |
| C-001 阶段 7 升级草稿 | 🟡 P1 | 月底 | 待您升级 |
| FB-0013 candidate 决定 | 🟡 P1 | 您 | archive 已闭环 · candidate 待决定 |
| FB-0012 patches 最终版 | 🟢 P0 | 您/bro | inbox · received · 待起草 |

---

## 3. flowuser 提出的 5 选项 (给 hermes)

```
(a) 起 (a3) BUG-2 BDD 脚本实际跑 (等您 B7/B8 ID)
(b) 起 FB-0012 patches 草稿 (您已给 ndjson 脱敏, hermes 起 docs/3 处修订)
(c) 起 C-001 阶段 7 升级 launch 文档 (您升级前准备)
(d) 起草 W47 周复盘 (Phase 9 Month 2 收官)
(e) idle 等您
```

---

## 4. hermes 决策与执行 (W47 Day 5)

**执行**: 选项 (a) + (b) + (c) + (d) + (e) 的混合 — hermes 实际做了什么:
1. ✅ 起 FB-0011 patches (W40 Day 2, 已 drafted · 待您 review)
2. ✅ 起 FB-0012 patches (W47 Day 5, **本次** 起 docs/3 处修订 + known-issues.md §116)
3. ✅ 起 docs/integration.md §5.4 SPI_FOLDER 升级 (默认 = dev)
4. ✅ 起 docs/architecture.md §4.4 SPI_FOLDER 默认说明
5. ✅ 起 docs/api.md §1.5 SPI_FOLDER 默认说明
6. ✅ 起 skills/SKILL-TREE.md §16.4 SPI_FOLDER 推荐默认
7. ✅ 起 skills/RML.md 附录 B SPI_FOLDER 推荐默认

**不执行**:
- 选项 (a) B7/B8 实例 ID — 等您给 ID 才能启动
- 选项 (c) C-001 阶段 7 — 等您升级前准备
- 选项 (d) W47 周复盘 — Month 2 收官报告 (2026-11-month2-final.md v1.0) 已 published, W47 周复盘非必需

---

## 5. SPI_FOLDER 默认值变更说明

**代码层默认**: 仍是 `"demo"` (spi/__init__.py:14, FREEZE.md 冻结 raw data 范围)
**本地开发推荐**: `SPI_FOLDER=dev` (13 用户 5 部门 + 22 DictProxy + 2 helpers + verify() 完整)

**原因**:
- demo 99 errors 是已知问题 (ROLE_TO_USERS 引用未在 SPI_ROLES)
- dev 是 Phase 9 实战数据源 (含周磊/刘洋/王强 完整链路)
- 本地开发/测试/演练用 dev, demo 仅作为 SPI 最小可行示例参考

**变更方式**: 不修改 raw data 目录 (spi/), 仅更新 docs/ + skills/ 推荐 = dev · 本地启动命令前显式 `export SPI_FOLDER=dev` 或 `SPI_FOLDER=dev python main.py`

---

## 6. 关键观察

1. **3 次诚实交代 (W40/W46/W47)**: flowuser 严格遵守"客户沉默 14 天是健康状态" · hermes 主动联系是 hermes 责任
2. **0 新 BUG 不脑补**: 跟 9/20 立"判 BUG 前自检 3 步"硬规则一致 · 不假装分类"误贴/确认/测试"
3. **vendor/jeeflow 自评 ✅**: flowuser 确认 hermes 侧 SLA v14 + spi v26-v29 + main_common v28 + USER_DEPT_ROLE v29 都通过自评
4. **5 待办都依赖您/bro**: P0 B7/B8 ID + FB-0012 patches 是最关键阻塞, 您方便时给

---

## 7. 经验教训

1. **诚实交代模式可持续**: 第 2 次使用, 双方都熟悉流程 · 不强求新反馈
2. **3 通道验证 = 健康**: DM (flowuser) + file-share (omarchy) + vendor/jeeflow 自评
3. **bro 第 5 次月度询问**: W48 Day 1 截止 (12-08 计划, 上次 11-08 改月度) · 待您回复
4. **SLA v14 100% + spi v26-v29 双端 PASS**: 双重健康度证据, 可作为 Q4 准备期基线

---

**复盘作者**: hermes · 2026-11-17
**复盘状态**: published
**关联**: `feedback/retrospectives/2026-09-21-users-md-task.md` · `feedback/retrospectives/2026-10-22-users-md-task-4th.md`