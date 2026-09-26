# Feedback: 001 - delegate 后 task 表 delegatedTo 字段未写

> **Persona**: 03
> **Date**: 2026-09-25
> **Reporter**: 王组长 (leader1)
> **Severity**: P1

## 现象（What happened）

我委派 task 12345 给副组长赵 (leader2)，但事后查 task 表发现 `delegatedTo` 字段还是 NULL。
后续 `delegateHistory` 也没正确写入 targetUserId。

## 影响（Impact）

- 历史追溯断链（审计看不到谁委派给谁）
- KPI 5 委派率统计不到这条
- 不知道是不是个例还是普遍 bug

## 期望（What we want）

委派后 `processTask.delegatedTo` 字段应该立即写入 targetUserId
并且 `delegateHistory` 能正确反映

## 已尝试（What I tried）

```bash
# 1. 委派
curl -sX POST .../wf/processTask/delegate -d '{
  "processTaskId":12345, "operator":"leader1", "targetUserId":"leader2"
}' | jq

# 2. 查 history
curl -sX POST .../wf/processTask/delegateHistory -d '{
  "processTaskId":12345
}' | jq
# → 返回空数组
```

## 证据（Evidence）

- `vendor/jeeflow/facade.py:1992 _processTask_delegate` 实现
- `vendor/jeeflow/facade.py:2036 _processTask_delegateHistory` 实现
- 没有找到写 `delegatedTo` 字段的代码

## 标签（Tags）

`bug`
## 闭环
**Closed at**: 2026-09-25
详见 `_routes/` 对应条目

**状态**: 已闭环 ✅
