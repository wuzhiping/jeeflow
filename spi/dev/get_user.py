"""get_user · 按 uid 取单用户 (派生自 USERS.json + DEPTS.json)
重构 v6 · 2026-11-17 · 本地包导入 (符合 SPEC §3.4 零父依赖)
"""
from .data import SPI_USERS, SPI_DEPT_MAIN_LEADERS

# DEPTS.json 的 leader 字段已直接给出 dept_name 的 parent_dept_id
# 但 get_user 需要 dept_name, 所以从 DEPT_MAIN_LEADERS 派生 (dept_id → dept_name 需扩展)

_DEPT_NAMES = {
    "D01": "研发部",
    "D02": "前端组",
    "D03": "后端组",
    "D04": "架构组",
    "D99": "总经办",
}


def SPI(payload, token={}) -> dict:
    uid = payload["uid"]
    info = SPI_USERS.get(uid, {"name": "用户" + uid, "post": "工程师"})
    dept_id = info.get("deptId", "D01")
    return {
        "userId": uid,
        "realName": info["name"],
        "deptId": dept_id,
        "deptName": _DEPT_NAMES.get(dept_id, "默认部"),
        "postId": info.get("level", "P5"),
        "postName": info.get("post", "工程师"),
    }


def pocketflow(payload, token={}) -> dict:
    return SPI(payload, token)
