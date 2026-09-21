# TDD FIX-T6: vendor/jeeflow/facade.py 上游实现 RE_APPLY 路由

- **时间**：2026-09-17 16:00:00
- **修复位置**：`vendor/jeeflow/facade.py:312`（新增分支）
- **去掉补丁**：main.py + main_pg.py `_reapply_flow` monkey patch
- **服务**：main.py（PID 3480027）

## 1. 问题（§64）

`/wf/processTask/execute` 用 `submitType=5` 时：
- facade.py L295-318 默认 else 分支把 5 当 AGREE 处理
- leader.RE_APPLY 直接流转到 end，state=20

## 2. 上游修复（vendor/jeeflow/facade.py）

```diff
         elif submit_type == SUBMIT_ROLLBACK_TO_OPERATOR:
             await self._engine.execute_and_jump_to_first_task_node(task_id, operator, flow_args)
+        elif submit_type == 5:  # SUBMIT_RE_APPLY — FIX-T6 2026-09-17：boot3 同义于跳回首个 task 节点（参考 §64 monkey patch 行为）
+            await self._engine.execute_and_jump_to_first_task_node(task_id, operator, flow_args)
         elif submit_type == SUBMIT_COUNTERSIGN_DISAGREE:
```

**注**：用字面量 `5` 而非 `SUBMIT_RE_APPLY` 常量，
因为 facade.py 顶部 SUBMIT_* 常量未定义 RE_APPLY（SubmitType 枚举在 model.py）。

## 3. 测试结果

```
设计: simple（apply → task1 → end）
操作: leader.RE_APPLY(5)
期望: 跳回 apply 任务

实测:
  state=10
  active=[(apply, ['user1'])]    ✅
  history:
    apply state=20                # 第 1 次完成
    task1 state=20                # leader 完成
    apply state=10                # RE_APPLY 跳回
```

## 4. 关键发现

1. **vendor 修改独立生效**：去掉 main.py + main_pg.py monkey patch 后仍正常工作
2. **RE_APPLY 与 ROLLBACK_TO_OPERATOR 等价**：复用 `execute_and_jump_to_first_task_node` 路径
3. **状态累积**：每个 task 节点每次进入产生新记录
4. **不需要 SubmitType 枚举引用**：facade.py 内可用字面量 `5`

## 5. 修复历程

| 阶段 | 实现 | 位置 |
|---|---|---|
| §64 BUG | jeeflow facade 缺 RE_APPLY 路由 | 上游缺失 |
| FIX-T4 (临时) | monkey patch facade.flow 替换 5 → 6 | main.py + main_pg.py |
| **FIX-T6 (本次)** | vendor/jeeflow/facade.py 新增 elif 分支 | **上游修复** |
| 后续 | 删 monkey patch（vendor 优先级生效） | main.py + main_pg.py |

## 6. 文档改进

- `docs/known-issues.md §64` 状态从 "FIX-T4 临时补丁" 更新为 "FIX-T6 上游修复"
- 新增 `docs/known-issues.md §74` vendor 改进工作流（已记录）
- AGENTS.md §1 已允许 vendor/jeeflow 修改（本次实测）

## 7. 测试报告

- vendor 上游修复：✅
- 不依赖 main.py monkey patch
- main.py + main_pg.py 同步清理（去掉 _reapply_flow）
