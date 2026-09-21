from spi.fdep.data import SPI_FIND_USER_BY_ROLE_DEPT


def SPI(payload, token={}) -> list:
    if "key" in payload:
        key = payload["key"]
        return SPI_FIND_USER_BY_ROLE_DEPT.get("functions", {}).get("find_user_by_role_dept", {}).get(key, [])
    dept = payload.get("deptId") or payload.get("u_deptId") or token.get("u_deptId", "")
    role = payload.get("roleCode") or payload.get("role") or ""
    key = f"{dept}:{role}"
    table = SPI_FIND_USER_BY_ROLE_DEPT.get("functions", {}).get("find_user_by_role_dept", {})
    return table.get(key, [])


def pocketflow(payload, token={}) -> list:
    return SPI(payload, token)
