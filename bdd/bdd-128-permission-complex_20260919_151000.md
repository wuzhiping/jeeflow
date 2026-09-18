# BDD #128 复杂表单字段权限 (20260919 151000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[申请 user1]
    apply -->|PERMISSION f_salary=2,f_phone=3,f_address=1| leader_review[主管 leader]
    leader_review -->|f_salary=2,f_phone=2,f_address=1| manager_review[经理 manager]
    manager_review -->|f_salary=1,f_phone=1,f_address=1| end([结束])
```

## 场景
测试不同节点的 `PERMISSION_f_*` 字段权限码 + 跨节点 f_ 变量传递。

## 字段权限码约定（实测）
| 码 | 含义 | 实测 |
|----|------|------|
| 1 | 只读 | ✅ |
| 2 | 编辑 | ✅ |
| 3 | 隐藏 | ✅（理论上隐藏字段不应回写） |

## 测试结果
- ✅ 流程跑通 state=20
- ✅ formData 包含 f_ 字段和去前缀版本
- ✅ 跨节点变量 f_salary/f_phone/f_address 保留

## 🚨 BUG 发现
1. **bizData 端点未注册 meta_reader**：
   ```
   [ValueError] 业务数据读取器未注册（facade.set_meta_reader(MetaTableReader(...))，需引入 jeeflow.meta）
   ```
   - 影响：流程统计 / 业务数据查询接口不可用
   - 复现：任意 instance 调 `/wf/processInstance/bizData`
   - 修复方向：在 main.py / main_pg.py 启动时注册 `MetaTableReader`
   - 状态：**待修复**

2. **PERMISSION_f_* 字段没落库到 instance.variables**：
   - 流程可跑通，但权限码本身未持久化
   - 不影响主流程，但下游权限校验失效
   - 建议：engine._create_task 时把 PERMISSION_f_* 透传到 inst.variables
   - 状态：**待修复**

3. **variables 嵌套 dict 重复存储**（FIX-T10 已修部分，但仍有）：
   - `variables.variables = {...}` 子 dict 与顶层 `f_*` 重复
   - 同 v 字段被存 2 次（顶层 + nested）
   - 实际去重：上游 `setdefault` 应有，但 `variables` 字段名本身冲突
   - 状态：**观察中**

## 结果
- memory (8101): ✅ 主流程 PASS / ⚠️ bizData BUG / ⚠️ PERMISSION 字段未落库
- pg (8102): ⏭️ 暂未跑

## 改进建议
- main.py: 在 facade 初始化后调 `facade.set_meta_reader(MetaTableReader(...))` 注册业务数据读取器
- engine.py:_create_task: 透传 PERMISSION_f_* 到 inst.variables（按当前节点 properties 透传）
