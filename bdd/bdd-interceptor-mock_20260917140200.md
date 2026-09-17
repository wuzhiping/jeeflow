# BDD Task 24: Mock 拦截器验证 _fire_post（PASS）

- **时间**：2026-09-17 14:02:00（TS=20260917140200）
- **JSON 定义**：`./bdd/bdd-interceptor-mock_20260917140200.json`
- **服务**：main.py（PID 3435402，新 MockAuditInterceptor 注册后）
- **修改文件**：`./main.py`（加 MockAuditInterceptor + interceptor_registry）

## 1. 场景设计

| 节点 | 流转 |
|---|---|
| start → apply → leader_review → end | 简单串行 |

**关键改动**：流程顶层 `postInterceptors: "com.example.MockAuditInterceptor"`

## 2. main.py 修改

```python
class MockAuditInterceptor(FlowInterceptor):
    """定义级拦截器：每次 pre/post_handle 写一条到 /tmp/jee-mock-audit.log"""
    def __init__(self, name="com.example.MockAuditInterceptor"):
        self._name = name
    @property
    def order(self): return 0
    async def pre_handle(self, node, instance) -> bool:
        with open("/tmp/jee-mock-audit.log", "a") as f:
            f.write(f"PRE  {self._name} node={node.id} inst={instance.id}\n")
        return True
    async def post_handle(self, node, instance) -> None:
        with open("/tmp/jee-mock-audit.log", "a") as f:
            f.write(f"POST {self._name} node={node.id} inst={instance.id} state={instance.state}\n")

_ic_registry = {
    "com.example.MockAuditInterceptor": MockAuditInterceptor(),
}
engine.set_extensions(EngineExtensions(registry=_registry, interceptor_registry=_ic_registry))
```

## 3. 测试结果

### 流程

```
start → apply (user1) → leader_review (leader) → end
```

### Audit log 实际输出

```
POST com.example.MockAuditInterceptor node=apply inst=91774357299391 state=10
POST com.example.MockAuditInterceptor node=leader_review inst=91774357299391 state=10
PRE  com.example.MockAuditInterceptor node=end inst=91774357299391
POST com.example.MockAuditInterceptor node=end inst=91774357299391 state=20
```

**全部 PASS** ✅

## 4. 关键发现

1. **postInterceptors 必须放流程顶层**（`{"postInterceptors": "com.example.X"}`），节点级 properties.postInterceptors **不生效**（§34 已记录）
2. **`_fire_post` 触发时机**：每个节点 execute 完成后（含 end 节点），调一次
3. **`_fire_pre` 触发时机**：进入下一个节点前（含 end 节点），但 end 节点前 _fire_pre
4. **end 节点无 pre**：engine.py:351 _fire_post → _execute_node(包含 pre+execute)
5. **interceptor_registry 注册名**：`register(name="com.example.X", instance=X())`
6. **未注册的拦截器**：`raise ValueError(f"postInterceptors 声明的拦截器未注册: {name}")`（engine.py:528）

## 5. 文档改进

- docs/flow.md §6 增强：interceptor 注册流程示例 + Mock 示例
- docs/known-issues.md §34 验证：节点级 postInterceptors 不生效，仅顶层生效

## 6. 后续

- Task 25: 嵌套多层 decision + 自定义变量
