# Route: 04-ops-audit ← 03-participant-003-bulk-cc-perf.md

> **From**: 03 · 2026-09-25 · HR 张 (hr1)
> **Severity**: P0
> **Tags**: system-perf
> **Routed at**: 2026-09-25T03:47:56.425343+00:00

## 来源反馈

**大量抄送导致 healthz 卡 5 秒**

今天 10:00 整点发布了一条「全员体检通知」流程，抄送给 500 人。
结果 `/healthz` 端点响应从 50ms 飙升到 5 秒。
期间所有 API 都变慢。



## 行动（待 plan owner 填写）

- [ ] 接收并确认
- [ ] 排期 / 优先级
- [ ] 修复 / 加 doc
- [ ] 闭环：回写 `feedback/03-participant-003-bulk-cc-perf.md` 加 `状态: 已闭环`
- [ ] release + 同步到 03-participant.md FAQ

## 状态

**状态**: open
