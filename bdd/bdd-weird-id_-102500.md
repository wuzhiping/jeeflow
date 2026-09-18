# BDD 任务 #117: 节点 id 含空格

## 目标
验证节点 id 含空格（如 `"apply node"`）能否被引擎接受

## 流程
start1 → "apply node" → end1

## 实测
1. **修复前**：save+deploy+start 全部成功，state=20（DONE）— 违反 §3.1 文档约束
2. **修复后**：deploy 立即 `99999999 [ValueError] 流程节点 id 含非法字符: ['apply node']`

## 结论
❌→✅ **BUG 已修复**

## 根因
- `docs/flow.md §3.1` 规定"节点 id 不含空格 / - / 中文"
- 但引擎 save/deploy/start 都不阻止
- 与 docs 规范不一致，存在跨语言兼容风险

## 修复（FIX-T34 2026-09-18）
`vendor/jeeflow/facade.py:240-247` deploy 校验：
```python
import re
bad_ids = sorted({i for i in node_ids if not re.match(r"^[A-Za-z0-9_]+$", i)})
if bad_ids:
    raise ValueError(f"流程节点 id 含非法字符: {bad_ids}（§3.1 docs/flow.md 约束，"
                     f"只允许字母/数字/下划线）")
```

## 优先级
高（与 docs 规范不一致；已修复）
