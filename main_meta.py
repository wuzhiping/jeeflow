"""Memory-mode MetaTableReader — 内存后端业务数据读取器

main.py (memory) 启动时用本模块的 build_meta_reader() 注册到 facade。
PG 后端用 vendor/jeeflow/meta.py:MetaTableReader(JdbcTableReader, JsonMetaProvider)。

Memory 模式无实际业务表，回显走 inst.variables 内部 f_* 字段（轻量闭环）。
"""
from typing import Any, Optional


class MemoryMetaReader:
    """无 JdbcTableReader 的轻量 meta_reader — 直接从 inst.variables 读 f_* 字段。

    行为契约（async 协程，facade 端 await）：
    - read_by_process_instance(table_name, instance_id) → {f_xxx: value, ...}
    - 不存在时返回 None
    """

    def __init__(self, repo):
        self._repo = repo

    async def read_by_process_instance(self, table_name: str, process_instance_id: Any) -> Optional[dict[str, Any]]:
        inst = await self._repo.find_instance_by_id(process_instance_id)
        if inst is None:
            return None
        result: dict[str, Any] = {}
        for k, v in (inst.variables or {}).items():
            if k.startswith("f_"):
                result[k] = v
        return result or None


def build_meta_reader(repo) -> MemoryMetaReader:
    """main.py 启动时调：facade.set_meta_reader(build_meta_reader(repo))"""
    return MemoryMetaReader(repo)
