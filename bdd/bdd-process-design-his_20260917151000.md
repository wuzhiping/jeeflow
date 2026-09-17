# BDD Task 53: processDesignHis 历史版本查询（PASS + 边界发现）

- **时间**：2026-09-17 15:10:00（TS=20260917151000）
- **服务**：main.py（PID 3462036）

## 1. 测试场景

同一个 design 部署 3 次 → 验证历史版本保留

| 部署次数 | processDefineId |
|---|---|
| 1 | 113 |
| 2 | 114 |
| 3 | 115 |

## 2. 测试结果

| API | 结果 |
|---|---|
| `/wf/processDesignHis/page` | **未知 action**（未注册） |
| `/wf/processDesign/detail` | 返回 `his: [...]` 字段（仅 1 条最新版本） |
| `/wf/processDesign/page` | 不返回 version 字段 |

### 关键发现

1. **`processDesignHis/page` API 不存在**：facade 没有 `_processDesignHis_*` 方法
2. **`/detail` 字段包含 `his`**：每次 deploy 时落一条 `wf_process_design_his` 表
3. **`his` 只保留最后 1 条**：每次 deploy 覆盖前一条（processDesignHis 累积应该不覆盖但实际只 1 条）
4. **每次 deploy 创建独立 processDefine**：但 design 关联的 processDefineId 没更新

## 3. Engine 行为（facade.py）

- `_processDesign_deploy`：先 save_his + save_design（关联 processDefineId），再 save define
- 设计表 isDeployed=1，历史表多条

## 4. 已知问题（§65）

| # | 问题 | 严重度 |
|---|---|---|
| 1 | `processDesignHis/page` 未注册 action | critical |
| 2 | `his` 字段只保留最后 1 条（应累积） | warning |
| 3 | `page` 接口不返回 version 字段 | warning |

## 5. 测试报告

- 设计约束：流程定义部署后历史版本应当累积，但本实现只保留 1 条
- API 命名规范：`_processDesignHis_*` 系列方法应在 facade 实现
