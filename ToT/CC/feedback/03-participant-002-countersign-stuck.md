# Feedback: 002 - 会签任务第 2 个人卡了 3 天没人动

> **Persona**: 03
> **Date**: 2026-09-25
> **Reporter**: 销售部小李 (user1)
> **Severity**: P1

## 现象（What happened）

我发起的合同审批流程，3 个部门会签。第 1 个领导 30 分钟批了，
第 2 个领导（采购部经理）3 天了还没动。整个流程卡住。

## 影响（Impact）

- 合同签不下来，业务受阻
- 客户已经在催
- 整个公司同时有 5 个类似的卡住会签

## 期望（What we want）

- 想找「能加签给副手」的功能，但 03 FAQ 里没找到
- 想看「会签任务能不能中途修改审批人」，不知道行不行
- 想看 03 decision-tree，加签/委派分支不全

## 已尝试（What I tried）

- IM 找采购部经理，对方在休假
- 找 IT 问「能加签吗」，回复说「等领导回来」
- 自己不知道该怎么办

## 证据（Evidence）

- 我的 processInstanceId = 1050
- 流程定义 ID = 100（合同审批）
- 节点配置：`countersignType=PARALLEL`
- 卡在 task 5678（采购部经理）

## 标签（Tags）

`design-issue`
## 闭环
**Closed at**: 2026-09-25
详见 `_routes/` 对应条目

**状态**: 已闭环 ✅
