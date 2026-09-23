# Promote Demo · invoice-approval · 2026-09-23

> **目的**：演示 promote 工具链完整流程（即使 local-pg 因缺依赖未启动）

## 流程节点

```
Step 1: design         ✅ flow_designer.py 5 问 → invoice-approval.json v0.1
Step 2: deploy         ✅ /wf/processDefine/deploy 到 local-memory (defineId=41)
Step 3: e2e            ✅ 小额+大额 2 条路径跑通（state=DONE）
Step 4: completeness   ✅ 50% → 69% → 74% → 89% → 94% → 100%
Step 5: docs           ✅ 5 文件 + 4 Job Cards
Step 6: baseline       ✅ test_invoice-approval_baseline_v0_1.md（100% PASS）
Step 7: promote        ⚠️ local-pg 缺 asyncpg，未实际推
                      ✅ request-promote + status 演示完整工作流
Step 8: ea-compliance  🔄 下一步
```

## request-promote 输出

详见上方脚本输出。提示：

- ⚠️  此操作需人工审批
- 步骤：人工审批 → 写留档 → `promote invoice-approval org-server-to-customer-test --confirm-ai`

## 已知问题

1. **local-pg 缺 asyncpg**：AGENTS 禁装依赖，无法启动。需要：
   - option A: 在另一台机器部署
   - option B: 修改 main_pg.py 用 psycopg2（如已安装）
2. **promote.py push 默认失败（HTTP 不通）**：因为目标 server 没起；可作为"故意失败"的演示
3. **push 用本地→本地演示**：发现 promote 默认指向 customer-test 而不是 local-pg（可能需要看 promote.py 是否有 stage-aware 路由）

## 留档

- promote 演示：本次
- baseline：`ToT/tdd/test_invoice-approval_baseline_v0_1.md`
