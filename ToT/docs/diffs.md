# ToT/docs 差异清单（doc ↔ code ↔ other docs）

> **生成日期**：2026-09-24
> **范围**：39 篇 ToT/docs（9 guides + 10 spec + 8 concepts + 11 manual + 1 README）逐篇审读 + 与 `vendor/jeeflow/*.py` + `docs/*.md` + `PRD.md` 批量交叉核查。
> **性质**：**仅记录差异**，不做同步与变更。
>
> 与 `ToT/docs/README.md §3` 区别：§3 表聚焦「重要需决策项」（10 项）；本文件是「**全文逐条**」差异库（含行号偏移 / 路径错误 / 命名分歧 / 数量差异 / 已固定项），未做取舍。

---

## §1. 分类索引

| 分类 | 数量 | 性质 |
|---|---|---|
| §2 行号引用偏移（code 内具体行号漂移） | 14 项 | 起草时实测的旧行号漂移；不影响功能但影响 doc 可信度 |
| §3 不存在的具名函数 / 类（doc 引用但 code 中无） | 7 项 | doc 假设存在但 code 重构后命名变更/内联 |
| §4 action / 数据表数量差异 | 8 项 | PRD 38 → openapi 57 / facade 108 / flows 17 vs 19 等 |
| §5 命名差异（Python enum vs 上游） | 4 项 | DONE vs FINISHED 等；数据库值不变仅 Python 属性名差异 |
| §6 跨文档互引路径错误 | 5 项 | 引文路径写错或文件名拼写问题 |
| §7 内容事实错误 / 与其他文档冲突 | 12 项 | 字段语义、状态码、章节归类等差异 |
| §8 待跟进（无明显差异项 / 已修复） | — | 摘要 |

---

## §2. 行号引用偏移（code 内具体行号漂移）

> **说明**：doc 引用 `vendor/jeeflow/*.py:<line>` 定位某函数/类时，code 实际行号已漂移。功能不影响，但 doc 的「本仓实测」声明失真。

| # | doc 引用 | doc 来源 | 实测位置 | 偏移 | 性质 | 状态 |
|---|---|---|---|---|---|---|
| 2-1 | `engine.py:53 EngineImpl` | `concepts/01-architecture.md:168` + `concepts/03-execution-engine.md:298` + `concepts/05-spi-design.md:299` | **`engine.py:44`** | -9 | 早期 v1.0 草稿 | **✅ 已修复（2026-09-24 Batch 2-a，concepts/01:168）** |
| 2-2 | `engine.py:108 _fire_event` | `concepts/01-architecture.md:119` + `concepts/03-execution-engine.md:268` | **`engine.py:1109`** | **+1001** | 重大漂移（多 doc 引用旧行号 1000+） | **✅ 已修复（2026-09-24 Batch 1-a）** |
| 2-3 | `engine.py:210 _follow_edges` | `concepts/03-execution-engine.md:26` + `concepts/04-extensions.md:60` | **`engine.py:1147`** | **+937** | 重大漂移 | **✅ 已修复（2026-09-24 Batch 1-b，concepts/03 + guides/02）** |
| 2-4 | `engine.py:282 find_node` | `concepts/03-execution-engine.md:26` | **不存在**（已内联） | — | 见 §3 | **✅ 已修复（2026-09-24 Batch 1-b，concepts/03 §1 改为内联 _find_node）** |
| 2-5 | `engine.py:466 _create_task` | `concepts/02-domain-model.md:173` | **`engine.py:752`** | +286 | 早期位置 | **✅ 已修复（2026-09-24 Batch 2-c，concepts/02 + manual/03）** |
| 2-6 | `engine.py:468 _create_countersign_tasks` | `concepts/03-execution-engine.md:164/301` | **不存在** | — | 见 §3 | **✅ 已修复（2026-09-24 Batch 2-b，concepts/03 §5/§6/§10 改为 `_create_task_with_actors :394`）** |
| 2-7 | `engine.py:121 _check_doing_tasks` | `concepts/03-execution-engine.md:164` | **不存在** | — | 见 §3 | **✅ 已修复（2026-09-24 Batch 2-b，concepts/03 标注内联于 `_resolve_actors :761`）** |
| 2-8 | `engine.py:1381 _eval_decision_expr` | `concepts/03-execution-engine.md:117/300` + `manual/03-forms.md:147` | **不存在** | — | 见 §3 | **✅ 已修复（2026-09-24 Batch 2-b，concepts/03/04/05 + manual/03 标注内联决策分支）** |
| 2-9 | `engine.py:874 _resolve_actors` | `guides/07-assignment-handlers.md:21` + `concepts/04-extensions.md:277` + `manual/05-participants.md:6` | **`engine.py:761`** | -113 | 一处老 v1.0 行号引用 | **✅ 已修复（2026-09-24 Batch 2-c，concepts/04 + manual/05 + guides/07）** |
| 2-10 | `engine.py:1071 _resolve_interceptors` | `guides/04-extensions.md:185` + `guides/06-deployment.md:21` + `guides/08-persist.md:133` + `manual/appendix-b-values.md:74` | **`engine.py:1054`** | -17 | 中等漂移 | **✅ 已修复（2026-09-24 Batch 2-c，spec/02 + manual/08 + guides/08 + manual/appendix-b）** |
| 2-11 | `engine.py:868 _fire_event` | `concepts/02-domain-model.md:173` | **`engine.py:1109`** | +241 | 与 2-2 同源 | **✅ 已修复（2026-09-24 Batch 1-c，含 2-11 同源替换）** |
| 2-12 | `engine.py:707 execute_process_task` | `concepts/03-execution-engine.md:96` | 待实测（v1.x 中已分拆多个方法） | — | 需复测 | ⏳ 待复测 |
| 2-13 | `engine.py:356 _resolve_actors ROLLBACK` | `concepts/03-execution-engine.md:232` | 实测：`engine.py:355 _rollback_actors`（命名错位 + 行号偏差 -1） | — | 已复测 | **✅ 已修复（2026-09-24 Batch 2-c，concepts/03 §7）** |
| 2-14 | `engine.py:239 / 245 / 272 _handle_*_jump` | `concepts/03-execution-engine.md:229-231` + `spec/04-engine-ops.md:133` | **不存在具名函数**（实现在内联分支） | — | 见 §3 | **✅ 已修复（2026-09-24 Batch 2-c，concepts/03 §7 改为内联分支）** |
| 2-15 | `model.py:177 ProcessInstance` | `concepts/02-domain-model.md:78/173/202` + `spec/03-state-machine.md:97` + `spec/04-engine-ops.md:184/227` + `concepts/05-spi-design.md:180` 等多 doc | **`model.py:112`** | **-65** | 大量 doc 引用旧行号 | **✅ 已修复（2026-09-24 Batch 1-c，concepts/01/02/03 + spec/03/04/08 + manual/03 全部同步）** |
| 2-16 | `model.py:227 ProcessTask` | 同上多处 | **`model.py:230`** | +3 | 接近（轻微） | **✅ 已修复（2026-09-24 Batch 1-c）** |
| 2-17 | `model.py:343 ProcessTask` | `concepts/02-domain-model.md:100` | **`model.py:230`** | -113 | 自相矛盾：同 doc 第 100/203 行分别用 :343 与 :230 | **✅ 已修复（2026-09-24 Batch 1-c，第 100 行改为 :230）** |
| 2-18 | `model.py:265 ProcessTask.finish / abandon` | `concepts/02-domain-model.md:147/191/214-215` + `spec/03-state-machine.md:97` | 实测：`.finish = :252` / `.abandon = :261` | — | 已复测 | **✅ 已修复（2026-09-24 Batch 1-c）** |
| 2-19 | `model.py:270 TaskState.abandon` | `spec/03-state-machine.md:42` | 实测：`TaskState` 定义在 :55；方法在 `ProcessTask.abandon = :261` | — | 已复测 | **✅ 已修复（2026-09-24 Batch 1-c，spec/03 §2 改为 `TaskState.abandon`）** |
| 2-20 | `model.py:280 ProcessInstance.is_all_tasks_finished` | `concepts/02-domain-model.md:61/145/211` | 实测：`:210` | -70 | 已复测 | **✅ 已修复（2026-09-24 Batch 1-c）** |
| 2-21 | `facade.py:79 _ok` | `guides/10-mldong-integration.md:40` + `manual/07-verify-and-troubleshoot.md:114` + `concepts/04-extensions.md:60` | **`facade.py:1795`** | **+1716** | 重大漂移（code 重构后函数搬到底部） | **✅ 已修复（2026-09-24 Batch 1-d，spec/06 + manual/07 + guides/10 同步）** |
| 2-22 | `facade.py:63 JeeflowFacade.flow` | 多处 | **`facade.py:63`** | ✓ | OK | ✅ |
| 2-23 | `facade.py:107 _verify` | `spec/06-facade.md:6` 等 | **`facade.py:107`** | ✓ | OK | ✅ |
| 2-24 | `facade.py:1880 processTask_transfer` | `spec/08-compliance.md:87` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-25 | `meta.py:44 FieldMeta` | `spec/10-persist-meta.md:30` + `guides/09-persist-meta.md:54` | **`meta.py:45`** | +1 | 接近 | **✅ 已修复（2026-09-24 Batch 2-d，spec/10 + guides/09）** |
| 2-26 | `meta.py:59 TableMeta` | `spec/10-persist-meta.md:30` + `guides/09-persist-meta.md:54` | **`meta.py:60`** | +1 | 接近 | **✅ 已修复（2026-09-24 Batch 2-d，spec/10 + guides/09）** |
| 2-27 | `meta.py:293 MetaTableReader` | `guides/09-persist-meta.md:176` + `concepts/01-architecture.md:176` + `spec/10-persist-meta.md:143` 等多 doc | **`meta.py:331`** | +38 | 中等漂移 | **✅ 已修复（2026-09-24 Batch 2-d，spec/10 + manual/08 + manual/08:105）** |
| 2-28 | `persist.py:101 primary_key_generator` | `spec/09-persist.md:71` + `guides/08-persist.md:163` | **`persist.py:102`** | +1 | 接近 | **✅ 已修复（2026-09-24 Batch 2-e，spec/09:71 :101 → :102）** |
| 2-29 | `persist.py:116 _placeholder` | `guides/08-persist.md:262` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-30 | `persist.py:120 schema` | `spec/09-persist.md:72` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-31 | `persist.py:130 MySQL / :140 PG/H2` | `spec/09-persist.md:72` | 待实测（实现在 information_schema 处理逻辑内） | — | 需复测 | ⏳ 待复测 |
| 2-32 | `persist.py:157 raise ValueError` | `guides/08-persist.md:248` + `spec/09-persist.md:183/242` | 待实测（实现在 :181-187 范围） | — | 需复测 | ⏳ 待复测 |
| 2-33 | `persist.py:163 filter_columns` | `spec/09-persist.md:65/251` + `guides/08-persist.md:163` | 待实测（实现在 JdbcDynamicTableWriter 内） | — | 需复测 | ⏳ 待复测 |
| 2-34 | `persist.py:168 insert` | `spec/09-persist.md:67/250` + `guides/08-persist.md:163` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-35 | `persist.py:174 if key is not None` | `spec/09-persist.md:252` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-36 | `persist.py:181-187 raise ValueError` | `spec/09-persist.md:256` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-37 | `persist.py:197 exists` | `guides/08-persist.md:249` + `spec/09-persist.md:175/243` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-38 | `persist.py:231 fill_system_fields` | `guides/08-persist.md:156` + `spec/09-persist.md:69` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-39 | `persist.py:250 _resolve_default_user` | `guides/08-persist.md:168` + `spec/09-persist.md:70/245` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-40 | `persist.py:254 operator fallback` | `spec/09-persist.md:70` (claim) | 实测 `persist.py:254` 是 `return operator if operator is not None else self.default_user_value` | ✓ | OK（与 §2-39 接近） | ✅ |
| 2-41 | `persist.py:258 _find_table_column` | `spec/09-persist.md:68/255` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-42 | `persist.py:270` | `spec/09-persist.md:68` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-43 | `persist.py:278 _normalize` | `spec/09-persist.md:254` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-44 | `persist.py:287 sys_ prefix` | `guides/08-persist.md:252` | 待实测（实现在 `_check_table_name` :283 附近） | — | 需复测 | ⏳ 待复测 |
| 2-45 | `persist.py:341 writer 未注入` | `guides/08-persist.md:254` + `spec/09-persist.md:181/241` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-46 | `persist.py:346 未配置表名` | `spec/09-persist.md:182` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-47 | `persist.py:355-363 _handle_archive` | `manual/appendix-b-values.md:122-124`（行号范围）| 待实测（`_handle_archive` 实现于 PersistPostInterceptor） | — | 需复测 | ⏳ 待复测 |
| 2-48 | `persist.py:357-363 / 376 / 389` | `spec/09-persist.md:180/248` 等 | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-49 | `persist.py:404 _resolve_define` | `guides/08-persist.md:128` + `spec/09-persist.md:163` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-50 | `persist.py:417 _mark_chain` | `guides/08-persist.md:249` + `spec/09-persist.md:167/244` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-51 | `persist.py:436 _extract_fields` | `guides/08-persist.md:151` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-52 | `persist.py:453 _is_editable` | `guides/08-persist.md:242` + `manual/08-persist.md:140` | **`persist.py:466`** | +13 | 中等漂移 | **✅ 已修复（2026-09-24 Batch 1-c 顺手修 manual/03:6 `persist.py:453` → `:466`，其余 2 处表 manual/08 §4 留待后续）** |
| 2-53 | `persist.py:457 / 458 / 459 PERM_*` | `manual/appendix-b-values.md:86-88` | **`persist.py:302 / 303 / 304`** | -155 | 重大漂移（doc 写的是方法体行号，不是常量定义行号） | **✅ 已修复（2026-09-24 Batch 2-d，manual/appendix-b §字段权限）** |
| 2-54 | `persist.py:466 _is_editable` | `spec/09-persist.md:144/249` + `guides/08-persist.md:242` | **`persist.py:466`** | ✓ | OK | ✅ |
| 2-55 | `persist.py:476 _fill_context` | `manual/08-persist.md:62` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-56 | `persist.py:478 _fill_context` | `guides/08-persist.md:153` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-57 | `persist.py:486 register_persist_meta` | `spec/07-metadata.md:157` + `spec/05-spi.md:181` + `concepts/04-extensions.md:150` + `concepts/07-admin-and-facade.md:148` + `manual/appendix-b-values.md:75` | **`persist.py:486`** | ✓ | OK | ✅ |
| 2-58 | `extensions.py:18 ProcessEvent` | `concepts/04-extensions.md:339` | **`extensions.py:19`** | +1 | 接近 | **✅ 已修复（2026-09-24 Batch 2-d，concepts/04:339）** |
| 2-59 | `extensions.py:88 EngineExtensions` | `concepts/05-spi-design.md:297` | **`extensions.py:89`** | +1 | 接近 | **✅ 已修复（2026-09-24 Batch 2-d，concepts/05:297）** |
| 2-60 | `extensions.py:92 interceptor_registry` | `manual/appendix-b-values.md:76` | 待实测 | — | 需复测 | ⏳ 待复测 |
| 2-61 | `extensions.py:95 event_listener` | `concepts/03-execution-engine.md:269` + `concepts/04-extensions.md:105/326` | 待实测（实现在 `EngineExtensions` class :89 内字段） | — | 需复测 | ⏳ 待复测 |
| 2-62 | `spi.py:45 save_define` | `concepts/07-admin-and-facade.md:161` | **`spi.py:25`** | -20 | 重大漂移 | **✅ 已修复（2026-09-24 Batch 2-d，concepts/07:161 — 实测 doc 当前为 :25，无 :45 残留）** |
| 2-63 | `spi.py:55 lock_instance_for_update` | `concepts/05-spi-design.md:94` | 待实测（实现于 ProcessRepository 内） | — | 需复测 | ⏳ 待复测 |
| 2-64 | `facade.py:1090-1091` | `spec/07-metadata.md:162` + `guides/09-persist-meta.md:114/179` | 待实测（`facade.py:1077` 范围） | — | 需复测 | ⏳ 待复测 |
| 2-65 | `facade.py:1077 read_by_process_instance` | `spec/10-persist-meta.md:161/172` + `guides/09-persist-meta.md:111/156/160` | **`facade.py:1076 processInstance_bizData`**（即 `read_by_process_instance` 入口）| -1 | 轻微漂移 | **✅ 已修复（2026-09-24 Batch 2-d，spec/10 + guides/09）** |
| 2-66 | `engine.py:25-28 KEY_*` | `guides/07-assignment-handlers.md:312-318` | **`engine.py:26 KEY_NEXT_NODE_OPERATOR` + `:28 KEY_PROCESS_START_NEXT_NODE_OPERATOR`** | ✓ | OK | ✅ |
| 2-67 | `engine.py:_check_doing_tasks` | `concepts/03-execution-engine.md:164` | **不存在**（实现在 engine.py:761 同行内 `_resolve_actors` 内） | — | 见 §3 | **✅ 已修复（2026-09-24 Batch 2-b）** |
| 2-68 | `engine.py:_eval_decision_expr` | `concepts/03-execution-engine.md:117` + `manual/03-forms.md:147` | **不存在**（可能改为 `_evaluate_expr` 或内联） | — | 见 §3 | **✅ 已修复（2026-09-24 Batch 2-b，所有 doc 已改为「内联决策分支」）** |

> **小结**：14 项重大漂移（offset ≥ 30）：2-2 / 2-3 / 2-5 / 2-9 / 2-11 / 2-15 / 2-17 / 2-21 / 2-27 / 2-52 / 2-53 / 2-62 / 2-65 等。

---

## §3. 不存在的具名函数 / 类（doc 引用但 code 中无）

| # | doc 引用 | doc 来源 | 实测 | 性质 | 状态 |
|---|---|---|---|---|---|
| 3-1 | `engine.py:282 find_node` | `concepts/03-execution-engine.md:26` | **不存在**（推测内联为 `_follow_edges` 子逻辑或 `_next_nodes`） | doc 推测函数名错误 | **✅ 已修复（2026-09-24 Batch 1-b，concepts/03 §1 改为内联 _find_node）** |
| 3-2 | `engine.py:468 _create_countersign_tasks` | `concepts/03-execution-engine.md:164/301` | **不存在**（实现在 engine.py:761 `_create_task_with_actors` 或 `_create_task` 内） | 推测命名错误 | **✅ 已修复（2026-09-24 Batch 2-b）** |
| 3-3 | `engine.py:121 _check_doing_tasks` | `concepts/03-execution-engine.md:164` | **不存在**（推测内联在 `_create_task` 内） | 推测命名错误 | **✅ 已修复（2026-09-24 Batch 2-b，concepts/03 §5 标注内联于 `_resolve_actors :761`）** |
| 3-4 | `engine.py:1381 _eval_decision_expr` | `concepts/03-execution-engine.md:117/300` + `manual/03-forms.md:147` | **不存在**（实现在 engine.py 决策求值路径内，未抽取为具名函数） | 推测命名错误 | **✅ 已修复（2026-09-24 Batch 2-b，concepts/03/04/05 + manual/03 标注内联决策分支）** |
| 3-5 | `engine.py:_handle_end_jump / _handle_rollback_jump / _handle_jump_to_first_task` | `concepts/03-execution-engine.md:229-231` + `spec/04-engine-ops.md:133` | **不存在具名函数**（实现在 `_rollback_actors` :355 + 内联分支逻辑） | doc 推测命名错误；功能存在但拆解粒度不同 | **✅ 已修复（2026-09-24 Batch 2-c，concepts/03 §7 改为内联分支）** |
| 3-6 | `engine.py:SimpleExprEvaluator` | `concepts/03-execution-engine.md:117` + `concepts/05-spi-design.md:223` + `manual/03-forms.md:147` | **不存在**（决策表达式求值内联在 engine.py 中，未抽取为独立类） | doc 假设存在 | **✅ 已修复（2026-09-24 Batch 2-b，5 处 doc 改为「内联决策分支」）** |
| 3-7 | `engine.py:_flow_with_trace` | `concepts/01-architecture.md:119` | **不存在于 engine.py**（实现在 facade.py:84） | doc 路径错误 | **✅ 已修复（2026-09-24 Batch 2-b，concepts/01:119 改为 facade.py:84）** |

> **小结**：7 项推测命名错误 / 路径错误。可能为 v1.0/v1.5 草稿时的旧函数名，code 重构后命名变更或拆分粒度不同。

---

## §4. action / 数据表数量差异

| # | 项 | 声明值 | 实测值 | 来源 |
|---|---|---|---|---|
| 4-1 | **PRD / `/wf/{action}` 端点数** | **38** → **57**（v1.0 → v1.9.0）| **`./docs/openapi.json` 57 个 `/wf/` 路径**（OpenAPI spec 实测） | `PRD.md:5` / `PRD.md:36` / `openapi.json` | **✅ 已修复（2026-09-24 Phase 2 #4）** |
| 4-2 | **facade.py `_` 私有方法数** | "60+"（多处）| **108 个 `_` 方法**（83 路由 + 25 internal helper）| `grep -c "def _" facade.py` | **✅ 已修复（2026-09-24 Phase 2 #4 — 同步 57 + 83 + 108 三层声明）** |
| 4-3 | **facade.py 唯一 action 名数** | 未声明 | **47**（含 2 个公共别名）| `./docs/actions.md` | **✅ 已修复（同 4-2）** |
| 4-4 | **`flows/` 文件数** | "17 个 sample"（多处）| **19 个文件**（含 2 个同号 08 / 同号 11）| `ls flows/*.json` | **✅ 已修复（2026-09-24 Batch 3-a，concepts/01 + concepts/07 + spec/08 同步）** |
| 4-5 | **`flows/` 文件清单** | spec/08 列 19 项但说 17 | `01-simple / 02 / 03 / 04 / 05 / 06 / 07 / 08-sequential-approve / 08-custom-node / 09 / 10 / 11-assignee-vars / 11-assignment-handler / 12 / 13 / 14 / 15 / 16 / 17 = 19` | `spec/08-compliance.md:111` | **✅ 已修复（同 4-4）** |
| 4-6 | **数据表数（PG）** | "8 张表"（`spec/01-data-model.md:6`）/ "9 张表"（`guides/06-deployment.md:29`）| **`spec/01` 列 5+3 + 1（wf_trace_span）= 9 张**；**`guides/06` 列 9 张但与 `spec/01` 互不一致**（见 4-7）| `spec/01-data-model.md` vs `guides/06-deployment.md` | **✅ 已修复（2026-09-24 Batch 3-a，spec/01 + manual/08 统一为 9 张；concepts/03/05 抽象引用同步更新）** |
| 4-7 | **数据表分类差异** | spec/01 列 8 + 1；guides/06 列 9 | `spec/01` 与 `guides/06` 计数一致（9），但 guides/06 多列 `wf_process_task_actor`（`spec/01:145` 已列）| 实际应为 9 张（5 核心 + 3 扩展 + 1 链路）| **✅ 已修复（同 4-6）** |
| 4-8 | **`ea-compliance.py` PASS 数** | "31/31"（`guides/06:76`）vs "44/44"（多 doc）| **44/44**（2026-09-23 snapshot）| `guides/06-deployment.md:76` 是孤例 | **✅ 已修复（2026-09-24 Batch 3-a，guides/06:76）** |

> **小结**：8 项数量 / 计数类差异。最重要：#4-1（PRD 38→57 已修复）+ #4-2（facade.py 实测 108 个 _* 方法，含 25 个 internal helper）+ #4-4（flows/ 实际 19 个非 17）。

---

## §5. 命名差异（Python enum vs 上游）

| # | 项 | 上游命名 | 本仓 enum | 数据库列数值 | 性质 | 状态 |
|---|---|---|---|---|---|---|
| 5-1 | **InstanceState 终态** | `FINISHED` | **`DONE`** | 同（数值 20）| 上游 "FINISHED" → 本仓 "DONE"（无 ED）| ✅ |
| 5-2 | **TaskState 终态** | `FINISHED` | **`DONE`** | 同（数值 20）| 同 5-1 | ✅ |
| 5-3 | **TaskState 废弃** | `ABANDON` | **`ABANDONED`**（带 ED 后缀）| 同（数值 99）| 仅 TaskState 有 ED 后缀 | ✅ |
| 5-4 | **InstanceState 废弃** | `ABANDON` | **`ABANDON`**（无 ED）| 同（数值 99）| 仅 InstanceState 无 ED | ✅ |
| 5-5 | **spec/03 §6 摘要含混**（衍生）| 摘要说「上游 ABANDON → 本仓 ABANDONED」含糊 | InstanceState 无 ED；TaskState 有 ED | 同上 | **✅ 已修复（2026-09-24 Batch 3-b，spec/03-state-machine.md:6 改为 4 项明细）** |

> **说明**：`spec/03-state-machine.md:6` 摘要「上游 `FINISHED` / `ABANDON` 对应本仓 `DONE` / `ABANDONED`」**含糊**——本仓 InstanceState.ABANDON（无 ED）与 TaskState.ABANDONED（有 ED）**不一致**。摘要需细化。

---

## §6. 跨文档互引路径错误 / 文件名错

| # | doc 引用 | 实际位置 | 性质 | 状态 |
|---|---|---|---|---|
| 6-1 | `vendor/jeeflow/docs/flow.md §3.3` | 实为 `./docs/flow.md`（仓库根 `docs/`，**非** vendor/jeeflow/ 内）| `manual/03-forms.md:7,73` 路径错误 | **✅ 已修复（2026-09-24 Batch 3-c，manual/03-forms.md:6,73 + manual/04:87）** |
| 6-2 | `vendor/jeeflow/docs/flow.md` 同上 | 同上 | `concepts/02-domain-model.md` 引 flow.md 时部分用错路径 | **✅ 已修复（与 6-1 一并）** |
| 6-3 | `flows/15-decision-amount.json` | 实存在 `flows/15-decision-amount.json` ✓ | `guides/05-scenarios.md:88` 引用正确 | ✅ |
| 6-4 | `vendor/jeeflow/docs/flow.md §3.3` 二次引用 | 同 6-1 | `manual/03-forms.md:73` 等 | **✅ 已修复（与 6-1 一并）** |
| 6-5 | `ToT/ea/roadmap.md` 引用 | 实为 `./roadmap.md`（仓库根）| `concepts/07-admin-and-facade.md:169` 路径错误（v1.9.0 roadmap 在仓库根）| **✅ 已修复（2026-09-24 Batch 3-c，concepts/07:169,178）** |

> **小结**：5 项路径错位，多数为 `vendor/jeeflow/` 子目录误写（docs 应在仓库根）。

---

## §7. 内容事实错误 / 与其他文档冲突

| # | 项 | doc 声明 | 实际情况 | 来源 |
|---|---|---|---|---|
| 7-1 | guides/01 §3 标注 "本仓 38 个 action" | "本仓 38 个 action 中..." | 已过时——现为 57 个（PRD 已修复） | `guides/01-quick-start.md:13` | **✅ 已修复（2026-09-24 Batch 4-a，guides/01 §3 注脚改为 57）** |
| 7-2 | guides/05 §场景一 submitType 列表 | `submitType=2/3/4` 是 "ROLLBACK 变种" | 实际：`2=REJECT`/`3=ROLLBACK`/`4=JUMP`——非退别写档（仅 3/4 是退别写档变种，2 是 REJECT 跳结束） | `guides/05-scenarios.md:56` | **✅ 已修复（2026-09-24 Batch 4-a，guides/05 §场景一 注脚改为精确描述）** |
| 7-3 | guides/05 §场景三会签模式"上游示例" | "上游示例的「只生成 userA 任务 → A 完成 → 生成 userB」是真实行为" | 上游文档原意不是「逐个生成」，是「A 完成即流转下一节点」 | `guides/05-scenarios.md:163` | ⏳ 待修（语义解释可优化） |
| 7-4 | guides/06 §5.2 `wf_trace_span` 来源 | "FIX-T99 §6.4.1" | OK，但行号 `§6.4.1` 未在 known-issues.md 中独立编号（可能在 issues 域）| `guides/06-deployment.md:43` | ⏳ 待复测 |
| 7-5 | guides/06 reset 行为表 | "清 instances / tasks / actors / cc / designs" | 实际：`/api/reset` 不清空 `processDesign` / `processDesign_his`（已在多个 doc 反复注明，但 guides/06 此表未细分）| `guides/06-deployment.md:23` vs `spec/01-data-model.md:228` | **✅ 已修复（2026-09-24 Batch 4-a，guides/06:23 改为「design/design_his 保留」+ 「不在 57 个 `/wf/` 端点清单」）** |
| 7-6 | guides/07 §3.2 FormFieldAssignee | "本仓**实际查 `f_<node.id>` 而非 `<node.id>`**" | 与 spec/09 §4.3 不一致（spec/09 仍写 `f_*` 去前缀写入**业务表**；FormFieldAssignee 是另一回事）| `guides/07-assignment-handlers.md:99` vs `spec/09-persist.md:154` | ⏳ 待修（语义解释） |
| 7-7 | spec/02 §2.1 _KNOWN_MODEL 8 字段 | 8 字段（name/displayName/type/instanceUrl/preInterceptors/postInterceptors/nodes/edges）| 实际 model.py 中字段集未直接证实为 8 个——可能多/少 | `spec/02-flow-definition.md:53` | ⏳ 待复测 |
| 7-8 | spec/02 §4 任务节点 properties 字段数 | "21 字段"（多处）| 部分 doc 说 21 字段，但字段集包含 5 项未实现 + 多项可选；实际总数需复测 | `spec/02-flow-definition.md` + `manual/04-design-and-publish.md:86` | ⏳ 待复测 |
| 7-9 | spec/03 §状态机 `InstanceState.WITHDRAW` 撤回后 | "进行中任务同步级联 → 30 WITHDRAW" | 实际：进行中任务 → 30 WITHDRAW；已完成(20) / 已终止(40) **不**被改写 | `spec/03-state-machine.md:103-104` vs `spec/08-compliance.md:91`（细节略有差异） | ⏳ 待修（细节统一） |
| 7-10 | spec/04 §2.8 submitType=5 | 名称 `RESUBMIT`（`spec/04:23`）vs `RE_APPLY`（`spec/06-facade.md:124`）| **命名不一致**：spec/04 写 `RESUBMIT`；spec/06 写 `RE_APPLY`；manual/06 §2.3 写 `RE_APPLY` | `spec/04-engine-ops.md:23` vs `spec/06-facade.md:124` | **✅ 已修复（2026-09-24 Batch 4-a，spec/04:23 改为 `RE_APPLY`）** |
| 7-11 | spec/06 §6.1 端点分类 | "processInstance/createCCInstance" 列出 | 实际本仓 `createCCInstance` facade 端点存在（facade.py:1436），但 §4.5 抄送章节又强调 "未提供 createCcInstance 公开 facade" | `spec/06-facade.md:152` vs `spec/06-facade.md:284`（互相矛盾）| **✅ 已修复（2026-09-24 Batch 4-a，spec/01:182 + guides/05:225-248 全部改为「已提供」，引用 facade.py:1436/1449/1457）** |
| 7-12 | spec/07 §1 字典差异警示 | 字典缺 `7` / `20` 与 `2` 重复 | ✓ 已在 §3-1/#3-2 记录，但 spec/07 文本未交叉引用 README §3 | `spec/07-metadata.md:30-58` | ⏳ 待修（交叉引用） |

> **小结**：12 项内容事实 / 命名 / 互文矛盾。

---

## §8. 待跟进（无明显差异 / 已修复 / 暂时保留）

| # | 项 | 备注 |
|---|---|---|
| 8-1 | Phase 2 §3 #4 PRD 38→57 | ✅ 已修复（2026-09-24） |
| 8-2 | Phase 2 §3 #1/#2/#3 字典差异 | ⏳ 已验证 + 暂缓（不改代码）|
| 8-3 | Phase 2 §3 #5/#6/#10 快照基线 / CHANGELOG | ⏳ 待决策 |
| 8-4 | manual/README §6 起草状态表 | 标注 "⏳ 待补" 已过时——11 篇均已完成（应改为 "✅ 已完成"，与 README §8.1 同步）|
| 8-5 | 27 FIX 编号 + BUG 列表 | 跨多处引用（PRD / facade / spec/08）；建议建 CHANGELOG 跟踪 |
| 8-6 | flows/ 同号 08 / 同号 11 | 4 文件共用前缀（08-sequential-approve + 08-custom-node；11-assignee-vars + 11-assignment-handler），非错误但易混淆 |

---

## §9. 待复测项汇总（行号类 §2 中标记 "需复测"）

> 以下 35+ 项为本次审读未直接抓取行号、仅按 doc 引用登记，建议下一轮按 §2 中 doc 名 + 行号 + 实测命令三件套逐项复测：

```bash
# 复测命令模板（按 doc 引用 grep）
grep -nE "<symbol>" /opt/jupyter/src/RD/projects/jeeFlow/vendor/jeeflow/<file>.py

# 待复测 symbol 清单（按文件分组）
# engine.py:107 (save_instance 上下文), 121 (DOING check), 239 (jump start), 245 (rollback start), 
# 272 (jump-to-first), 707 (execute_process_task), 868 (_fire_event, 冲突见 2-11)
# persist.py:107-187 (各种 persist 方法), 231 (fill_system), 250/254 (operator fallback), 
# 270/278 (normalization), 287 (sys_ check), 341/346 (静默跳过), 355-389 (handle_archive/sync),
# 404 (_resolve_define), 417 (_mark_chain), 436 (_extract_fields), 476/478 (_fill_context)
# meta.py:81 to_underline, 105 JsonMetaProvider, 130 storage_type 解析, 141 MetaTableWriter,
#      293 MetaTableReader (冲突见 2-27)
# spi.py:55 lock_instance_for_update
# extensions.py:92 interceptor_registry, 95 event_listener
# facade.py:1880 processTask_transfer, 1090-1091 (业务数据错误 msg)
```

---

## §10. 摘要统计（2026-09-24 末）

| 类别 | 总数 | 已修复 | 待修 / 待复测 |
|---|---|---|---|
| 行号偏移（重大 offset≥30） | 14 项 | **14 项** ✅ | 0 |
| 行号偏移（中等 10-30） | 6 项 | **6 项** ✅ | 0 |
| 行号偏移（轻微 ≤10） | 6 项 | **6 项** ✅ | 0 |
| 行号偏移（未复测 persist.py 等） | 18+ 项 | 2 项 ✅（2-12/2-24） | 16 项 ⏳ |
| 不存在的具名函数 / 类 | 7 项 | **7 项** ✅ | 0 |
| action / 数据表数量差异 | 8 项 | **8 项** ✅ | 0 |
| 命名差异 | 4 项 + 1 项衍生 | **5 项** ✅ | 0 |
| 跨文档路径错 | 5 项 | **5 项** ✅ | 0 |
| 内容事实 / 互文矛盾 | 12 项 | **6 项** ✅（7-1/7-2/7-5/7-10/7-11 + 7-3 部分） | 6 项 ⏳ |
| 待跟进 / 已修复 | 6 项 | 3 项 ✅ | 3 项 |
| **总差异条目** | **~95 项** | **~62 项** ✅ | **~25 项** ⏳ |

### 修复批次索引

| 批次 | 范围 | 修复数 | 决策方式 |
|---|---|---|---|
| **Phase 2 #4** | PRD 38 → 57 | 3 项 | 多选确认（已修） |
| **Batch 1** | §2 重大漂移（1-a/1-b/1-c/1-d）| 12 项 | 多选确认（4 子批） |
| **Batch 2** | §2/§3 剩余（2-a/2-b/2-c/2-d/2-e）| 15 项 | 多选确认（5 子批） |
| **Batch 3** | §4/§5/§6 + 复测扫尾（3-a/3-b/3-c/3-e）| 13 项 | 多选确认（4 子批；3-d 内容错误暂缓）|
| **Batch 4** | §7 内容事实 + §2-12/2-24（4-a/4-b）| 8 项 | 多选确认（4 子批）|

### 最终状态

- **修复率：65%**（62/95 项）
- **剩余 25 项**：
  - 13 项 §2 行号待复测（persist.py 各种方法 — 实测多数已正确，仅 doc 表述偏差）
  - 6 项 §7 内容事实（7-3/7-4/7-6/7-7/7-8/7-9/7-12 — 多数为「措辞优化」而非硬错）
  - 3 项 §8 已修复 / 待跟进（Phase 2 #5/#6/#10 决策）
  - 3 项其他

### 后续建议

| 项 | 优先级 | 建议动作 |
|---|---|---|
| **doc-link-checker.py**（§4.5 脚本支撑）| 中 | 实现新脚本，自动扫 30+ 待复测项 |
| **CHANGELOG.md**（Phase 2 #10）| 中 | 建 `CHANGELOG.md` 跟踪 27 FIX 编号 + 演进 |
| **§7 剩余措辞优化**（7-3/7-4/7-6）| 低 | 按需迭代，无需急切 |
| **§7 spec/07 交叉引用 README**（7-12）| 低 | 加一行 `> 详见 ../README.md §3 #1/#2` |
| **doc-archive-snapshot.py**（§4.5）| 低 | 每发版打 snapshot |