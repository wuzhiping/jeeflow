"""修复 §41 get_user 按 userId 派部门（userA→D01, userB→D02, userC→D03, leader→D01, manager→D02, director→D03, boss→D99）"""
from spi.demo.data import SPI_USERS

DEPT_MAP = {
    "user1": "D01", "userA": "D01", "userB": "D02", "userC": "D03",
    "leader": "D01", "manager": "D02", "director": "D03", "boss": "D99",
}

def SPI(payload, token={}) -> dict:
    uid = payload["uid"]
    info = SPI_USERS.get(uid, {"name": "用户" + uid, "post": "工程师"})
    dept_id = DEPT_MAP.get(uid, "D01")
    dept_name = {"D01": "研发部", "D02": "市场部", "D03": "财务部", "D99": "总经办"}.get(dept_id, "默认部")
    return {"userId": uid, "realName": info["name"], "deptId": dept_id, "deptName": dept_name,
            "postId": "P01", "postName": info["post"]}


def pocketflow(payload, token={}) -> dict:
    return SPI(payload, token)
