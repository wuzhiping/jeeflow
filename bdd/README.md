# BDD 目录使用约定

本目录存放流程设计 + 测试报告（BDD 模式）。每次会话产出 1 个独立 JSON 定义 + 1 个 .md 报告。

## 文件命名规范

```
bdd-<场景名>_<YYYYMMDDHHMMSS>.json    # 流程定义
bdd-<场景名>_<YYYYMMDDHHMMSS>.md     # 测试报告
bdd-<场景名>_<YYYYMMDDHHMMSS>-patch-<N>.{json,md}   # 修正版本
```

- **场景名**：kebab-case，描述业务场景（如 `expense-ratio-tiered`、`candidate-pool-take`）
- **时间戳**：统一一次任务的 `YYYYMMDDHHMMSS`；同任务修正用 `patch-1` / `patch-2`
- **每次完全独立任务**：新时间戳

## 报告模板（标准格式）

```markdown
# BDD Task <N>: <场景标题>（<PASS/PARTIAL/FAIL>）

- **时间**：<YYYY-MM-DD HH:MM:SS>（TS=<YYYYMMDDHHMMSS>）
- **JSON 定义**：`./bdd/bdd-<场景名>_<TS>.json`
- **服务**：main.py / main_pg.py（PID <N>）

## 1. 场景设计

<业务背景 + mermaid 流程图>

## 2. 测试结果

| Case | 操作 | state | 当前节点 actor | 结果 |

## 3. 关键发现

1. <新引擎行为>
2. <已知约束>

## 4. 文档改进

- docs/known-issues.md §N 新增：<标题>
- docs/flow.md §X 增强：<内容>

## 5. 后续

<下一个任务方向或已知问题>
```

## runner.py 工具

`./bdd/runner.py` 提供 `print_state` helper，用于 BDD 测试中查看实例状态：

```python
from runner import print_state

# 打印实例 + 任务 + 状态
print_state(instance_id)
# 打印实例 + 任务 + 历史节点
print_state(instance_id, 'history')
```

**输出格式**：
```
state=10 active=1
  ACTIVE: leader_review actors=['leader']
  DONE:   apply state=20 actors=['user1']
history: ['apply', 'leader_review', 'end']
current: None
```

## statics.json 累积统计

`./bdd/statics.json` 是 BDD 任务的元数据汇总，**每次新增任务必须更新**：

```json
{
  "tasks": [
    {
      "id": "Task <N>",
      "name": "<场景名>",
      "time": "<YYYYMMDDHHMMSS>",
      "node_types": ["task", "decision", "join"],
      "features": ["<特性 1>", "<特性 2>"],
      "errors": ["§<N> <标题>"]
    }
  ],
  "statistics": {
    "by_node_type": {...},
    "by_feature_category": {...},
    "by_severity": {"critical": [...], "warning": [...]},
    "by_fix_status": {"fixed": [...], "documented_only": [...]}
  }
}
```

### 更新步骤

1. 新增 task 条目到 `tasks` 数组
2. 重新生成 `statistics` 维度：

```python
./venv/bin/python3 -c "
import json
from collections import Counter
d = json.load(open('./bdd/statics.json'))
# ... 见 §3 维度计算
"
```

3. 校验 ID 完整性：检查 `tasks` 数组与历史时间戳无缺失

## BDD 工作流

### Step 1: 读 BDD.md

BDD.md 关键约束：
- 不能修改 main.py 只能给出修复建议（**例外**：用户授权修复时可改）
- 流程用户/角色数据**必须从 API 获取**（`/api/users` + `/api/roles`），不得捏造
- 已知 bug 不要复现（参考 `./docs/known-issues.md`）
- json + 报告写到 `./bdd/`
- **必须在 statics.json 中累积统计**

### Step 2: 获取真实数据

```bash
curl -s -X POST http://localhost:8101/api/users \
  -H "Content-Type: application/json" -d '{}'
curl -s -X POST http://localhost:8101/api/roles \
  -H "Content-Type: application/json" -d '{}'
curl -s -X POST http://localhost:8101/api/dicts \
  -H "Content-Type: application/json" -d '{}'
```

### Step 3: 设计 + 部署 + 测试

1. 写 `./bdd/bdd-<场景>_<TS>.json`
2. `/api/reset`（清空状态）
3. `processDesign/save` + `processDesign/deploy`
4. `processInstance/startAndExecute` 启动
5. `processTask/execute` 推进
6. `processInstance/detail` 核验

### Step 4: 写报告 + docs 复盘

1. 写 `./bdd/bdd-<场景>_<TS>.md`（按报告模板）
2. 新发现的引擎行为/约束 → `./docs/known-issues.md §N`
3. 新发现的字段语义 → `./docs/flow.md §X`
4. 修复（如授权）→ main.py + 同步 main_pg.py
5. 更新 `./bdd/statics.json`

## 与 tdd/ 目录区别

| 维度 | bdd/ | tdd/ |
|---|---|---|
| 目的 | BDD 场景驱动测试 | TDD 单元/集成测试 |
| 文件 | `<场景>_<TS>.{json,md}` | `<key>.{json,md}` |
| 命名 | kebab-case + 时间戳 | 流程 key |
| 维护 | 累积统计 | 流程晋升到 flows/ |

**约定**：bdd/ 是会话级累积统计；tdd/ 是流程设计 WIP。
