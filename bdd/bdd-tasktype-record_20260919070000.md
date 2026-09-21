# BDD 任务 #107: taskType=2 RECORD 节点测试

## 目标
验证 taskType=2 (RECORD) 节点的 properties 是否被引擎识别并落库。

## 流程
apply → record1(taskType=2) → end

## 实测
1. processDesign/deploy → processDefineId=18
2. processInstance/startAndExecute → instId=91843330824193
3. 查 todoList: record1 节点的 taskType=**0** (期望 2)
4. processTask/execute record1 → 0 成功
5. processInstance/detail: record1.taskType=**0** (期望 2)

## 结论
❌ **BUG：engine._create_task 不读 node.properties.taskType**

## 根因
vendor/jeeflow/engine.py:402-446 _create_task 只传 form/performType 给 inst.create_task
```python
nt = inst.create_task(self._next_id(), node.id, ..., form, now)  # 无 taskType
```
model.py:183-200 create_task 工厂方法也没有 taskType 参数。
TaskType 枚举定义在 model.py:79-84，但全程未被引用。

## 影响
- taskType=0/1/2 三个枚举值**全部无效**
- 不能区分"主审/副审/记录"
- 前端 taskType 字段显示永远 0

## 修复建议（FIX-T30）
1. `inst.create_task` 加 `task_type: int = 0` 参数
2. `engine._create_task` 读 `node.properties.taskType` 传入
3. `memory.py:201` JDBC save_task 也透传
