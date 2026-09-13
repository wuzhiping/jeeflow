from typing import Optional
from jeeflow.model import UserInfo
from jeeflow.spi import OrgUserProvider

# 四端（Java/Go/Python/Node）统一同一套 8 个具名用户，切换后端不再"换人"
DEMO_USERS = {
    "user1": ("张三", "工程师"),
    "userA": ("孙倩", "工程师"),
    "userB": ("周明", "工程师"),
    "userC": ("吴婷", "工程师"),
    "leader": ("李四", "组长"),
    "manager": ("王五", "经理"),
    "director": ("赵六", "总监"),
    "boss": ("钱七", "总经理"),
}

# 四端统一同一套 4 个角色（与 assignment-handler 流程的角色码对齐）
DEMO_ROLES = {
    "engineer": "工程师",
    "leader": "组长",
    "manager": "经理",
    "director": "总监",
}

# 四端统一同一套字典项（请假类型 / 流程类型）：{value,label}[] 形态，宿主按 code 拉取
DEMO_DICTS = {
    "wf_leave_type": [
        {"value": "annual", "label": "年假"},
        {"value": "sick", "label": "病假"},
        {"value": "personal", "label": "事假"},
    ],
    "wf_process_type": [
        {"value": "oa", "label": "OA"},
        {"value": "hr", "label": "人事"},
        {"value": "finance", "label": "财务"},
    ],
}

def demo_user_map(uid: str) -> dict:
    real_name, post_name = DEMO_USERS.get(uid, ("用户" + uid, "工程师"))
    return {"userId": uid, "realName": real_name, "deptId": "D01", "deptName": "研发部",
            "postId": "P01", "postName": post_name}

class SimpleUserProvider:
    async def get_user(self, uid: str) -> Optional[UserInfo]:
        real_name, post_name = DEMO_USERS.get(uid, ("用户" + uid, "工程师"))
        return UserInfo(userId=uid, realName=real_name, deptId="D01", deptName="研发部", postId="P01", postName=post_name)

class DemoOrgUserProvider(OrgUserProvider):
    """组织维度取人（部门领导/分管领导/角色），扁平演示组织结构"""
    async def find_dept_leaders(self, dept_id: str) -> list:
        return ["leader"]
    async def find_dept_main_leaders(self, dept_id: str) -> list:
        return ["manager"]
    async def find_by_role(self, role_code: str) -> list:
        return {"leader": ["leader"], "manager": ["manager"],
                "director": ["director"], "boss": ["boss"]}.get(role_code, [])

def demo_user_search(query: dict):
    """在 8 个演示用户内分页检索（candidatePage 依赖）；m_* 条件值按关键字包含匹配"""
    keywords = [str(v).strip().lower() for k, v in query.items()
                if k.startswith("m_") and str(v).strip()]
    all_rows = []
    for uid, (real_name, _) in DEMO_USERS.items():
        if not keywords or all(kw in uid.lower() or kw in real_name.lower() for kw in keywords):
            all_rows.append(demo_user_map(uid))
    try:
        page_num = max(1, int(query.get("pageNum", 1)))
        page_size = max(1, int(query.get("pageSize", 10)))
    except (TypeError, ValueError):
        page_num, page_size = 1, 10
    start = min((page_num - 1) * page_size, len(all_rows))
    return all_rows[start:start + page_size], len(all_rows)