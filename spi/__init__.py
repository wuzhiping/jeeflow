import os
import sys
# 优先使用本地 vendor/jeeflow（项目内嵌）
_VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

from typing import Optional
from jeeflow.model import UserInfo
from jeeflow.spi import OrgUserProvider

from importlib import reload , import_module

SPI_FOLDER = os.environ.get("SPI_FOLDER", "demo")  # SPI 数据子包名；envvar SPI_FOLDER 可在 import spi 之前覆盖

_data_mod = import_module(f"spi.{SPI_FOLDER}.data")
SPI_USERS = _data_mod.SPI_USERS
SPI_ROLES = _data_mod.SPI_ROLES
SPI_DICTS = _data_mod.SPI_DICTS

def SPI(func,payload,token= {}) -> dict:
    sopfile = "spi."+ SPI_FOLDER +"."+func

    # FIX-BDD-T1 (2026-09-17)：reload data 模块保证 JSON 热更新生效
    # 原版只 reload func 模块，但 SPI_ROLE_TO_USERS / SPI_USERS / SPI_DICTS
    # 在 spi.demo.data 顶层 import 时一次性绑定，修改 JSON 后内存值不刷新
    reload(_data_mod)
    # func 模块依赖 data 顶层常量；同步 reload 让 pocketflow 重新拿 data 引用
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