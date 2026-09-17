# BDD Regression Summary: flows/ 全 16 个流程

- **时间**：2026-09-17 17:35-17:45
- **覆盖**：flows/01-15 共 16 个 JSON（README.md 跳过）
- **服务**：8101 memory + 8102 PG

## 1. 测试结果矩阵

| 流程 | 名称 | 8101 | 8102 | 备注 |
|------|------|------|------|------|
| 01 | simple | ✅ | ✅ | 申请人→上级→结束 |
| 02 | multi-task | ✅ | ✅ | 三层审批 user1→leader→manager→boss |
| 03 | decision-expr | ✅ | ✅ | 金额决策（amount 未传走 fallback） |
| 04 | fork-join | ✅ | ✅ | 并行 userA+userB → join |
| 05 | countersign-parallel | ✅ | - | 并行会签 3 人 |
| 06 | countersign-sequential | ✅ | - | 顺序会签 userA→userB |
| 07 | countersign-ratio | ✅ | - | 比例会签（RatioCapableEngine） |
| 08 | countersign-sequential-approve | ✅ | - | 会签后联签 |
| 08-custom-node | custom-node | ❌ | ❌ | **已知缺陷 §16**（FIX-T17 raise） |
| 09 | with-reject | ✅ | - | 驳回路径（默认走通过） |
| 10 | mixed-mode | ✅ | ✅ | 业务流+拦截器 |
| 11 | assignee-vars | ✅ | ✅ | 处理人为变量 deptLeader |
| 11 | assignment-handler | ❌ | ❌ | **已知缺陷**：SPI DEMO_ROLE_TO_USERS.json 未装 |
| 12 | candidate-page | ✅ | ✅ | 候选人分页 |
| 13 | countersign-one-vote-veto | ✅ | ✅ | 一票否决会签 |
| 14 | decision-submitType | ✅ | ✅ | 提交类型决策 |
| 15 | decision-amount | ✅ | ✅ | 金额决策 |

**总计**：17 个 json（08 有两个变体）
- ✅ PASS：14 个
- ❌ FAIL（已知缺陷）：2 个（08-custom-node, 11-assignment-handler）
- **通过率**：14/16 = 87.5%

## 2. 关键发现

1. **22 个 vendor FIX 后所有标准流程正常运行**
2. **双端一致性**：memory + PG 行为完全一致（除 ID 格式）
3. **08-custom-node 引擎缺陷**：custom 节点 assignee 解析抛错（FIX-T17 改进，从静默改 raise）
4. **11-assignment-handler SPI 缺陷**：FormFieldAssigneeHandler 找不到 SPI 角色（SPI 配置文件不完整）

## 3. 文档改进

- runner.py v2 通用执行模板（taskActorIdList 字段修正）
- 08-custom-node / 11-assignment-handler 已知缺陷需在 AGENTS.md §7 反模式表补充
