# SPI 实现规范（Service Provider Interface）

`spi/` 包为 jeeflow 工作流引擎提供**组织架构、用户、角色、字典**等基础数据的可插拔实现。

通过环境变量 `SPI_FOLDER` 切换不同实现，**无需修改业务代码**。

---

## 1. 包结构

```
spi/
├── __init__.py              # dispatcher 入口（SPI() / SimpleUserProvider / SpiOrgUserProvider）
├── SPEC.md                  # 本规范
├── demo/                    # 默认演示实现
│   ├── data.py              # JSON 加载器
│   ├── DEMO_*.json          # 演示数据
│   └── <func>.py            # 各 SPI 函数
├── dev/                     # 开发场景实现
│   ├── data.py
│   ├── DEV_*.json
│   └── <func>.py
└── <other>/                 # 第三方或自定义实现
```

每个实现（如 `demo`、`dev`）是一个 **regular Python package**，必须有 `__init__.py`（可为空）。

---

## 2. 切换实现

### 2.1 环境变量

```bash
export SPI_FOLDER=dev      # 切换至 spi/dev
python main.py
```

### 2.2 Python 入口切换

```python
import os
os.environ["SPI_FOLDER"] = "dev"
import spi                  # 必须在设置 envvar 之后 import
```

### 2.3 默认值

未设置 `SPI_FOLDER` 时使用 `demo`（向后兼容）。

---

## 3. 规范（每个实现必须遵守）

### 3.1 目录约定

- 包名 = 实现名（小写字母 + 数字 + 下划线）
- 数据 JSON 文件统一前缀：`<PACKAGE>_<ENTITY>.json`（如 `demo` 包用 `DEMO_USERS.json`，`dev` 包用 `DEV_USERS.json`）
- `data.py` 暴露以下常量（dict 类型）：

  | 常量名 | 数据结构 | 用途 |
  |--------|----------|------|
  | `SPI_USERS` | `{<uid>: {"name": str, "post": str}}` | 全量用户表 |
  | `SPI_ROLES` | `{<role_code>: <role_name>}` | 角色字典 |
  | `SPI_DICTS` | `{<dict_code>: [{"value", "label"}]}` | 业务字典 |
  | `SPI_ROLE_TO_USERS` | `{<role_code>: [<uid>]}` | 角色→用户映射 |
  | `SPI_DEPT_LEADERS` | `{<dept_id>: [<uid>]}` | 部门领导 |
  | `SPI_DEPT_MAIN_LEADERS` | `{<dept_id>: [<uid>]}` | 分管领导 |
  | `SPI_FIND_USER_BY_ROLE_DEPT` | `{"functions": {"find_user_by_role_dept": {<key>: [<uid>]}}}` | 角色+部门组合查找 |

### 3.2 函数文件

每个 SPI 函数对应一个 `<func>.py`，必须导出：

```python
def SPI(payload, token={}) -> <return_type>:
    """实现业务逻辑"""
    ...

def pocketflow(payload, token={}) -> <return_type>:
    """dispatcher 调用入口，委托给 SPI()"""
    return SPI(payload, token)
```

### 3.3 函数清单（必须实现）

| 函数名 | payload | 返回值 | 说明 |
|--------|---------|--------|------|
| `get_user` | `{"uid": str}` | `{"userId","realName","deptId","deptName","postId","postName"}` | 单用户查询，对齐 `UserProvider.get_user` |
| `user_map` | `{}` | `{"USERS": {<uid>: {"name","post"}}}` | 全量用户表 |
| `user_search` | `{"m_*": kw, "pageNum": int, "pageSize": int}` | `{"rows": [...], "total": int}` | 多关键字 AND 分页 |
| `roles` | `{}` | `SPI_ROLES` 原样 | 角色列表 |
| `dicts` | `{}` | `SPI_DICTS` 原样 | 字典全集 |
| `find_by_role` | `{"role_code": str}` | `[<uid>]` | 按角色取人，对齐 `OrgUserProvider.find_by_role` |
| `find_dept_leaders` | `{"dept_id"/"u_deptId"/"deptId": str}` | `[<uid>]` | 部门领导，对齐 `OrgUserProvider.find_dept_leaders` |
| `find_dept_main_leaders` | `{"dept_id"/"u_deptId"/"deptId": str}` | `[<uid>]` | 分管领导，对齐 `OrgUserProvider.find_dept_main_leaders` |
| `find_user_by_role_dept` | `{"deptId"/"u_deptId","roleCode"/"role"}` 或 `{"key": "dept:role"}` | `[<uid>]` | 角色+部门组合 |

### 3.4 dispatcher 调用约定

`spi/__init__.py:SPI(func, payload, token={})` 是唯一入口：

1. 拼路径 `spi.<SPI_FOLDER>.<func>`
2. `import_module + reload` 强制重载（JSON 热更新生效）
3. 调用模块的 `pocketflow(payload, token)` 取返回值
4. 返回值由调用方按需封装

**实现模块禁止跨包依赖**——`spi/dev/` 只能 import `spi.dev.data`（同包），不能 import `spi.demo.*`。

### 3.5 命名空间隔离

| 层级 | 函数名 | 入参 | 出参 |
|------|--------|------|------|
| dispatcher | `SPI(func, payload, token)` | `func: str, payload: dict, token: dict` | 调用结果 |
| impl | `SPI(payload, token)` | `payload: dict, token: dict` | 业务结果 |
| impl 入口 | `pocketflow(payload, token)` | 同 impl | 同 impl |

名字相同（都叫 `SPI`）但参数不同——调用方用 dispatcher (`spi.SPI(...)`)，实现内调用自己的 `SPI(...)`。

---

## 4. 扩展新实现步骤

1. 创建 `spi/<your_name>/__init__.py`（空文件即可）
2. 准备数据 JSON：`<YOUR_NAME>_USERS.json` / `ROLES.json` / `DICTS.json` / `ROLE_TO_USERS.json` / `DEPT_LEADERS.json` / `DEPT_MAIN_LEADERS.json` / `FIND_USER_BY_ROLE_DEPT.json`
3. 写 `data.py` 加载 JSON 并暴露常量
4. 逐函数实现 `<func>.py`（参照 §3.3 函数清单）
5. 实现 `cli.py` + `api.py`（参照 §8）
6. 测试：
   ```bash
   SPI_FOLDER=<your_name> python -c "from spi import SPI; print(SPI(func='roles', payload={}))"
   SPI_FOLDER=<your_name> python -m spi.cli verify
   SPI_FOLDER=<your_name> python -m spi.cli list-users
   ```
7. 业务层启动时设置 `SPI_FOLDER=<your_name>`

---

## 5. 顶层封装（`spi/__init__.py`）

| 名称 | 类型 | 说明 |
|------|------|------|
| `SPI(func, payload, token={})` | 函数 | dispatcher 唯一入口 |
| `SPI_FOLDER` | str | 当前实现名（envvar 控制） |
| `SPI_USERS / SPI_ROLES / SPI_DICTS` | dict | re-export 当前实现的数据 |
| `SimpleUserProvider` | class | `get_user(uid) -> UserInfo`，对齐 `jeeflow.spi.UserProvider` |
| `SpiOrgUserProvider(OrgUserProvider)` | class | `find_dept_leaders / find_dept_main_leaders / find_by_role` |
| `spi_user_search(query)` | 函数 | 解包 `user_search` 为 `(rows, total)` |

---

## 6. 已实现

| 包 | 场景 | 用户数 | 角色数 | 字典数 | 备注 |
|----|------|--------|--------|--------|------|
| `demo` | OA 审批（研发部/市场部/财务部/总经办） | 9 | 4 + SPI 角色 75 个 | 2 | 默认，演示用 |
| `dev` | 研发协作（前端组/架构组） | 6 | 4 + SPI 角色 6 个 | 2 | 扁平开发团队，演示用 |

---

## 7. 零父依赖

每个实现包**禁止 import 父包或父包同级模块**（除 `spi.<self>.data`）。本包可独立 import、单独 reload，与项目主入口（`main.py`/`main_pg.py`）解耦。

---

## 8. CLI / API 规范（v26 新增）

### 8.1 概述

dispatcher 层（`spi/cli.py` + `spi/api.py`）通过 `SPI_FOLDER` 动态路由到实现包的 `cli.py` + `api.py`。

**核心原则**：CLI / API 跟随 SPI_FOLDER 自动切换，**不跳过 SPI**。

### 8.2 dispatcher 层入口

#### `spi/cli.py` — CLI 统一入口

- `python -m spi.cli verify`
- `python -m spi.cli status`
- `python -m spi.cli list-users`
- `python -m spi.cli show-user <uid>`
- `python -m spi.cli list-depts`
- `python -m spi.cli show-dept <dept_id>`
- `python -m spi.cli help`
- `python -m spi`（通过 `spi/__main__.py`）

#### `spi/api.py` — FastAPI 路由

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/spi/verify` | GET | 数据完整性验证 |
| `/api/spi/status` | GET | 数据概况 |
| `/api/spi/users` | GET | 列出所有用户 |
| `/api/spi/users/{uid}` | GET | 用户详情 |
| `/api/spi/depts` | GET | 列出所有部门 |
| `/api/spi/depts/{dept_id}` | GET | 部门详情 + 成员 |

集成方式：
```python
from spi.api import register_routes
register_routes(app)  # main.py / main_pg.py 调用
```

### 8.3 实现包接口约定（强制）

每个实现包（如 `spi/demo/`、`spi/dev/`）**必须提供**：

- `cli.py`：暴露 6 个 `_data_*` 数据获取函数（返回纯 dict / list，不做打印）
- `api.py`：从 cli.py re-export 同样的 6 个函数（FastAPI 用）

#### 6 个 `_data_*` 函数签名

```python
def _data_verify() -> dict:
    """数据完整性验证结果"""

def _data_status() -> dict:
    """SPI 数据概况 (通常复用 verify 结果)"""

def _data_list_users() -> list[dict]:
    """用户列表, 每用户 6 字段: uid, name, post, level, dept_id, roles"""

def _data_show_user(uid: str) -> dict | None:
    """用户详情 (None 表示 uid 不存在)"""

def _data_list_depts() -> list[dict]:
    """部门列表, 每部门 5 字段: dept_id, name, size, leader, main_leader"""

def _data_show_dept(dept_id: str) -> dict | None:
    """部门详情 + 成员, 返回 {info, members} 或 None"""
```

### 8.4 行为约定

- dispatcher 检测 `SPI_FOLDER`，调用对应实现包
- 实现包提供 `cli.py` + `api.py`：路由到该实现包
- 实现包**未提供** `cli.py` 或 `api.py`：
  - CLI：`NotImplementedError` → 退出码 1 + stderr 错误信息
  - API：HTTP 404 + `detail: "SPI_FOLDER=<folder> 不支持 API (缺少 api 模块)"`
- **禁止**在 dispatcher 层硬编码具体实现包（如 `from spi.dev.cli`）

### 8.5 扩展新实现包（CLI/API）

1. 创建 `spi/<name>/cli.py`，实现 6 个 `_data_*` 函数
2. 创建 `spi/<name>/api.py`，从 cli.py re-export 6 个函数
3. 测试：
   ```bash
   SPI_FOLDER=<name> python -m spi.cli verify
   SPI_FOLDER=<name> python -m spi.cli list-users
   ```
4. 启动 `main.py` 时设置 `SPI_FOLDER=<name>`，API 自动跟随
