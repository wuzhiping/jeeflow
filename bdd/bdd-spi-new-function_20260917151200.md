# BDD Task 54: SPI 新增 find_user_by_role_dept（PASS）

- **时间**：2026-09-17 15:12:00（TS=20260917151200）

## 1. 新增 SPI

新增 `spi/demo/find_user_by_role_dept.py` + `DEMO_FIND_USER_BY_ROLE_DEPT.json`：

| key | 返回 |
|---|---|
| D01:leader | ['leader'] |
| D02:manager | ['manager'] |
| D03:director | ['director'] |
| D01:finance | ['leader'] |
| D02:finance | ['manager'] |
| D99:none | [] |

## 2. 测试结果

```python
SPI(func='find_user_by_role_dept', payload={'key': 'D01:leader'}) → ['leader']
SPI(func='find_user_by_role_dept', payload={'key': 'D02:manager'}) → ['manager']
SPI(func='find_user_by_role_dept', payload={'key': 'D99:none'}) → []
```

## 3. SPI 注册流程

1. 新增 `spi/demo/DEMO_FIND_USER_BY_ROLE_DEPT.json` 数据
2. `spi/demo/data.py` 增加 `SPI_FIND_USER_BY_ROLE_DEPT = _load("...")`
3. 新增 `spi/demo/find_user_by_role_dept.py`：
   - `SPI(payload, token) -> list`
   - `pocketflow(payload, token) -> list`（SPI 框架调用入口）
4. `spi.__init__.py` 的 `SPI()` 函数自动 import + reload（无需手动注册）

## 4. 关键发现

1. **`SPI(func='xxx', payload)` 是统一调用入口**：`spi/__init__.py` 通过 `import_module + reload` 动态加载
2. **`pocketflow` 是 SPI 模块必须导出的函数**：SPI() 调用 `agt.pocketflow(payload, token)`
3. **数据/逻辑分离**：`data.py` 模块级 dict 启动加载，业务逻辑在 `xxx.py` 中
4. **`SPI_FOLDER` 环境变量可切换 SPI 实现**：默认 `demo`，可换为 prod 部署

## 5. 与现有 SPI 对比

| SPI | 入参 payload | 返回 |
|---|---|---|
| find_by_role | {role_code} | list[userId] |
| find_dept_leaders | {dept_id} | list[userId] |
| find_user_by_role_dept | {key: "D01:leader"} 或 {deptId, roleCode} | list[userId] |

复合查询更精细，支持按 (部门, 角色) 组合取人。

## 6. 测试报告

- 实际场景：流程图根据发起人部门 + 角色动态选审批人
- 使用方：`OrgUserProvider` 可加 `find_user_by_role_dept` 方法复用此 SPI
