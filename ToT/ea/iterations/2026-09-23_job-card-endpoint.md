# Iteration #34 · 2026-09-23 · W43 · 新 endpoint + Work Guidance · 解决 Job Card 内容读取

> **驱动**：用户观察"SKILL.md 知道 job_card_url，但 agent 读不到内容作为工作指导"
> **核心成果**：✅ **新增 `processDefine/getJobCardContent` endpoint** + SKILL.md `## Work Guidance` 节（4 步工作流 + endpoint 规范）

---

## 1. 时间线（~20 分钟 / 3 步）

| 时段 | 工作 |
|------|------|
| 0~5 min | 需求澄清：基于 flow-id + url 读 markdown 内容（防越界）|
| 5~15 min | `vendor/jeeflow/facade.py` 加 `_processDefine_getJobCardContent` + 重启 engine + 5 测试 |
| 15~20 min | SKILL.md Tools §A 加一行 + 新增 `## Work Guidance` 节 |

---

## 2. 新 endpoint 设计

### 2.1 接口

| 项 | 值 |
|----|----|
| action | `processDefine/getJobCardContent` |
| 请求 | `{processDefineName: "<flow-id>", url: "<job_card 相对路径>"}` |
| 返回 | `{url, content, length}` |
| 安全 | url 必须以 `ToT/flows/<flow-id>/job_cards/` 开头（防越界） |
| url 后缀 | 自动补 `.md`（不强制要求） |

### 2.2 实现

```python
async def _processDefine_getJobCardContent(self, args: dict) -> dict:
    name = str(args.get("processDefineName", ""))
    url = str(args.get("url", ""))
    if not name: raise ValueError("processDefineName 必填")
    if not url: raise ValueError("url 必填")

    def_ = await self._repo.find_define_by_name(name)
    if not def_: raise ValueError(f"流程定义不存在: {name}")

    # 标准化 url
    normalized_url = url if url.endswith(".md") else url + ".md"
    expected_prefix = f"ToT/flows/{name}/job_cards/"
    if not normalized_url.startswith(expected_prefix):
        raise ValueError(f"url 不安全: {url}（应位于 {expected_prefix}）")

    # 读文件（engine cwd = 仓库根，相对路径可达）
    try:
        with open(normalized_url, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise ValueError(f"job_card 文件不存在: {normalized_url}")

    return {"url": normalized_url, "content": content, "length": len(content)}
```

---

## 3. SKILL.md Work Guidance 节

新增 `## Work Guidance · 读 Job Card 作为工作指导`（4 子节）：
- **为什么需要这个能力**：Tools §B `processTask/detail` 只给 URL 不给内容
- **工作流**：4 步（接单 → 拿 URL → 读工作指导 → 基于内容做决策）
- **endpoint 规范**：请求 / 返回 / 安全 / 后缀
- **注意事项**：必须先部署流程 / 客户 server 路径 / content 大小

### 3.1 Tools §A 同步

加新行：
| `processDefine/getJobCardContent` | 读 job_card markdown 内容（作为工作指导） | **fdep** / **invoice-approval** |

---

## 4. 测试矩阵（5 测试全过）

| Test | 输入 | 结果 |
|------|------|------|
| 1 | fdep stage_review url | ✅ 3116 chars 完整 Job Card |
| 2 | 越界 url（invoice-approval url 配 fdep）| ❌ "url 不安全" 拒绝 |
| 3 | 不存在的 url | ❌ FileNotFoundError |
| 4 | url 自动补 `.md` 后缀 | ✅ work |
| 5 | invoice-approval job_card_submit（部署后）| ✅ 1993 chars |
| 6 | customer-test | ❌ "未知 action"（新代码未推 customer） |

---

## 5. 关键决策（ADR 风格）

### ADR-34.1 · 引擎层加 endpoint（不动 SKILL 解决）
- **决策理由**：仅 SKILL.md 文档无法让 agent 跨 server 读 job_card（customer-test 拿不到本地文件）；必须 engine 提供统一 API
- **代价**：动了 `vendor/jeeflow/facade.py`，需要重新部署 engine

### ADR-34.2 · 安全：url 必须以 `ToT/flows/<flow-id>/job_cards/` 开头
- **决策理由**：防止目录遍历攻击（如 `url=ToT/config/servers.json`）
- **行为**：跨流程越界 / 跨目录访问均拒绝

### ADR-34.3 · url 自动补 `.md`
- **决策理由**：用户友好；agent 给 url 时不必关心后缀
- **行为**：`job_card_stage_review` 与 `job_card_stage_review.md` 等价

### ADR-34.4 · 不预加载 job_cards 到内存
- **决策理由**：静态读即可，无需缓存；engine cwd 已是仓库根，相对路径 `open()` 立即可读
- **代价**：每次调用读一次文件（job_card ~ 1-5 KB，性能 OK）

---

## 6. 度量（飞轮 34 圈累积）

| 指标 | #33 | **#34** |
|------|-----|---------|
| engine endpoint 数 | 50+ | **+1 (getJobCardContent)** |
| SKILL.md 节数 | 7 | **8 (+Work Guidance)** |
| flow-operator 文件数 | 3 | **3** |
| §9 检查项 | 44 | **44** |
| EA roadmap 版本 | v3.8 | **v3.8** |

---

## 7. 闭环示意

```
┌── "job_card URL 知道，但读不到内容" ──┐
↓                       │
设计 endpoint：getJobCardContent │
↓                       │
facade.py 实现（+40 行）  │
↓                       │
重启 engine + 5 测试      │
↓                       │
✅ fdep stage_review 3116 chars  │
✅ 越界 / 不存在 / 自动补后缀 │
↓                       │
SKILL.md +Work Guidance  │
↓                       │
→ 飞轮第 34 圈 ✅           │
```

---

## 8. 经验沉淀

### 8.1 Job Card 作为工作指导的最小闭环
- **端到端 4 步**：接单 → 拿 URL → 读内容 → 决策提交
- **engine 一致性**：API 一致让 agent 不必区分本地 / 远端
- **安全第一**：url 越界检查是必备，不可省

### 8.2 Engine 改动的边界
- **能不加 endpoint 就不加**：本次必须加（URL 无法跨 server 读）
- **加 endpoint 必带安全**：路径前缀检查
- **小改动小测试**：5 测试覆盖核心场景，不膨胀

### 8.3 文档与实现同步
- **Tools 表同步**：新 endpoint 必须出现在 §A
- **新章节同步**：新能力需新一节 `## Work Guidance` 说明工作流
- **endpoint 规范表**：请求 / 返回 / 安全 / 备注全列

---

## 9. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第三十四轮迭代 · W43 新 endpoint + Work Guidance**：① **新增 `processDefine/getJobCardContent`** endpoint（facade.py +40 行）；② **安全**：url 必须 `ToT/flows/<flow-id>/job_cards/` 开头 + 自动补 `.md` 后缀；③ **静态读**（不预加载），engine cwd=仓库根，相对路径可达；④ **SKILL.md Tools §A** 加新行；⑤ **SKILL.md 新增 `## Work Guidance` 节**（4 子节：为什么 / 工作流 / endpoint 规范 / 注意事项）；⑥ **5 测试全过**：fdep stage_review 3116 chars + 越界拒绝 + 不存在报错 + 自动补后缀 + invoice-approval 1993 chars；⑦ **ea-compliance 44/44 PASS**；⑧ **未触动**：所有 SOP / config / iter#33 任何文件；⑨ 新增 iterations/2026-09-23_job-card-endpoint.md；⑩ iterations/README.md 刷新 33 → 34 圈。 |