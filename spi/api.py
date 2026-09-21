"""spi FastAPI 路由 (dispatcher 层, 重构 v26)

统一的 API 入口, 通过 SPI_FOLDER 动态选择实现包:
- SPI_FOLDER=demo → spi/demo/api.py
- SPI_FOLDER=dev  → spi/dev/api.py

Routes:
- GET /api/spi/verify        → 数据完整性验证
- GET /api/spi/status        → 数据概况
- GET /api/spi/users         → 列出所有用户
- GET /api/spi/users/{uid}   → 用户详情
- GET /api/spi/depts         → 列出所有部门
- GET /api/spi/depts/{dept_id} → 部门详情 + 成员

每个实现包必须提供 api.py, 导出以下 _data_* 函数 (参见 SPEC §8):
- _data_verify, _data_status, _data_list_users, _data_show_user,
  _data_list_depts, _data_show_dept

如果 SPI_FOLDER=<impl> 但 <impl>/api.py 不存在, 返回 HTTP 404 + 错误信息.
"""
from fastapi import APIRouter, HTTPException

from .cli import (
    _data_verify,
    _data_status,
    _data_list_users,
    _data_show_user,
    _data_list_depts,
    _data_show_dept,
)


router = APIRouter(prefix="/api/spi", tags=["spi"])


def _try_data(func_name: str):
    """调用当前 SPI_FOLDER 的 _data_* 函数

    Raises:
        HTTPException: 404 - 实现包不支持 API (缺少 api.py)
    """
    from spi import get_spi_folder
    folder = get_spi_folder()
    try:
        from importlib import import_module
        api_mod = import_module(f"spi.{folder}.api")
    except ImportError as e:
        raise HTTPException(
            status_code=404,
            detail=f"SPI_FOLDER={folder} 不支持 API (缺少 api 模块): {e}",
        )
    func = getattr(api_mod, func_name, None)
    if func is None:
        raise HTTPException(
            status_code=500,
            detail=f"spi.{folder}.api 缺少 {func_name} 函数",
        )
    return func


@router.get("/verify")
def api_verify() -> dict:
    """数据完整性验证

    对应 CLI: python -m spi.cli verify
    """
    return _try_data("_data_verify")()


@router.get("/status")
def api_status() -> dict:
    """SPI 数据概况

    对应 CLI: python -m spi.cli status
    """
    return _try_data("_data_status")()


@router.get("/users")
def api_list_users() -> dict:
    """列出所有用户

    对应 CLI: python -m spi.cli list-users

    返回: {
        "spi_folder": str,
        "total": int,
        "users": [
            {"uid", "name", "post", "level", "dept_id", "roles"}
        ]
    }
    """
    from spi import get_spi_folder
    users = _try_data("_data_list_users")()
    return {
        "spi_folder": get_spi_folder(),
        "total": len(users),
        "users": users,
    }


@router.get("/users/{uid}")
def api_show_user(uid: str) -> dict:
    """显示用户完整信息

    对应 CLI: python -m spi.cli show-user <uid>

    HTTP 状态码:
    - 200: uid 存在
    - 404: uid 不存在 (或 SPI_FOLDER 不支持)
    """
    info = _try_data("_data_show_user")(uid)
    if info is None:
        raise HTTPException(status_code=404, detail=f"User not found: {uid}")
    return info


@router.get("/depts")
def api_list_depts() -> dict:
    """列出所有部门

    对应 CLI: python -m spi.cli list-depts

    返回: {
        "spi_folder": str,
        "total": int,
        "depts": [...]
    }
    """
    from spi import get_spi_folder
    depts = _try_data("_data_list_depts")()
    return {
        "spi_folder": get_spi_folder(),
        "total": len(depts),
        "depts": depts,
    }


@router.get("/depts/{dept_id}")
def api_show_dept(dept_id: str) -> dict:
    """显示部门完整信息 + 成员

    对应 CLI: python -m spi.cli show-dept <dept_id>

    HTTP 状态码:
    - 200: dept_id 存在
    - 404: dept_id 不存在 (或 SPI_FOLDER 不支持)
    """
    data = _try_data("_data_show_dept")(dept_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Department not found: {dept_id}")
    return data


def register_routes(app) -> None:
    """注册 spi 路由到 FastAPI app

    用法 (main.py / main_pg.py):
        from spi.api import register_routes
        register_routes(app)

    行为:
    - 始终注册 6 个路由
    - SPI_FOLDER=dev 时, 路由访问 spi.dev.api._data_*
    - SPI_FOLDER=demo 时, 路由访问 spi.demo.api._data_*
    - SPI_FOLDER=xxx (无 api.py) 时, 路由返回 HTTP 404 + 错误信息
    """
    app.include_router(router)