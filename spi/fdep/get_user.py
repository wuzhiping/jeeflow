from spi.fdep.data import SPI_USERS


DEPT_MAP = {
    "dev01": "T01", "dev02": "T01", "dev03": "T01",
    "dev04": "T02", "dev05": "T02", "dev06": "T02",
}


def SPI(payload, token={}) -> dict:
    uid = payload["uid"]
    info = SPI_USERS.get(uid, {"name": "用户" + uid, "post": "工程师"})
    dept_id = DEPT_MAP.get(uid, "T01")
    dept_name = {"T01": "前端组", "T02": "架构组"}.get(dept_id, "默认组")
    post_to_id = {
        "前端工程师": "J01", "后端工程师": "J02", "测试工程师": "J03",
        "架构师": "J04", "技术经理": "J05", "CTO": "J06"
    }
    post_id = post_to_id.get(info["post"], "J01")
    return {"userId": uid, "realName": info["name"], "deptId": dept_id, "deptName": dept_name,
            "postId": post_id, "postName": info["post"]}


def pocketflow(payload, token={}) -> dict:
    return SPI(payload, token)
