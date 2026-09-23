from .data import SPI_DEPT_LEADERS


def SPI(payload, token={}) -> list:
    """按 dept_id 返回部门领导映射（修复 §38/§41）"""
    dept_id = str(payload.get("dept_id") or payload.get("u_deptId") or payload.get("deptId") or "").strip() if isinstance(payload, dict) else str(payload).strip()
    return SPI_DEPT_LEADERS.get(dept_id, ["leader"])


def pocketflow(payload, token={}) -> list:
    return SPI(payload, token)
