# FIX-T28 TDD 报告

## 目标
08-custom-node 流程在 vendor FIX-T17 raise 后无法启动；新增 custom 节点 fallback `[operator]`

## 改动
- **vendor/jeeflow/engine.py:EngineImpl._resolve_actors**（FIX-T28，2026-09-17）
  - 在最后 `return []` 前判断 `if node.type == TYPE_CUSTOM: return [operator]`
  - 仅 custom 节点回落，task 节点继续 raise（行为一致）

## TDD 用例
| ID | 场景 | 期望 | 实际 |
|----|------|------|------|
| 1 | 8101 memory 08-custom-node | start + execute-user1 → state=20 | ✅ |
| 2 | 8102 PG 08-custom-node | start + execute-user1 → state=20 | ✅ |

## 端到端验证
- 8101 memory 后端：✅
- 8102 PG 后端：✅

## 复盘
- 之前 FIX-T17 让所有 custom 节点 raise
- 现在 custom 节点（snaker:custom）走 fallback `[operator]`
- task 节点继续 raise（保留 FIX-T17 错误提示能力）
- 后续：可实现真正的 custom 节点 clazz/methodName 调用
