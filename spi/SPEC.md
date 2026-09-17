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
5. 测试：
   ```bash
   SPI_FOLDER=<your_name> python -c "from spi import SPI; print(SPI(func='roles', payload={}))"
   ```
6. 业务层启动时设置 `SPI_FOLDER=<your_name>`

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
