# 2026-11-17 spi/dev 重构 v25 · CLI → FastAPI 路由 (远程 API 暴露)

> **重构日期**: 2026-11-17 (W47 Day 5)
> **状态**: ✅ **published** · 20 DictProxy + 9 SPI 函数 + 2 helpers + CLI v22-v24 不动 (内部重构提取 _data_* 函数)
> **关联**: `spi/dev/api.py` 新增 (FastAPI APIRouter) + 6 路由
> **下一里程碑**: v26 dispatcher 三层分离

---

## 1. 重构动机

**v22-v24 CLI 只能在本地查**, 无法:
- Web 前端集成 SPI 数据
- 远程 dashboard / 监控
- 多进程共享同一数据视图

**目标**: 把 CLI 的 4 查询命令暴露为 FastAPI 路由, 保持 CLI 与 API 一致语义.

---

## 2. 改动范围

### 2.1 新增文件

| 文件 | 行数 | 内容 |
| --- | --- | --- |
| `spi/dev/api.py` | 约 130 | FastAPI APIRouter + 6 路由 |

### 2.2 重构 cli.py

| 操作 | 详情 |
| --- | --- |
| 提取 6 个 `_data_*` 函数 | `_data_verify() / _data_status() / _data_list_users() / _data_show_user(uid) / _data_list_depts() / _data_show_dept(dept_id)` |
| cli.py 命令改为调用 `_data_*` 函数 | 命令只负责格式化输出 |
| api.py 命令也调用 `_data_*` 函数 | 路由只负责 JSON 响应 |

**关键**: CLI 与 API 共享同一数据访问函数, 0 重复实现.

### 2.3 main.py 改动 (+2 行)

```python
# main.py
from spi.dev.api import router as spi_router
app.include_router(spi_router)  # 注册 6 路由
```

### 2.4 6 API 端点

| 方法 | 路径 | 函数 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/spi/verify` | `_data_verify()` | verify 结果 |
| GET | `/api/spi/status` | `_data_status()` | SPI 概况 |
| GET | `/api/spi/users` | `_data_list_users()` | 用户列表 |
| GET | `/api/spi/users/{uid}` | `_data_show_user(uid)` | 用户档案 |
| GET | `/api/spi/depts` | `_data_list_depts()` | 部门列表 |
| GET | `/api/spi/depts/{dept_id}` | `_data_show_dept(dept_id)` | 部门详情 |

---

## 3. 测试 (8/8 PASS, curl)

```bash
$ curl http://localhost:8101/api/spi/verify
{"ok": true, "errors": [], "warnings": [], "summary": {...}}

$ curl http://localhost:8101/api/spi/users/u_fe_eng
{"userId": "u_fe_eng", "name": "周磊", "dept_name": "前端组", ...}

$ curl -i http://localhost:8101/api/spi/users/u_nonexistent
HTTP/1.1 404 Not Found
{"detail": "User not found: u_nonexistent"}
```

---

## 4. 设计决策

### 4.1 _data_* 函数是 CLI/API 共享契约

- **位置**: spi/dev/cli.py 定义 (因为它最初在 CLI 引入)
- **签名**: 不允许改 (v26 提升到 SPEC.md §8 正式约束)
- **复用**: api.py 直接调用, 无重复

### 4.2 FastAPI APIRouter (不是直接挂载)

- **APIRouter**: 模块化路由, 便于 v26 dispatcher 重组
- **prefix**: 不在 APIRouter 设 (因为 main.py 是 include_router 入口)

### 4.3 错误处理

| 场景 | 状态码 | body |
| --- | --- | --- |
| 查询成功 | 200 | data dict |
| uid 不存在 | 404 | `{"detail": "User not found: xxx"}` |
| dept_id 不存在 | 404 | `{"detail": "Dept not found: xxx"}` |

---

## 5. 关键代码片段

### 5.1 api.py (FastAPI APIRouter)

```python
from fastapi import APIRouter, HTTPException
from .cli import _data_verify, _data_status, _data_list_users, _data_show_user, _data_list_depts, _data_show_dept

router = APIRouter()

@router.get("/api/spi/verify")
async def spi_verify():
    return _data_verify()

@router.get("/api/spi/users/{uid}")
async def spi_show_user(uid: str):
    user = _data_show_user(uid)
    if user is None:
        raise HTTPException(404, f"User not found: {uid}")
    return user
```

---

## 6. 经验教训

1. **CLI 与 API 共享数据访问层**: 提取 `_data_*` 函数, 避免重复
2. **APIRouter 模块化**: 便于 v26 dispatcher 重组
3. **错误码统一**: 404 + `{"detail": ...}`, FastAPI 标准
4. **为 v26 dispatcher 铺路**: 6 端点 + 6 _data_* 函数契约, dispatcher 只需动态加载实现层

---

**复盘作者**: hermes · 2026-11-17
**复盘状态**: published
**关联**: v24 CLI retrospective / v26 dispatcher retrospective / v28 main_common retrospective