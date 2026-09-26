# Feedback: 003 - 大量抄送导致 healthz 卡 5 秒

> **Persona**: 03
> **Date**: 2026-09-25
> **Reporter**: HR 张 (hr1)
> **Severity**: P0

## 现象（What happened）

今天 10:00 整点发布了一条「全员体检通知」流程，抄送给 500 人。
结果 `/healthz` 端点响应从 50ms 飙升到 5 秒。
期间所有 API 都变慢。

## 影响（Impact）

- 整个公司 jeeFlow 不可用 5-10 分钟
- 业务部门发起的所有审批全部卡住
- 我们是 10:00 整点发的，恰好是全员上线高峰

## 期望（What we want）

- 抄送应该是异步的，不应该阻塞 API
- 或者有批量背压机制
- 监控应该有「抄送队列长度」指标

## 已尝试（What I tried）

- 重试几次 `/healthz` 越来越慢
- 看 `/api/admin/health` → pg pool idle 0
- 联系陈 DBA 后做了紧急清理

## 证据（Evidence）

- processInstanceId = 1100
- 抄送节点：cc_all_500
- 时间窗口：10:00-10:10
- `/api/admin/health` 显示 `pg.idle=0` 持续 8 分钟

## 标签（Tags）

`system-perf`
## 闭环
**Closed at**: 2026-09-25
详见 `_routes/` 对应条目

**状态**: 已闭环 ✅
