from spi.fdep.data import SPI_DEPT_LEADERS


def SPI(payload, token={}) -> list:
    dept_id = str(payload.get("dept_id") or payload.get("u_deptId") or payload.get("deptId") or "").strip() if isinstance(payload, dict) else str(payload).strip()
    return SPI_DEPT_LEADERS.get(dept_id, ["dev05"])


def pocketflow(payload, token={}) -> list:
    return SPI(payload, token)
