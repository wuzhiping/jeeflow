# TDD FIX-T17: vendor/jeeflow 空 actors raise ValueError + instance 转 ABANDON

- **时间**：2026-09-17 16:58:00
- **修复位置**：
  - `vendor/jeeflow/engine.py:_create_task` actors=[] raise ValueError
  - `vendor/jeeflow/engine.py:_create_task_with_actors` actors=[] raise ValueError（ROLLBACK 路径）
  - `vendor/jeeflow/engine.py:start_process_instance_by_id` try/except → 转 ABANDON + re-raise
  - `main.py + main_pg.py:_logged_resolve_actors` handler 未注册/SPI 匹配空 raise ValueError
- **服务**：main.py（8101）+ main_pg.py（8102）

## 1. 背景（设计缺陷）

- `engine._create_task` 当 actors=[] 时静默 return（`if not actors: return`）
- `main.py + main_pg.py:_logged_resolve_actors` handler 未注册时静默 return []
- 结果：流程在某节点卡住，instance.state=10 (DOING) 但 activeTaskList=[]
- 排查困难：用户不知道哪个节点失败、为什么

## 2. 修复内容

### engine._create_task（vendor）

```python
async def _create_task(self, node, inst, operator, vars_):
    actors = await self._resolve_actors(node, inst, operator, vars_)
    if not actors:
        raise ValueError(f"节点[{node.id}]无法解析任何处理人：assignee/handler/SPI 角色均未匹配，"
                         f"请检查 properties.assignee、assignmentHandler FQCN、SPI role_code")
    ...
```

### engine.start_process_instance_by_id try/except（vendor）

```python
start_node = _find_by_type(flow, TYPE_START)
if not start_node: raise ValueError("no start node")
try:
    for node in _follow_edges(flow, start_node.id):
        await self._execute_node(flow, inst, node, operator, vars_)
except ValueError as e:
    # FIX-T17：start 路径节点创建失败 → instance 标记 ABANDON
    from .model import InstanceState
    inst.state = InstanceState.ABANDON
    inst.updateTime = datetime.now()
    try:
        await self.repo.update_instance(inst)
    except Exception:
        pass
    raise
```

### main.py + main_pg.py _logged_resolve_actors raise

```python
async def _logged_resolve_actors(node, inst, operator, vars_):
    handler_name = node.properties.get("assignmentHandler", "")
    if handler_name and engine.ext and engine.ext.registry:
        h = engine.ext.registry.resolve_assignment(handler_name)
        if not h:
            _fix_log(...)
            raise ValueError(f"节点[{node.id}] handler FQCN='{handler_name}' 未注册")
    actors = await _orig_resolve_actors(node, inst, operator, vars_)
    if handler_name and not actors:
        _fix_log(...)
        raise ValueError(f"节点[{node.id}] handler '{handler_name}' SPI 角色匹配为空（检查 role_code）")
    return actors
```

## 3. 启动命令（vendor 优先级修复）

```bash
# 关键：用 PYTHONPATH 把 vendor 放到 sys.path 第二位（空字符串 '' 之后）
PYTHONPATH=/opt/jupyter/src/RD/projects/jeeFlow/vendor setsid nohup ./.venv/bin/python3 main.py &

# PG 后端
PYTHONPATH=/opt/jupyter/src/RD/projects/jeeFlow/vendor \
JEEFLOW_PG_DSN="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm" \
setsid nohup ./.venv/bin/python3 main_pg.py &
```

**原因**：`sys.path.insert(0, _VENDOR)` 在 `from jeeflow import ...` 之后才执行，被 site-packages 抢先；用 PYTHONPATH 让 vendor 在 sys.path[1] 优先。

## 4. 测试结果

### 错误情况（不存在 role）

```
memory 8101:
  code: 99999999
  msg: 节点[review] handler '...OrgUserAssignmentHandlers$TaskRoleAssigneeHandler' SPI 角色匹配为空（检查 role_code）

PG 8102:
  code: 99999999
  msg: 节点[review]无法解析任何处理人：assignee/handler/SPI 角色均未匹配...
```

### 正常流程（flows/01-simple.json）

```
正常流程: inst=91812559552705 (state=10 DOING)  ✅
```

## 5. 关键发现

1. **vendor 优先级**：sys.path.insert(0, _VENDOR) 不够；必须用 PYTHONPATH 把 vendor 放在 site-packages 之前
2. **空 actors 是 bug 不是特性**：raise 让上游 facade 报清晰错误
3. **ABANDON 状态**：实例从 DOING → ABANDON，便于排查（state=99）
4. **FIX-T17 vs 兼容**：正常流程（01-simple 等）仍工作，只是错误情况被捕获
