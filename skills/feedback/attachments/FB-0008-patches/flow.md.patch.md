# docs/flow.md §3.3 修订方案 (FIX-DOC-2)

> **当前**: line 161 + line 213-216 描述模糊, 设计师可能误用
> **修订后**: 明确三种模式 + 互斥性 + 行为差异

---

## 修订 1 · line 161 (字段表)

### 当前 (原文)

```
| countersignCompletionCondition | string | 否 | 会签完成条件；可放 properties 根下，也可放 properties.field 内。两种取值：① Activiti 表达式，如 "#nrOfCompletedInstances==2"（flows/07）；② 常量 "ONE_VOTE_VETO" 一票否决（flows/13） |
```

### 修订后 (建议)

```
| countersignCompletionCondition | string | 否 | 会签完成条件；**两种语义互斥**, 不可复合。可放 properties 根下, 也可放 properties.field 内。详见下方"会签完成模式表" |
```

---

## 修订 2 · line 213-216 (会签说明段落)

### 当前 (原文)

```
**比例会签（N/M 通过）扩展（实测 2026-09-17 BDD Task 16）**：
- countersignType=PARALLEL + countersignCompletionCondition="#nrOfCompletedInstances>=K"
- 每次 task 完成时 evaluate 表达式；true → abandon 剩余 DOING（taskState=99 ABANDON）+ 推进下游
- RatioCapableEngine 扩展（main_pg.py:93-155）
```

### 修订后 (建议)

替换为:

```
**会签完成模式（实测 2026-09-21 BUG-2 复现 + BDD Task 16 + FB-0008）**：

| 模式 | countersignCompletionCondition 字段值 | 行为 | 样例 |
|------|---------------------------------------|------|------|
| **全员通过 (默认)** | (字段省略) | PARALLEL: 全员 approve 才流转; 任何 reject 走 reject 边 | flows/05 |
| **比例通过 (N/M)** | "#nrOfCompletedInstances>=K" (OGNL 表达式) | 满足 K/M 立即流转 + 余者 taskState=99 ABANDON (updateUser=触发者, FIX-T111) | flows/07 |
| **一票否决** | "ONE_VOTE_VETO" (字符串常量) | 任一 reject (submitType=20) 立即流转 state=45 + 余者 ABANDON | flows/13 |

⚠️ **关键互斥 (FB-0008 / flowuser 报告)**:
- 字段值 = 表达式 → **放弃** 一票否决能力 (即使 reject, 引擎已按比例流转, reject 来不及)
- 字段值 = 字符串 → **放弃** 比例能力 (引擎只识别 ONE_VOTE_VETO, 不评估表达式)
- 这是引擎设计选择, 不是 bug. 设计师必须二选一, 不要试图"2/3 通过 OR 任一 reject"

**比例会签实现细节 (实测 2026-09-17 BDD Task 16)**:
- countersignType=PARALLEL + countersignCompletionCondition="#nrOfCompletedInstances>=K"
- 每次 task 完成时 evaluate 表达式; true → abandon 剩余 DOING (taskState=99 ABANDON, updateUser=触发者) + 推进下游
- RatioCapableEngine 扩展 (main_pg.py:93-155)
- 一票否决: 引擎识别字符串 "ONE_VOTE_VETO", 任一 reject (submitType=20) 立即 cs_veto 路径流转 (FIX-T46)
```

---

## 修订理由 (给 bro review)

1. **当前文档没说明互斥性**: 设计师 (如 flowuser) 误以为可以"2/3 通过 OR 任一 reject"复合规则
2. **三种模式应明确列出**: 让设计师能直接对号入座
3. **行为差异要写清**: 比例模式 ABANDON 触发者是最后通过者, 一票否决是 rejecter
4. **加 FB-0008 来源**: 实证案例, 不是凭空想象

---

## 风险评估

- **风险**: 低 (仅文档, 不改引擎)
- **兼容性**: 0 影响 (样例字段值不变)
- **回滚**: 易 (git revert)

---

## 应用方式 (建议)

```bash
# 1. 备份
cp docs/flow.md docs/flow.md.bak.20260921

# 2. 应用修订 (用 Edit 工具, 找 line 161 + line 213 替换)

# 3. 验证 (确认语法 + 章节号)
wc -l docs/flow.md
grep -n "countersignCompletionCondition" docs/flow.md
```

⏱️ Last updated: 2026-09-21 · FB-0008 / FIX-DOC-2
