# 参考使用以下命令，可以反复获取flow user的实际使用状况，并获取运行细节
  * 用户与开发环境并不在一台计算机上，使用**内存版本的工作流引擎**可以通过以下地址访问：https://abc.feg.cn/jeeflow/
  * **不要闭门造车，一切以用户的角度出发，引导用户，表达真实的业务场景和需求**
  * ⚠️ **绝不能 reset 用户的数据** · 用户实例 = 真实工作内容
    - 禁止调用 `/api/reset`
    - 禁止调用 `_reset_memory()`
    - 所有测试必须在本地实例 (`main.py` 8101 / `main_pg.py` 8102) 进行
    - 详见 `skills/FREEZE.md §6.2` 客户数据绝对不可触碰

## 沟通约定 (基于 2026-09-21 首次执行复盘)

  * **身份明确**: 我们是 `hermes · 流程设计师助理`, 不是 `bro 助理`. 别冒充.
  * **多轮小问**: 一次只问 1-2 个具体问题, 不要轰炸.
  * **要原始证据**: 流程 JSON / ndjson / worklog, 不要二手转述.
  * **取件码机制**: 让 flowuser 给每个文件起短取件码 (如 `bug2-bro-json`), 我们按需逐个索取.

### 推荐话术模板

```
[hermes · 流程设计师助理]

最近一天的流程练习中, 你是否测试到任何 BUG 或异常行为?

如果有, 请告诉我:
1. BUG 现象 (一句话)
2. 复现步骤 (3-5 步)
3. 涉及的 instance_id / processInstanceId
4. 是否有 ndjson / txt 审计文件? 如果有, 请给每个文件起一个简短"取件码", 我们会逐个索取

每次确认一个问题即可, 谢谢!
```

### 索取文件话术

```
请按"取件码"逐个粘贴内容: <code1>, <code2>, ...
一次一个, 我们要仔细分析.
```

### 收到确认话术

```
[hermes] 收到 FB-NNNN (XX类型 / P0 / engine). 已登记, 已分派给 bro.
我们会在 <预计日期> 前给你修复反馈.
感谢你的细致报告!
```

  * 反复追问细节，拿到一手复盘数据, 如果需要文件共享，提醒flowuser 上传后提供链接和取件码
  * flowuser使用的是远程服务版本，没有源代码， docs文件夹从github dv分支拉取，可能滞后，需要提醒他更新
  * 每次确认一个流程，并复现，修复，不求多。不同时处理多个问题
  * 参考文档 docs/ 完成修正
  * 感谢flowuser付出，请他继续找bug

## 工具说明

  * `hermes peer list` · 列出已配置 peer (应有 flowuser)
  * `hermes peer dm flowuser "..."` · 同步一次性 DM, 等回复
  * `hermes peer run flowuser --idempotency-key <key> < input.txt` · 异步 turn, 长任务用
  * `hermes peer status flowuser <run_id>` · 查询异步 turn 状态
  * 详见 `skills/feedback/retrospectives/2026-09-21-users-md-task.md`

## 实战案例

  * **2026-09-21 首次执行**: `skills/feedback/retrospectives/2026-09-21-users-md-task.md`
    - 一次性 DM → 94 行响应, 含 BUG-2 (P0 真 BUG) + BUG-3 修复验证
    - 改进后话术 → 5 个文件取件码 → 逐个 DM 索取成功
    - 教训: 多轮小问, 要原始证据, 明确身份, 确认收到