# 用户指南 01 · 快速开始

> **来源**：https://jeeflow-doc.mldong.com/guides/01-quick-start
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的设计视角快速入口。
> **裁剪记录**：§1 环境要求、§2 一键体验（演示站 + 5 语言启动 + 前端 jeeflow-ui）整段裁剪；§3 保留 API 主体并加本仓对齐注解；§4 / §5 原文保留；§6 链接保留原状待后续核对。

---

## 3. 方式二：直接调 API

> **本仓对齐注解**（与上游 jeeflow 的差异）：
> - **端口**：上游文档默认 `8100`（Python 后端），本仓 jeeFlow 监听 `8101`（内存）或 `8102`（PG）。请将下述示例的端口替换为本仓端口。
> - **action 路径**：上游写 `processDefine/startAndExecute`，本仓 38 个 action 中**对应入口是 `processInstance/startAndExecute`**（详见 `../docs/api.md` §1）。
> - **语义**：operator / submitType / processTaskId 字段名与本仓一致，跨后端可直接照搬。

不启动前端，用 curl 走完一个流程：

```bash
# 1. 发起（自动完成申请节点）
curl -X POST http://localhost:8101/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d '{"processDefineId":1,"operator":"user1"}'
# → {"code":0,"msg":"成功","data":null}

# 2. 组长查待办
curl -X POST http://localhost:8101/wf/processTask/todoList \
  -H "Content-Type: application/json" -d '{"operator":"leader"}'  # 门面契约统一 operator
# → rows[0].id 即任务ID

# 3. 组长同意
curl -X POST http://localhost:8101/wf/processTask/execute \
  -H "Content-Type: application/json" \
  -d '{"processTaskId":"<taskId>","operator":"leader","submitType":1}'
# → {"code":0,"msg":"成功","data":null}

# 4. 查看实例状态
curl -X POST http://localhost:8101/wf/processInstance/detail \
  -H "Content-Type: application/json" -d '{"id":"<instanceId>"}'
```

---

## 4. 试试驳回闭环（核心流程）

```
user1 发起 → leader 同意 → manager 点"退回"（submitType=6）
  → 第一个任务节点重新执行并强制指派给发起人 → user1 收到新待办
user1 重新提交（submitType=0）
  → leader 再次收到审批
leader 同意 → 流程完成
```

> 与 mldong 框架一致：`submitType=2`（拒绝）会跳结束（实例→45）；`submitType=6`（退回发起人）保留实例进行中并给发起人建新待办。全枚举见[统一门面接口文档 §2.8](./../spec/06-facade)。

这就是 jeeflow 的核心业务闭环：**发起 → 审批 → 退回发起人 → 重新提交 → 完成**。底层机制见[设计原理 06](./../concepts/06-contracts)。

---

## 5. 14 个示例流程

| # | 流程 | 演示点 |
|---|---|---|
| 1 | 简单审批 | 基础单级审批 |
| 2 | 多级审批 | 三级串行（组长→经理→总监）|
| 3 | 决策表达式 | amount 变量路由（>1000 经理 / ≤1000 总监）|
| 4 | 并行分支合并 | fork→join |
| 5 | 并行会签 | 3 人并行 |
| 6 | 串行会签 | 2 人依次 |
| 7 | 按比例会签 | 4 人并行（阈值完成，#nrOfCompletedInstances 表达式）|
| 8 | 串行会签-审批 | 串行会签（按同意推进）|
| 9 | 自定义节点 | customClass 处理器 |
| 10 | 含驳回流程 | 两级审批 + 驳回退回 |
| 11 | 混合模式 | fork+join+decision+会签组合 |
| 12 | assignee 变量解析 | assignee 取流程变量（字面量回退）|
| 13 | 参与者解析（内置 handler）| assignment handler 动态取人 |
| 14 | 候选人双源 | candidatePage 候选（用户/角色）|

---

## 6. 下一步

> **链接状态**：以下链接保留原状，待所有用户指南归档完成后集中核对是否已在本仓 `ToT/` 对应位置定义。

- 学流程定义怎么写 → [02-流程定义](./02-flow-definition)
- 学后端 API（40+ 个 action 参数/返回/契约）→ [统一门面接口文档](./../spec/06-facade)
- 学写扩展（自定义参与者/决策器/拦截器）→ [04-扩展开发](./04-extensions)