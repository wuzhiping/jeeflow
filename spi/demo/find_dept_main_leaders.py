from spi.demo.data import SPI_DEPT_MAIN_LEADERS


def SPI(payload, token={}) -> list:
    """按 dept_id 返回部门分管领导映射（修复 §41）"""
    dept_id = str(payload.get("dept_id") or payload.get("u_deptId") or payload.get("deptId") or "").strip() if isinstance(payload, dict) else str(payload).strip()
    return SPI_DEPT_MAIN_LEADERS.get(dept_id, ["director"])


def pocketflow(payload, token={}) -> list:
    return SPI(payload, token)
