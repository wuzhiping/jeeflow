import os
import sys
# 优先使用本地 vendor/jeeflow（项目内嵌）
_VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

from typing import Optional
from jeeflow.model import UserInfo
from jeeflow.spi import OrgUserProvider

from importlib import reload, import_module

_SPI_FOLDER = os.environ.get("SPI_FOLDER", "dev")
_data_mod = import_module(f"spi.{_SPI_FOLDER}.data")
SPI_USERS = _data_mod.SPI_USERS
SPI_ROLES = _data_mod.SPI_ROLES
SPI_DICTS = _data_mod.SPI_DICTS


def get_spi_folder() -> str:
    """获取当前 SPI 实现包名"""
    return _SPI_FOLDER


def set_spi_folder(folder: str) -> None:
    """运行时切换 SPI 实现（issues/110）。切换后 SPI_USERS/SPI_ROLES/SPI_DICTS 同步更新。
    调用方需确保业务侧无残留对旧实现数据的引用，否则可能读到不一致状态。"""
    global _SPI_FOLDER, _data_mod, SPI_USERS, SPI_ROLES, SPI_DICTS
    _SPI_FOLDER = folder
    new_data_mod = import_module(f"spi.{folder}.data")
    reload(new_data_mod)
    _data_mod = new_data_mod
    SPI_USERS = _data_mod.SPI_USERS
    SPI_ROLES = _data_mod.SPI_ROLES
    SPI_DICTS = _data_mod.SPI_DICTS


# 兼容旧 API（部分代码可能引用 SPI_FOLDER）
SPI_FOLDER = property(lambda self: _SPI_FOLDER) if False else _SPI_FOLDER


def SPI(func, payload, token={}) -> dict:
    """SPI dispatcher：路由到 spi.<SPI_FOLDER>.<func>.pocketflow"""
    sopfile = "spi." + _SPI_FOLDER + "." + func

    # FIX-BDD-T1 (2026-09-17)：reload data 模块保证 JSON 热更新生效
    reload(_data_mod)
    agt = import_module(sopfile)
    reload(agt)

    return agt.pocketflow(payload, token)


class SimpleUserProvider:
    async def get_user(self, uid: str) -> Optional[UserInfo]:
        return UserInfo(**SPI(func="get_user", payload={"uid": uid}))


class SpiOrgUserProvider(OrgUserProvider):
    """组织维度取人（部门领导/分管领导/角色），扁平演示组织结构"""

    async def find_dept_leaders(self, dept_id: str) -> list:
        return SPI(func="find_dept_leaders", payload={"dept_id": dept_id})

    async def find_dept_main_leaders(self, dept_id: str) -> list:
        return SPI(func="find_dept_main_leaders", payload={"dept_id": dept_id})

    async def find_by_role(self, role_code: str) -> list:
        return SPI(func="find_by_role", payload={"role_code": role_code})


def spi_user_search(query: dict):
    """在当前实现的用户表内分页检索（candidatePage 依赖）；m_* 条件值按关键字包含匹配"""
    result = SPI(func="user_search", payload=query)
    return result["rows"], result["total"]
