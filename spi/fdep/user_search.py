from spi.fdep.data import SPI_USERS
from spi.fdep.get_user import SPI as get_user_impl

_DEPT_NAME = {"T01": "前端组", "T02": "架构组"}


def SPI(payload, token={}) -> dict:
    keywords = [str(v).strip().lower() for k, v in payload.items()
                if k.startswith("m_") and str(v).strip()]
    all_rows = []
    for uid in SPI_USERS.keys():
        row = get_user_impl({"uid": uid})
        real_name = row["realName"]
        if not keywords or all(kw in uid.lower() or kw in real_name.lower() for kw in keywords):
            all_rows.append(row)
    try:
        page_num = max(1, int(payload.get("pageNum", 1)))
        page_size = max(1, int(payload.get("pageSize", 10)))
    except (TypeError, ValueError):
        page_num, page_size = 1, 10
    start = min((page_num - 1) * page_size, len(all_rows))
    return {"rows": all_rows[start:start + page_size], "total": len(all_rows)}


def pocketflow(payload, token={}) -> dict:
    return SPI(payload, token)
