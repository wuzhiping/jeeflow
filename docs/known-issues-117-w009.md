## §117 W009 字段权限声明下游覆盖 (Verify 警告)

> **来源**: omarchy BDD 10-run (取件码 77045, FB-0013) + omarchy 多次 5-run 验证
> **发现**: 2026-09-21 (Phase 8 中期)
> **状态**: 🟡 warning (非阻塞, 持续触发)
> **类型**: verify warning

---

### 现象

```
[W009/warning] 字段 f_leaveType 在节点 ['task1'] 声明为 read/hidden, 
  但节点 ['apply'] 未声明 (下游可覆盖, 建议显式声明) nodes=['apply']
```

**触发条件**: 字段 `f_xxx` 在下游节点 (`task1` / `manager`) 声明 `PERMISSION_f_xxx` (read/hidden), 但上游节点 (`apply`) 未声明对应 `PERMISSION`.

### 根因

设计流程时, 字段 `f_xxx` 的权限声明仅在下游节点声明, 上游未声明, 触发 W009 warning (字段被下游覆盖的可能性).

**当前引擎行为**:
- 下游可覆盖上游字段权限
- 这是**非阻塞**警告, 不阻止 save / deploy / start

### 复现 (omarchy 取件码 77045 · simple 流程)

```
flags: [apply/task1]
└── task1 field: {PERMISSION_f_leaveType: 1}
    └── apply: 未声明 PERMISSION_f_leaveType
        → W009 触发 (10 次 run 每次都触发)
```

### 期望 (修复方案)

| 选项 | 描述 |
|------|------|
| **方案 A (推荐)** | 在上游 `apply` 节点也声明 `PERMISSION_f_leaveType`, 与下游对齐 |
| **方案 B** | 在 `vendor/jeeflow/verify.py` 中调整 W009 规则, 改为 "info" 级别 |
| **方案 C** | 保持当前 (非阻塞 warning), 文档化即可 |

### 教训

1. **W009 是设计一致性警告**, 不是 BUG
2. **下游覆盖上游 = 静默行为**, 需要显式声明
3. **非阻塞**, 不影响流程执行
4. **建议** 流程设计时, 上游 + 下游节点都声明字段权限, 保持一致性

### 客户贡献

- omarchy 取件码 77045 (FB-0013): 简单审批流程 10/10 PASS + W009 持续触发
- omarchy 取件码 39376 (FB-0015): BDD-1601 5-run + W009 (f_amount, f_leaveType, f_reason 等 3 个字段)
- omarchy 取件码 97841 (FB-0014): BDD-1517 + W009 + W014 新增

### 关联

- `feedback/archive/FB-0013.json` · omarchy 持续渠道第 1 次贡献
- `feedback/archive/FB-0014.json` · omarchy 持续渠道第 2 次贡献
- `feedback/archive/FB-0015.json` · omarchy 持续渠道第 3 次贡献
- `sla/check_w014_decision_expr_unknown_var.sh` · W014 verify 工具 (omarchy 贡献, 32/32 PASS)
- `sla/W014-VERIFY-RULE.md` · W014 工具说明

### 当前处理

- 🟡 **W009 是 warning, 不是 BUG**, 流程正常运行
- 🟡 不阻塞 hero, 现状接受 (设计如此)
- 📋 列入候选 known-issues §117 (本文件)
- 📋 FAQ Q3.4 (决策 expr 未知变量) 已记录 W014 类似机制

---

⏱️ Last updated: 2026-11-17 (W47 Day 5) · known-issues §117 published