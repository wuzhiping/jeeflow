# TDD 工作目录约定

本目录是流程 JSON 的 **WIP（work-in-progress）** 落地处。每次新增 / 修改流程，
必须按 AGENTS.md §3.2 的 TDD 五步走，**不要**直接把 JSON 写到 `./flows/`。

## 目录用途

- `./tdd/<name>.json` — 当前会话要开发 / 改动的流程 JSON（设计中、测试中）
- `./flows/<name>.json` — 通过测试的稳定样例，对外可作为 fork 模板

## 文件命名

- 用小写字母、数字、`-` 分隔，不带 `.bak` / `.old` 后缀
- 命名应能直接表达业务场景，例如 `leave-3day-parallel.json`、`expense-multi-approve.json`
- 与最终晋升到 `./flows/` 的文件名保持一致（晋升即 `cp`）

## 生命周期

```
设计 Agent ──► ./tdd/<name>.json ──► 测试 Agent 部署 / 启动 / 跑通
                                     │
                                     ├─ 失败 → 在 <name>.json 内调整，重跑
                                     │
                                     └─ 稳定 ──► cp 到 ./flows/<name>.json
                                                │
                                                ▼
                                  ./tdd/test_<name>_<YYYYMMDDHHMMSS>.md
                                  （必写，顶部标"已晋升"）
```

## 文件命名

- JSON：`./tdd/<name>.json`，`<name>` 用小写字母、数字、`-` 分隔
- 测试日志：`./tdd/test_<name>_<YYYYMMDDHHMMSS>.md`
  - 时间戳格式 `YYYYMMDDHHMMSS`（例：`20260915143052`）
  - 本地时区，文件创建时 `date +%Y%m%d%H%M%S` 生成
  - 同一次开发的多次回归会留下多份日志，靠时间戳排序追溯

## 与 AGENTS.md 的关系

- §3.2 step 5：JSON 必须落 `./tdd/<key>.json`
- §3.2 step 8：测试通过后写 `./tdd/test_<key>_<YYYYMMDDHHMMSS>.md`
- §3.2 step 9：若发现新字段语义，更新 `./docs/flow.md`
- §3.2 step 11：稳定后 `cp` 到 `./flows/<key>.json`（可选晋升）

## 文件生命周期对照

| 文件 | 创建时机 | 命运 |
| --- | --- | --- |
| `./tdd/<key>.json` | §3.2 step 5 | 调整 → 重测；稳定后 cp 到 `./flows/<key>.json` |
| `./tdd/test_<key>_<YYYYMMDDHHMMSS>.md` | §3.2 step 8 | 永远保留（含失败记录 / 校验结论 / 晋升标记） |
| `./flows/<key>.json` | §3.2 step 11 | 晋升后的稳定样例，可作为 fork 模板 |

## 注意事项

- 本目录下的 JSON 可能是不稳定版本，**不可作为 fork 模板**
- 真正可作为模板的样例只看 `./flows/*.json`
- 测试失败时不要立即删除 JSON 与 test 文档，应保留以供回归

---

## 测试脚本索引与使用

本目录下 `*.py` 为测试基建脚本，**仅在当前会话维护**，不晋升到 `./flows/`，不写盘进度摘要。所有脚本依赖 `requests`，已在项目根 `./venv/` 内可用，无需安装。

| 脚本 | 用途 | 用法 |
| --- | --- | --- |
| `./tdd/validate_flow.py` | JSON schema 校验（防 `]`/`}` 截断）+ 节点/边拓扑检查 | `python ./tdd/validate_flow.py <flow.json> [<flow.json> ...]` |
| `./tdd/regression_runner.py` | 参数化回归（processDefineId × submitType 矩阵）+ 输出 JSON 报告 | `python ./tdd/regression_runner.py --define 145 --cases 1,2,3,5,6,20` |

### validate_flow.py 检查项

- JSON 可解析（避免末尾 `]`/`}` 缺失）
- 顶层含 `name` / `nodes` / `edges`
- 每个节点 `id` 唯一 + `type` ∈ {`snaker:start`, `snaker:end`, `snaker:task`, `snaker:decision`, `snaker:fork`, `snaker:join`, `snaker:custom`}
- 每条边 `sourceNodeId` / `targetNodeId` 在 nodes 中存在
- 节点拓扑：`snaker:start` 入度 0；`snaker:end` 出度 0
- decision 出边可含 `properties.expr`（非 decision 出边若有 expr 仅警告）

### regression_runner.py 用法

参数化起批 + execute 回归：

```bash
python ./tdd/regression_runner.py \
    --define <processDefineId> \
    --cases <comma-separated submitType list> \
    [--operator user1] [--assignee user2] \
    [--base http://localhost:8101]
```

每个 case 跑：

1. `POST /api/reset` 重置环境
2. `POST /wf/processInstance/startAndExecute`（submitType=1）
3. `POST /wf/processInstance/execute` × N（每个 submitType 一次）
4. `POST /wf/processInstance/detail` 校验终态 `state==7` 或 `state==45`/`state==10`（按 §7a 路由矩阵）

报告落 `./tdd/regression_<define>_<YYYYMMDDHHMMSS>.json`，含每个 case 的：

- `submitType`
- `processInstanceId`
- `actualState`
- `expectedState`
- `pass: bool`
- `elapsedMs`

> 端口默认 `8101`，端点路径严格按 `./main.py:180` 注册的 `/wf/{action:path}` 单入口；端点名称来自 `./docs/actions.md` §1-§2 已登记清单。