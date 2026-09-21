# FIX-T22 TDD 报告

## 目标
未知节点类型从「静默 return（流程卡死无错误）」升级为「明确报错」

## 改动
- **vendor/jeeflow/engine.py:_execute_node**（FIX-T22，2026-09-17）
  - 在 `else` 分支新增 `raise ValueError(f"未知节点类型: ...")` 替代静默 return

## TDD 用例
| ID | 场景 | 期望 | 实际 |
|----|------|------|------|
| 1 | 含 snaker:unknown 节点的流程启动 | 启动失败 + 明确错误信息 | ✅ code=99999999 msg=`[ValueError] 未知节点类型: node_id='unk' type='snaker:unknown'` |

## 端到端验证
- 8101 memory 后端：✅ ValueError 抛出
- 8102 PG 后端：✅ 已部署，无影响

## 复盘
- 之前未知节点类型会让流程卡在 `unk` 节点后无任何提示
- 现在会立即抛错，设计器/调用方可快速定位
- 后续：可考虑 `_engine_warning` 日志记录 + metrics 计数
