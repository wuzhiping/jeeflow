# spi.dev SPI 实现包

**FlowMatrix 科技研发组织** · 13 虚构人员 · 5 部门 (tree 结构 parent_id) · 8 角色 · 4 字典组 · 派生导航 (USERS_BY_DEPT / USERS_BY_LEVEL / USERS_FULL / DEPT_LEADER_BY_USER / DEPT_MAIN_LEADER_BY_USER / USER_DEPT_CHAIN / USER_LEADER_CHAIN / ANCESTORS / DESCENDANTS / DEPT_FULL_INFO / DEPT_MEMBERS_FULL) (重构 v19 · 2026-11-17)

研发场景组织结构 / 用户 / 角色 / 字典的 SPI（Service Provider Interface）实现集。
供前端 `candidatePage`、工作流审批节点、API Mock 等场景在无真实后端时按统一契约取数。

---

## 目录结构

```
spi/dev/
├── __init__.py              # 空，标记 regular package
├── data.py                  # JSON 加载器（仅供本包内部 from .data import 使用）
├── jsons/                   # 数据 JSON 子目录 (重构 v2 · v3 去 DEV_ 前缀 · v4 DEPT 合并 · v5 复数化)
│   ├── USERS.json             # 8 个开发场景用户
│   ├── ROLES.json             # 4 个开发场景角色
│   ├── DICTS.json             # 2 组开发场景字典
│   ├── ROLE_TO_USERS.json     # 4 个角色-用户映射
│   └── DEPTS.json             # 部门数据 (合并 dept_leaders + dept_main_leaders + find_user_by_role_dept, 复数命名)
│
├── user_map.py              # 全量用户表（SPI func=user_map）
├── get_user.py              # 按 uid 取单用户（SPI func=get_user）
├── user_search.py           # 多关键字分页检索（SPI func=user_search）
├── roles.py                 # 角色列表（SPI func=roles）
├── dicts.py                 # 字典全集（SPI func=dicts）
│
├── find_by_role.py          # 按角色码取用户（SPI func=find_by_role）
├── find_dept_leaders.py     # 按部门取部门领导（SPI func=find_dept_leaders）
└── find_dept_main_leaders.py# 按部门取分管领导（SPI func=find_dept_main_leaders）
```

---

## 调用契约

### 1. dispatcher 入口（`spi/__init__.py`）

```python
from spi import SPI
SPI(func, payload, folder="demo", token={}) -> dict | list
```

调度规则：
1. 拼接 `sopfile = "spi." + folder + "." + func`
2. `import_module(sopfile)` + `reload(agt)`（每次调用强制重载，便于 JSON 热更新）
3. 调用 `agt.pocketflow(payload, token)` 取返回值

因此**每个实现文件必须导出 `pocketflow(payload, token) -> Any`**，并在其内部委托给 `SPI(payload, token)`。

### 2. impl SPI 入口（每个 `spi/dev/<func>.py`）

```python
def SPI(payload, token={}) -> <返回类型>:
    ...
def pocketflow(payload, token={}) -> <返回类型>:
    return SPI(payload, token)
```

约定：
- `payload`：dict，调用方传入的入参（按实现约定取值）
- `token`：dict，默认 `{}`；保留位用于将来注入会话信息
- 返回值：见各函数清单

### 3. SPI 命名空间隔离

dispatcher `SPI(func, payload, folder, token)` 与 impl `SPI(payload, token)` 名字相同但参数不同（dispatcher 多了 `func`/`folder`，impl 只有 `payload`/`token`），调用链为：

```
调用方 → spi.SPI(func, payload, folder, token)      # dispatcher
        → agt.pocketflow(payload, token)            # impl 入口
        → agt.SPI(payload, token)                   # impl 业务
```

---

## 数据源（JSON）

由 `data.py` 加载，路径相对本包目录（不依赖 cwd）。

### `USERS.json` —— 8 个开发场景用户

```json
{
  "<uid>": {"name": "<中文姓名>", "post": "<岗位名>"},
  ...
}
```

| uid       | name | post     |
|-----------|------|----------|
| user1     | 张三 | 工程师   |
| userA     | 孙倩 | 工程师   |
| userB     | 周明 | 工程师   |
| userC     | 吴婷 | 工程师   |
| leader    | 李四 | 组长     |
| manager   | 王五 | 经理     |
| director  | 赵六 | 总监     |
| boss      | 钱七 | 总经理   |

### `ROLES.json` —— 4 个开发场景角色

```json
{"<role_code>": "<role_name>"}
```

| role_code | role_name |
|-----------|-----------|
| engineer  | 工程师     |
| leader    | 组长       |
| manager   | 经理       |
| director  | 总监       |

### `DICTS.json` —— 2 组开发场景字典

```json
{"<code>": [{"value": "<v>", "label": "<l>"}, ...]}
```

- `wf_leave_type` → 年假 / 病假 / 事假
- `wf_process_type` → OA / 人事 / 财务

### `ROLE_TO_USERS.json` —— 角色-用户映射

```json
{"<role_code>": ["<uid>", ...]}
```

| role_code | uids        |
|-----------|-------------|
| leader    | ["leader"]  |
| manager   | ["manager"] |
| director  | ["director"]|
| boss      | ["boss"]    |

未列出的 role_code 一律返回 `[]`。

### `DEPTS.json` —— 部门基础数据 + 领导映射 + 角色组合 (重构 v4 · v5 复数化)

> **重构说明 (v4)**: 此文件合并了 3 个旧 JSON (`DEPT_LEADERS.json` + `DEPT_MAIN_LEADERS.json` + `FIND_USER_BY_ROLE_DEPT.json`).
> **重构说明 (v5)**: 文件名 `DEPT.json` → `DEPTS.json` (复数化, 与 `USERS.json` / `ROLES.json` / `DICTS.json` 命名一致).
> 对外 API 不变 (`SPI_DEPT_LEADERS` / `SPI_DEPT_MAIN_LEADERS` / `SPI_FIND_USER_BY_ROLE_DEPT` 三个常量保持派生兼容).

```json
{
  "version": "1.0.0",
  "departments": {
    "<dept_id>": {
      "name": "<部门名>",
      "leader": "<leader_uid>",
      "main_leader": "<main_leader_uid>",
      "role_combinations": {
        "<role_code>": ["<uid>", ...]
      }
    }
  }
}
```

| 字段 | 说明 |
|------|------|
| `name` | 部门中文名 |
| `leader` | 部门领导 (uid) |
| `main_leader` | 分管领导 (uid) |
| `role_combinations` | 该部门下, 角色对应的用户列表 |

**示例 (D01 研发部)**:
```json
{
  "name": "研发部",
  "leader": "leader",
  "main_leader": "director",
  "role_combinations": {
    "leader": ["leader"],
    "finance": ["leader"]
  }
}
```

---

## 函数清单

每个 SPI 函数对应 `spi/demo/<func>.py` 一个文件，调用方式：

```python
from spi import SPI
SPI(func="<func>", payload={...}, folder="demo", token={})
```

### user_map —— 全量用户表

- **入参 `payload`**：忽略
- **返回**：`{"USERS": {<uid>: {"name","post"}, ...}}`（即 `SPI_USERS` 原样）
- **用途**：前端冷启动一次性拉全表，做本地客户端检索缓存
- **顶层封装**：无

### get_user —— 按 uid 取单用户

- **入参 `payload`**：`{"uid": "<uid>"}`
- **返回**：
  ```python
  {
    "userId":   "<uid>",
    "realName": "<name>",
    "deptId":   "D01",
    "deptName": "研发部",
    "postId":   "P01",
    "postName": "<post>",
  }
  ```
- **fallback**：未知 uid 返回 `{"userId": uid, "realName": "用户"+uid, "deptId":"D01", "deptName":"研发部", "postId":"P01", "postName":"工程师"}`
- **顶层封装**：`SimpleUserProvider.get_user(uid) -> UserInfo`，与 `jeeflow.spi.UserProvider` 接口对齐

### user_search —— 多关键字分页检索

- **入参 `payload`**：
  - `m_*` 开头键：模糊检索条件，**全部**任一命中即纳入结果（OR 语义）
  - `pageNum`：int，默认 `1`；非法值回落 `1`
  - `pageSize`：int，默认 `10`；非法值回落 `10`
- **返回**：
  ```python
  {"rows": [...], "total": <int>}
  ```
  其中 `rows` 每项形态同 `get_user`；`total` 为分页前全量命中数
- **匹配规则**：对每条记录的 `uid` / `realName`（小写）做子串包含；多个关键字间为 AND
- **顶层封装**：`spi_user_search(query) -> (rows, total)`，解包为 tuple

### roles —— 角色列表

- **入参 `payload`**：忽略
- **返回**：`SPI_ROLES` 原样（dict，4 项）
- **顶层封装**：无

### dicts —— 字典全集

- **入参 `payload`**：忽略
- **返回**：`SPI_DICTS` 原样（dict，2 组）
- **顶层封装**：无

### find_by_role —— 按角色码取用户 uid 列表

- **入参 `payload`**：`{"role_code": "<code>"}`
- **返回**：`list[str]`（uid 列表；未匹配返回 `[]`）
- **顶层封装**：`SpiOrgUserProvider.find_by_role(role_code) -> list`（async）

### find_dept_leaders —— 按部门取部门领导

- **入参 `payload`**：`{"dept_id": "<dept>"}`
- **返回**：`list[str]`，演示固定 `["leader"]`
- **顶层封装**：`SpiOrgUserProvider.find_dept_leaders(dept_id) -> list`（async）

### find_dept_main_leaders —— 按部门取分管领导

- **入参 `payload`**：`{"dept_id": "<dept>"}`
- **返回**：`list[str]`，演示固定 `["manager"]`
- **顶层封装**：`SpiOrgUserProvider.find_dept_main_leaders(dept_id) -> list`（async）

---

## 顶层封装（`spi/__init__.py`）

| 名称 | 类型 | 用途 |
|------|------|------|
| `SPI(func, payload, folder="demo", token={})` | 函数 | dispatcher 入口 |
| `SPI_FOLDER` | str | 默认 `"demo"`；envvar `SPI_FOLDER` 可在 `import spi` 前覆盖 → 切换至 `spi.<SPI_FOLDER>.data` |
| `SPI_USERS / SPI_ROLES / SPI_DICTS` | dict | 默认 `demo` 数据常量 re-export |
| `SimpleUserProvider` | class | `get_user(uid) -> UserInfo`，对齐 `jeeflow.spi.UserProvider` |
| `SpiOrgUserProvider(OrgUserProvider)` | class | `find_dept_leaders / find_dept_main_leaders / find_by_role`，对齐 `jeeflow.spi.OrgUserProvider` |
| `spi_user_search(query)` | 函数 | 解包 `user_search` 为 `(rows, total)` |

---

## 使用示例

```python
from spi import SPI, spi_user_search, SpiOrgUserProvider
import asyncio

# 1. 直调 dispatcher
SPI(func="get_user",  payload={"uid": "user1"})
SPI(func="roles",     payload={})
SPI(func="dicts",     payload={})
SPI(func="user_map",  payload={})

# 2. 检索 wrapper
rows, total = spi_user_search({"m_realName": "张", "pageNum": 1, "pageSize": 10})

# 3. 组织维度（async）
async def main():
    s = SpiOrgUserProvider()
    print(await s.find_by_role("manager"))           # ['manager']
    print(await s.find_dept_leaders("D01"))         # ['leader']
    print(await s.find_dept_main_leaders("D01"))    # ['manager']
asyncio.run(main())
```

---

## 扩展新实现

1. 在 `spi/<your_folder>/__init__.py` 留空（regular package marker）
2. 复用 `data.py` 模式：把 JSON 放到同目录，loader 暴露常量
3. 每个函数一个文件 `<func>.py`，导出 `SPI(payload, token)` + `pocketflow(payload, token)`
4. `from spi import SPI` 即可（`SPI_FOLDER` 默认仍为 `demo`；改 envvar 切到 `<your_folder>`）

---

## 零父依赖

`spi/demo/` 所有实现模块**禁止 import 任何父包或父包同级模块**（除 `spi.demo.data` 外）。本包可独立 import、单独 reload，与项目主入口（`main.py`/`main_pg.py`）解耦。