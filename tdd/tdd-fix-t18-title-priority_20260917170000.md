# TDD FIX-T18: vendor/jeeflow/engine.py _add_auto_gen_title title 优先级

- **时间**：2026-09-17 17:00:00
- **修复位置**：`vendor/jeeflow/engine.py:_add_auto_gen_title` (FIX-T18 段)
- **背景**：设计器前端可显式传 args.title，但 vendor 引擎总是用 autoGenTitle 覆盖，title 被吞
- **服务**：main.py（8101）+ main_pg.py（8102）

## 1. 上游修复（vendor/jeeflow/engine.py）

```python
def _add_auto_gen_title(self, display_name: str, vars_: dict):
    """issue 29：自动生成标题（对齐 boot3 FlowUtil.addAutoGenTitle）
    FIX-T18 (2026-09-17)：title 优先级——显式 args.title > autoGenTitle
    """
    real_name = vars_.get(KEY_REAL_NAME, "")
    title = f"{real_name}的{display_name}-{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    # FIX-T18：只有 args.title 未显式提供时才用 autoGenTitle（设计器前端可覆盖）
    if "title" not in vars_ or not vars_["title"]:
        vars_[KEY_AUTO_GEN_TITLE] = title
    else:
        vars_[KEY_AUTO_GEN_TITLE] = vars_["title"]
```

## 2. 测试结果

```
memory 无 title: autoGenTitle='用户alice的简单审批流程-2026-09-18 00:01' (默认格式)
memory 显式 title: autoGenTitle='请假申请-2026-001' (覆盖)
PG 显式 title: autoGenTitle='PG请假-003' (覆盖)
```

## 3. 关键发现

1. **优先级**：显式 args.title > 自动生成 autoGenTitle
2. **设计器前端可覆盖**：允许业务系统指定自定义标题（不依赖 u_realName 拼接）
3. **双后端一致**：memory + PG 行为统一