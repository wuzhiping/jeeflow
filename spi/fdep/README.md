# spi.dev SPI 实现包

模拟"研发协作"场景的开发团队 SPI（Service Provider Interface）实现。

与 `spi.demo` 区别：
- 部门维度：`T01 前端组` / `T02 架构组`（vs demo 的 `D01-D99`）
- 用户数：6 个（vs demo 9 个）
- 角色：developer / tester / architect / tech_lead + 2 SPI 角色（vs demo 75 个）
- 字典：bug 严重度 + 变更类型（vs demo 假期 + 流程类型）

适用于演示代码评审、Bug 修复、部署审批等研发流程。

---

## 切换方式

```bash
export SPI_FOLDER=dev
python main.py
```

或在 Python 入口：

```python
import os
os.environ["SPI_FOLDER"] = "dev"
import spi
```

---

## 数据集

### `DEV_USERS.json` —— 6 个研发用户

| uid | name | post | dept |
|-----|------|------|------|
| dev01 | 陈伟 | 前端工程师 | T01 前端组 |
| dev02 | 黄丽 | 后端工程师 | T01 前端组 |
| dev03 | 马涛 | 测试工程师 | T01 前端组 |
| dev04 | 徐静 | 架构师 | T02 架构组 |
| dev05 | 孙磊 | 技术经理 | T02 架构组 |
| dev06 | 吴芳 | CTO | T02 架构组 |

### `DEV_ROLES.json` —— 4 个核心角色

| role_code | role_name |
|-----------|-----------|
| developer | 开发工程师 |
| tester | 测试工程师 |
| architect | 架构师 |
| tech_lead | 技术负责人 |

### `DEV_DICTS.json` —— 2 组字典

- `dev_bug_severity` → P0/P1/P2/P3（致命/严重/一般/建议）
- `dev_change_type` → feature/bugfix/refactor（新功能/缺陷修复/重构）

### `DEV_ROLE_TO_USERS.json` —— 角色-用户映射（含 SPI 节点角色）

| role_code | uids |
|-----------|------|
| developer | [dev01, dev02] |
| tester | [dev03] |
| architect | [dev04] |
| tech_lead | [dev05] |
| cto | [dev06] |
| code_review | [dev04, dev05] |
| deploy_approve | [dev05, dev06] |

### `DEV_DEPT_LEADERS.json` / `DEV_DEPT_MAIN_LEADERS.json`

| dept_id | dept_name | leaders | main_leaders |
|---------|-----------|---------|--------------|
| T01 | 前端组 | [dev04] | [dev05] |
| T02 | 架构组 | [dev05] | [dev06] |

### `DEV_FIND_USER_BY_ROLE_DEPT.json`

| key | uids |
|-----|------|
| T01:developer | [dev01, dev02] |
| T01:tester | [dev03] |
| T02:architect | [dev04] |
| T02:tech_lead | [dev05] |

---

## 函数清单

每个 SPI 函数对应 `spi/dev/<func>.py` 一个文件，所有函数遵循 [SPEC.md §3.3](../SPEC.md) 规范。

| 函数 | 用途 |
|------|------|
| `get_user` | 按 uid 取单用户（含 deptId/postId 完整字段） |
| `user_map` | 全量用户表 |
| `user_search` | 多关键字 AND 分页检索 |
| `roles` | 角色列表 |
| `dicts` | 字典全集 |
| `find_by_role` | 按角色取人 |
| `find_dept_leaders` | 按部门取部门领导 |
| `find_dept_main_leaders` | 按部门取分管领导 |
| `find_user_by_role_dept` | 按部门+角色组合取人 |

---

## 演示场景示例

```bash
export SPI_FOLDER=dev
python main.py
```

发起一个"代码评审"流程：dev01 提交 → code_review（dev04+dev05 并行）→ tech_lead（dev05）→ deploy_approve（dev05+dev06 任一）→ 完成。

节点配置参考：

```json
{
  "id": "code_review",
  "type": "snaker:task",
  "properties": {
    "performType": 1,
    "countersignType": "PARALLEL",
    "assignmentHandler": "com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$TaskRoleAssigneeHandler"
  }
}
```

引擎会查 `SPI_ROLE_TO_USERS["code_review"]` → `[dev04, dev05]`，并行创建会签任务。

---

## 扩展建议

- 真实接入：把 `DEV_USERS.json` 替换为数据库查询（修改 `data.py` 暴露 dict 即可）
- 多租户：实现 `get_tenant_users(tenant_id)` 并加入 dispatcher 函数清单
- 自定义角色：往 `DEV_ROLE_TO_USERS.json` 添加业务角色（如 `release_manager: [dev05]`）
