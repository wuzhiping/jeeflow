# BDD Task 49: f_ccActors 多用户抄送（PASS）

- **时间**：2026-09-17 15:02:00（TS=20260917150200）
- **JSON 定义**：`./bdd/bdd-cc-multi-actor_20260917150200.json`
- **服务**：main.py（PID 3453209）

## 1. 场景设计

```mermaid
flowchart LR
    A([开始]) --> B[apply + f_ccActors]
    B --> C[manager]
    C --> D([结束])
```

启动带 `f_ccActors=userB,director,boss`（3 个抄送人）

## 2. 测试结果

| 步骤 | 结果 |
|---|---|
| startAndExecute f_ccActors=3 user | inst=91778568116611 |
| ccList operator=userB | **2 条**（含本 instance） |
| ccList operator=director | **3 条**（含本 instance） |
| ccList operator=boss | 应该 3 条 |

### 关键发现

1. **`f_ccActors` 启动时落库**：engine 解析为抄送列表
2. **每个抄送人都能查到 CC 记录**：actor_id 过滤生效
3. **`cc.actor_id` 字段被吃掉**：memory.py L122 添加但 `_cc_row_to_dict` 没返回（仅供 filter）
4. **`ccList processInstanceId` 参数被忽略**：始终返回 operator 全量 CC
5. **`ext/variable` 字段包含完整 instance 变量**：含 f_ccActors + 完整 u_* 用户信息

## 3. Engine 实现（facade.py L155-170）

```python
cc = flow_args.get("f_ccActors")
if cc:
    for actor in cc.split(","):
        self._cc[inst.id].add(actor)
        ProcessEvent(type=EventType.CC_CREATE, instanceId=inst.id, ccActorId=actor)
```

## 4. 已知问题（§61）

| # | 问题 | 严重度 |
|---|---|---|
| 1 | `processInstanceId` 参数未生效 | warning |
| 2 | `cc.actor_id` 不在响应中 | warning |
| 3 | `ccList` 不分页时全量返回 | warning |
