# FDEP 模块索引 · 8 个 .py + 5 个 JSON

> **来源**：本仓 `spi/fdep/` + 上游 jeeflow
> **定位**：给流程设计者用的「找人 + 查字典」模块索引——避免 `grep` 找半天才知道哪个文件管哪个接口

---

## 1. FDEP 是什么

**FDEP**（本仓自定义命名）= `spi/fdep/` 目录下的一组 SPI 实现，提供：
- 用户/部门查询（`get_user.py` / `find_dept_leaders.py` 等）
- 字典查询（`dicts.py`）
- 用户搜索（`user_search.py`）
- 内存数据（`data.py`）

被 `vendor/jeeflow/builtin.py` 的 8 个 assignment handler 调用：
- `OperatorAssignmentHandler`（指定操作人）
- `FormFieldAssigneeHandler`（表单字段指定）
- `DeptLeaderAssignmentHandler`（部门领导）
- `DeptMainLeaderAssignmentHandler`（部门主领导）
- `ApplicantDeptLeaderAssignmentHandler`（申请人部门领导）
- `ApplicantDeptMainLeaderAssignmentHandler`（申请人部门主领导）
- `TaskRoleAssigneeHandler`（任务角色）

**调用链**：
```
flow 定义（processDefine）参与者解析
  ↓
assignment handler（builtin.py）
  ↓
FDEP 实现（spi/fdep/*.py）
  ↓
返回参与者列表 → engine 创建 task
```

---

## 2. 8 个 .py 文件速查

| 文件 | 行数 | 公开函数 | 用途 |
|---|---|---|---|
| `__init__.py` | - | 导出所有 | 模块入口 |
| `data.py` | 582 | `get_*` / `find_*` | 内存数据 + 查询封装 |
| `dicts.py` | 171 | `get_dict_items(dict_type)` | 字典项查询 |
| `get_user.py` | - | `get_user_by_id(user_id)` | 按 ID 查用户 |
| `find_dept_leaders.py` | - | `find_dept_leaders(dept_id)` | 查部门所有领导 |
| `find_dept_main_leaders.py` | - | `find_dept_main_leaders(dept_id)` | 查部门主领导 |
| `user_search.py` | - | `search_users(keyword)` | 关键字搜用户 |
| `user_map.py` | - | `get_user_map()` | 全量用户映射 |

**详细行号**：`find spi/fdep -name '*.py' -exec wc -l {} +`

---

## 3. 5 个 JSON 数据文件

| 文件 | 用途 |
|---|---|
| `FDEP_DEPT_LEADERS.json` | 部门 → 领导列表 |
| `FDEP_DEPT_MAIN_LEADERS.json` | 部门 → 主领导 |
| `FDEP_DICTS.json` | 字典项 |
| `FDEP_FIND_USER_BY_ROLE_DEPT.json` | 按角色+部门查用户 |
| `FDEP_ROLES.json` | 角色定义 |

**示例**（FDEP_DEPT_LEADERS.json）：
```json
{"deptId":"D001","leaders":["user1","user2"]}
```

---

## 4. 在 flow 定义里如何使用

**场景**：申请人提交后自动找到「申请人部门领导」审批。

```python
# processDefine.json 中参与者解析配置
{
  "nodeId": "dept_leader_approve",
  "taskType": "APPROVE",
  "assignmentHandler": "ApplicantDeptLeaderAssignmentHandler"
  # handler 内部调用 spi/fdep/find_dept_main_leaders.py
}
```

**测试时**：用 `spi/dev/` 下的内存数据（`USERS.json` / `DEPTS.json` / `ROLES.json`），通过 `OrgUserProvider` 路由。

---

## 5. 设计者的 5 条常见操作

| 想做什么 | 改哪个文件 |
|---|---|
| 加一个字典类型 | `FDEP_DICTS.json` |
| 加一个角色 | `FDEP_ROLES.json` |
| 修改部门领导名单 | `FDEP_DEPT_LEADERS.json` |
| 修改主领导 | `FDEP_DEPT_MAIN_LEADERS.json` |
| 修改找用户规则 | `spi/fdep/find_*.py` |

---

## 6. 与上游差异

本仓 `spi/fdep/` 是**本仓独有扩展**（非上游 jeeflow 提供）。上游 jeeflow 用 `OrgUserProvider` SPI 让业务方自己实现。

**演进**：从上游 SPI → 本仓 `spi/fdep/` 内存实现 → 生产替换为 `spi/dev/` 实际数据库。

---

## 7. 相关 doc

- 引擎 SPI 矩阵 → `ToT/docs/spec/spi-matrix.md`（01 plan A4 待建）
- 8 个 assignment handler 详解 → `ToT/docs/guides/07-assignment-handlers.md`
- 用户/部门数据契约 → `ToT/docs/manual/02-dept-user-role.md`

---

**版本**：v1.11.1 · **来源**：故事 001（张 HR 找不到 FDEP 字典在哪）→ 02 persona review