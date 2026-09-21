# BDD-DEV-006 dev-overtime-multi-decision (20260921231000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交加班]
    apply --> d1{时长分级}
    d1 -- f_hours<=8 --> d2{短期细分}
    d1 -- f_hours>8 --> cto[CTO 审批]
    d2 -- f_hours<=4 --> leader_only[组长审批]
    d2 -- f_hours>4 --> rd[总监复核]
    leader_only --> hr[HR 备案]
    rd --> hr
    cto --> hr
    hr --> end([结束])
```

## 场景

加班审批 - 多层 decision 嵌套 + 三分支汇合。按时长分 3 档（≤4h / 4-8h / >8h）。

## 用到的能力

- 多层 `snaker:decision` 嵌套（d1 → d2 → 终态）
- decision 出边 `expr` 含数值比较（`#f_hours<=8` / `#f_hours>8` / `#f_hours<=4`）
- 多入边 task 节点（hr_record 由 leader_only / rd / cto 三路汇合）

## 执行脚本

3 个分支场景一次性回归：

```bash
# 场景A: 3小时 → leader_only → hr_record → DONE
# 场景B: 6小时 → rd_review → hr_record → DONE
# 场景C: 12小时 → cto_approve_high → hr_record → DONE
```

每次 reset + deploy + start + 2 次 execute（审批人 + hr_record）。

## 校验

| 场景 | hours | 第一层 decision | 第二层 | 中间节点 | 最终节点 | state |
|---|---|---|---|---|---|---|
| A | 3 | d1(≤8) → d2 | d2(≤4) → leader_only | leader_only | hr_record | 20 ✅ |
| B | 6 | d1(≤8) → d2 | d2(>4) → rd_review | rd_review | hr_record | 20 ✅ |
| C | 12 | d1(>8) | (跳过) → cto_approve_high | cto_approve_high | hr_record | 20 ✅ |

## 结果

- memory (8101): ✅ **PASS**（多层 decision + 三分支汇合）
- pg (8102): skipped

## 经验教训

- decision 嵌套时，引擎按 JSON `edges` 顺序评估 expr，与 Java snaker 一致
- 多入边 task 节点等效 join 模式，HR 备案 3 路汇合无需显式 join 节点
- 中间决策节点的所有出边 expr 都失败时，引擎兜底走第一条边（见 §3.4 兜底逻辑）