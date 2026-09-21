# BDD 任务 #110: 多任务节点字段权限组合

## 目标
验证 2 个 task 节点各自有不同 PERMISSION 字段，写入规则是否被引擎强制

## 流程
apply → task_leader(f_amount=1只读, f_secret=2编辑) → task_manager(f_amount=2编辑, f_secret=3隐藏) → end

## 实测
| 节点 | 操作人 | 字段写入 | 期望落库 | 实测落库 | 结果 |
|------|--------|----------|----------|----------|------|
| apply | user1 | f_amount=1000, f_secret=ORIG | 1000, ORIG | 1000, ORIG | ✓ |
| task_leader | leader | f_amount=2000, f_secret=LEADER | 1000(只读), LEADER | 1000, LEADER | ✓ |
| task_manager | manager | f_amount=3000, f_secret=MGR | 3000, LEADER(隐藏) | 3000, LEADER | ✓ |

## 结论
✅ **PASS**：PERMISSION_* 字段权限在多任务节点流转中保持正确

## 关键验证
- 字段权限按**节点**独立计算（每个 task 节点读自己的 properties.field.PERMISSION_*）
- 隐藏字段(3) 写入值被静默丢弃，持久化保留上次值
- 编辑字段(2) 写入生效
- 只读字段(1) 写入值被忽略

## 跨任务副作用
- 上一节点的编辑结果会带到下一节点（f_secret=LEADER 从 leader→manager）
- 下一节点的隐藏规则只看自己节点的 PERMISSION 配置
- 这是正确行为：任务间变量共享，节点级权限独立

## 设计建议
- 字段权限码 1/2/3 已在 docs/flow.md §5.1 + known-issues §82 记录
- 字段权限只控制**写入**是否生效，不控制**展示**（隐藏字段值仍可通过 bizData 查）
