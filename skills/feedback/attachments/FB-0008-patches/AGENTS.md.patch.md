# docs/AGENTS.md §5.8 修订方案 (FIX-DOC-2)

> **当前**: line 293-295 会签测试表未说明字段值类型 + 互斥性
> **修订后**: 与 flow.md §3.3 一致

---

## 修订 · line 293-295 (会签测试表)

### 当前 (原文)

```
| 类型 | curl 操作 | 预期 performType/countersignType | 预期完成条件 |
| --- | --- | --- | --- |
| 并行 | 三用户按序 processTask/execute | 1 / PARALLEL | 全员通过才流转（剩余成员 taskState 仍 10，不自动废弃） |
| 串行 | 三个用户按顺序 processTask/execute | 1 / SEQUENTIAL | 仅最后一个通过即流转 |
| 比例 | N 个用户中 K 个通过 | 1 / PARALLEL | countersignCompletionCondition 在 field 下 |
| 一票否决 | 任一用户 reject（submitType=20） | 1 / PARALLEL | ONE_VOTE_VETO（仅当配置时生效；剩余成员废弃） |
```

### 修订后 (建议)

替换为:

```
| 类型 | curl 操作 | 预期 performType/countersignType | countersignCompletionCondition 字段值 | 预期完成条件 |
| --- | --- | --- | --- | --- |
| 并行 (全员通过) | 三用户按序 processTask/execute (全部 submitType=0) | 1 / PARALLEL | (字段省略) | 全员通过才流转（剩余成员 taskState 仍 10，不自动废弃） |
| 串行 | 三个用户按顺序 processTask/execute | 1 / SEQUENTIAL | (字段省略) | 仅最后一个通过即流转 |
| 比例 (N/M) | N 个用户中 K 个 submitType=0 | 1 / PARALLEL | "#nrOfCompletedInstances>=K" (OGNL 表达式) | 满足 K/M 立即流转; 余者 taskState=99 ABANDON (updateUser=触发者, FIX-T111) |
| 一票否决 | 任一用户 reject (submitType=20) | 1 / PARALLEL | "ONE_VOTE_VETO" (字符串常量) | 立即流转 state=45 + 余者 ABANDON (updateUser=rejecter, FIX-T46+T111) |

⚠️ **FB-0008 关键提示 (2026-09-21 flowuser 反馈)**:
- 字段值 = 表达式 → 引擎按比例模式处理, **放弃** 一票否决能力
- 字段值 = 字符串 "ONE_VOTE_VETO" → 引擎按一票否决处理, **放弃** 比例能力
- 这两种语义 **互斥**, 不能复合 (如设计师想"2/3 通过 OR 任一 reject"是行不通的)
- 设计师必须二选一, 不要试图构造"复合规则"
- 详见 `docs/flow.md §3.3` (修订后) + `docs/known-issues.md §113`
```

---

## 修订 2 · 现有 line 117-118 (设计模板行)

### 当前 (原文)

```
| 比例会签（✅ 已实现，RatioCapableEngine 扩展） | `./flows/07-countersign-ratio.json` | `countersignCompletionCondition: "#nrOfCompletedInstances==2"`（OGNL 表达式，`nrOfCompletedInstances`/`nrOfInstances` 自动注入） |
| 一票否决会签 | `./flows/13-countersign-one-vote-veto.json` | `countersignCompletionCondition: "ONE_VOTE_VETO"` |
```

### 修订后 (建议)

在末尾加:

```
| 会签互斥性提示 (FB-0008) | — | `countersignCompletionCondition` 字段值 = 表达式 OR 字符串常量, 二选一, 详见 §5.8 修订 + flow.md §3.3 |
```

---

## 修订理由

1. **会签测试表应有字段值列**: 设计师测试时能直接对照
2. **明确每种模式的字段值**: 避免 flowuser 类的误解
3. **加互斥性警告**: 直接阻止"复合规则"误用
4. **指向 flow.md + known-issues.md**: 单一信息源

---

## 风险评估

- **风险**: 低 (仅文档)
- **兼容性**: 0 影响
- **回滚**: 易

⏱️ Last updated: 2026-09-21 · FB-0008 / FIX-DOC-2
