# BDD-DEV-023 用户反馈 FB-0016 handler 错误消息误导修复 (20260922)

## 触发

用户在 https://abc.feg.cn/jeeflow/healthz 启动 `flows/11-assignment-handler.json` 报：
```
[ValueError] 节点[task1] handler 'com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler'
SPI 角色匹配为空（检查 role_code）
```

defineId=27（remote state pdId 27），用户反馈 "SPI 数据层问题, 引擎无法修"。

## 实测结论

SPI dev 完整：
- 13 users (含 u_ceo/u_cto/u_rd_dir/u_arch/u_fe_lead/u_fe_senior/u_fe_eng/u_be_lead/u_be_senior1/u_be_senior2/u_be_eng/u_qa_lead/u_qa_eng)
- 8 roles (ceo/cto/rd_director/tech_lead/architect/senior_engineer/engineer/qa_engineer)
- `qa_engineer` → [u_qa_lead, u_qa_eng]

**真实根因**：FormFieldAssigneeHandler 期望 `variables.f_task1`，调用方未传 → handler 返回 `[]` → 引擎抛"统一"错误"handler SPI 角色匹配为空"。**用户误读**为"SPI 缺数据"。

## 修复 (FIX-T117)

`vendor/jeeflow/engine.py:_create_task:760-798` 按 `_last_resolve_meta.source` 给具体错误：

```python
# 修复后
if not actors:
    meta = self._last_resolve_meta or {}
    src = meta.get("source", "unknown")
    if src == "form_field":
        raise ValueError(
            f"节点[{node.id}] FormFieldAssigneeHandler 返回空：未找到 variables['f_{node.id}']"
            f" 或 variables['{node.id}']。请在 startAndExecute.variables 中传入"
            f" f_{node.id}=<userId[,userId,...]>（如 f_{node.id}='u_qa_lead,u_be_lead'）"
        )
    elif src == "task_role":
        rc = meta.get("roleCode", "")
        raise ValueError(
            f"节点[{node.id}] TaskRoleAssigneeHandler 返回空：roleCode='{rc}' 在 SPI 角色表中无用户。"
            f" 请检查 (1) properties.roleCode='{rc}' 是否正确；"
            f"(2) SPI 角色表 role_to_users['{rc}'] 是否已配置用户"
        )
    elif src == "dept_leader":
        raise ValueError(
            f"节点[{node.id}] DeptLeaderAssignmentHandler 返回空：发起人(u_userId)无部门主管。"
            f" 请检查 (1) variables.u_userId 在 SPI 用户表中存在；"
            f"(2) 该用户所在部门的 dept_leaders 已配置主管"
        )
    elif src == "operator":
        raise ValueError(
            f"节点[{node.id}] OperatorAssignmentHandler 返回空：操作人为空。"
            f" 请检查 POST /wf/processTask/execute 的 operator 参数"
        )
    else:
        raise ValueError(f"节点[{node.id}]无法解析任何处理人：assignee/handler/SPI 角色均未匹配")
```

`vendor/jeeflow/engine.py:_resolve_actors:917-925` 记录 meta：

```python
if h:
    self._last_resolve_meta = {
        "source": self._handler_source_key(handler_name),
        "handlerName": handler_name,
        "roleCode": node.properties.get("roleCode", "")
    }
    actors = await h.assign(node, inst, operator)
    if not actors:
        return actors  # _create_task 通过 _last_resolve_meta 给具体错误
    return actors
```

`main_common.py:install_resolve_actors_wrapper:444-449` 移除冗余 raise：

```python
# 旧代码（删除）
# raise ValueError(f"节点[{node.id}] handler '{handler_name}' SPI 角色匹配为空（检查 role_code）")

# 新行为：只 log warning，让 engine 内部 _create_task 通过 _last_resolve_meta 给具体错误
```

## 复测

### 本地 8101

| 场景 | handler | 输入 | 旧错误 | 新错误 |
|------|---------|------|--------|--------|
| 1 | FormField | 缺 `f_task1` | "SPI 角色匹配为空 (检查 role_code)" | "FormFieldAssigneeHandler 返回空：未找到 variables['f_task1']" |
| 2 | TaskRole | roleCode="no_such_role" | (旧统一错误) | "TaskRoleAssigneeHandler 返回空：roleCode='no_such_role' 在 SPI 角色表中无用户" |
| 3 | DeptLeader | operator=u_be_eng | n/a | 解析为 u_be_lead ✅ |
| 4 | 11-assignment-handler + f_task1 | `f_task1="u_qa_lead"` | (成功) | state=20 ✅ |

### 远程 abc.feg.cn/jeeflow (用户服务器)

⚠️ **fix 还未部署**。远程服务器 vendor/jeeflow/engine.py 仍是 FIX-T117 之前的版本，错误信息仍是旧的 "SPI 角色匹配为空"。

### 全 19 流程回归

19/19 flows state=20 ✅，零回归。

## 部署到 abc.feg.cn

由于无法直接 ssh 到 abc.feg.cn（无 password auth，仅 publickey），需要通过 git push 触发：

```bash
# 本机:
cd /opt/jupyter/src/RD/projects/jeeFlow
./push.sh   # 自动 commit + push 到 github
# abc.feg.cn 服务器:
ssh root@abc.feg.cn 'cd /opt/jupyter/src/RD/projects/jeeFlow && git pull && docker compose restart jeeflow'
# 或:
ssh root@abc.feg.cn 'cd /app && git pull && pkill -f "uvicorn main:app" && nohup uv run main.py &'
```

FIX-T117 修改的文件：
- `vendor/jeeflow/engine.py` (主修复)
- `main_common.py` (移除 wrapper 冗余 raise)

## 关联文档

- `docs/known-issues.md §122` (FIX-T117 详细)
- `vendor/jeeflow/engine.py:760-798, 917-925` (修复点)
- `main_common.py:444-449` (wrapper 清理)
- 远程服务器：https://abc.feg.cn/jeeflow/healthz (待 git pull + restart)