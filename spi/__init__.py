from typing import Optional
from jeeflow.model import UserInfo
from jeeflow.spi import OrgUserProvider

from importlib import reload , import_module
import os

SPI_FOLDER = os.environ.get("SPI_FOLDER", "demo")  # SPI 数据子包名；envvar SPI_FOLDER 可在 import spi 之前覆盖

_data_mod = import_module(f"spi.{SPI_FOLDER}.data")
SPI_USERS = _data_mod.SPI_USERS
SPI_ROLES = _data_mod.SPI_ROLES
SPI_DICTS = _data_mod.SPI_DICTS

def SPI(func,payload,token= {}) -> dict:
    sopfile = "spi."+ SPI_FOLDER +"."+func

    agt = import_module(sopfile)
    reload(agt)

    result = agt.pocketflow(payload, token)
    return result

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
    """在 8 个演示用户内分页检索（candidatePage 依赖）；m_* 条件值按关键字包含匹配"""
    result = SPI(func="user_search", payload=query)
    return result["rows"], result["total"]