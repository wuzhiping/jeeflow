"""spi/demo API 数据接口 (重构 v26)

约定 (参见 SPEC §8): 必须导出以下 _data_* 函数 (与 cli.py 共享签名).
api.py 必须暴露与 cli.py 完全相同的 6 个 _data_* 函数.

本文件是 cli.py 的薄包装, 保持接口一致.
"""
from .cli import (
    _data_verify,
    _data_status,
    _data_list_users,
    _data_show_user,
    _data_list_depts,
    _data_show_dept,
)