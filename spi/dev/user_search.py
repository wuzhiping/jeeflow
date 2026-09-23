from .data import SPI_USERS


def SPI(payload, token={}) -> dict:
    keywords = [str(v).strip().lower() for k, v in payload.items()
                if k.startswith("m_") and str(v).strip()]
    all_rows = []
    for uid, info in SPI_USERS.items():
        real_name = info["name"]
        post_name = info["post"]
        if not keywords or all(kw in uid.lower() or kw in real_name.lower() for kw in keywords):
            all_rows.append({"userId": uid, "realName": real_name, "deptId": "D01", "deptName": "研发部",
                             "postId": "P01", "postName": post_name})
    try:
        page_num = max(1, int(payload.get("pageNum", 1)))
        page_size = max(1, int(payload.get("pageSize", 10)))
    except (TypeError, ValueError):
        page_num, page_size = 1, 10
    start = min((page_num - 1) * page_size, len(all_rows))
    return {"rows": all_rows[start:start + page_size], "total": len(all_rows)}


def pocketflow(payload, token={}) -> dict:
    return SPI(payload, token)