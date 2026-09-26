# health-check.py — ToT/docs 综合健康度评分

> **状态**：✅ 已实现（2026-09-25）
> **定位**：每周/每次 release 跑一次，看 ToT/docs 健康度趋势

## 5 维度评分（加权综合）

| 维度 | 权重 | 来源 | 评分规则 |
|---|---|---|---|
| **Drift** | 30% | `doc-link-checker.py --json` | 100 - drift/total×100 - near_match/total×50 |
| **Snapshot** | 15% | `ToT/sop/snapshots/*.json` 数量 | 50 + count×5（上限 100）|
| **API Coverage** | 25% | vendor/jeeflow 公开 API 在 ToT/docs 出现率 | covered/total×100 |
| **Freshness** | 20% | `git log` 对比 doc vs vendor mtime | 100 - stale_90×50 - stale_30×20 |
| **Consistency** | 10% | 核心概念在 ≥3 个 doc 出现率 | well_distributed/concepts×100 |

**综合分** = Σ(score × weight) / Σ(weight)
- 🟢 ≥85 健康
- 🟡 60-84 亚健康
- 🔴 <60 异常

## 用法

```bash
# 跑全维度
python3 ToT/sop/health-check.py

# JSON 输出（CI 集成）
python3 ToT/sop/health-check.py --json

# 单维度
python3 ToT/sop/health-check.py --dimension drift
python3 ToT/sop/health-check.py --dimension api
python3 ToT/sop/health-check.py --dimension freshness

# 保存历史
python3 ToT/sop/health-check.py --save ToT/sop/snapshots/_health_baseline.json
```

## 当前评分（2026-09-25）

```
════════════════════════════════════════════════════════════
  ToT/docs Health Report
  2026-09-25T00:16:51+00:00
════════════════════════════════════════════════════════════

  Drift              ████████████████████ 100/100  ✅  (30%)
    total: 134 · ok: 134 · near_match: 0 · drift: 0

  Snapshot           ███████████████████░  95/100  ✅  (15%)
    total: 9 · recent_3d: 0

  API Coverage       ███████████████░░░░░  78/100  ✅  (25%)
    total: 73 · covered: 57
    missing_sample: [CountersignType, DefineRow, DefineState, Engine, FlowEdge ...]
    ➜ 补齐 16 个公开 API

  Freshness          ████████████████████ 100/100  ✅  (20%)
    total_docs: 41 · fresh: 41 · stale_30_90: 0 · stale_90_plus: 0

  Consistency        ██████████████████░░  90/100  ✅  (10%)
    well_distributed: 9/10 concepts
    Engine: 0 ⚠️ (未在任何 doc 提到)

────────────────────────────────────────────────────────────
  Overall Score: ██████████████████░░ 92/100  🟢 健康
```

## 改进建议（按当前评分）

1. **API Coverage 78→100**：补齐 16 个公开 API
   - `Engine`、`CountersignType`、`DefineRow`、`DefineState`
   - `FlowEdge`、`FlowNode`、`FlowModel`
   - `MemoryExtRepository`、`InstanceRow`、`InstanceStatsRow`
   - `PerformType`、`QueryCondition`
2. **Engine 概念孤立**：在 ToT/docs/concepts/ 添加 engine.md 文档
3. **Snapshot 9→12+**：保持每 release 一个 snapshot 节奏

## 与 release.sh 集成（建议）

```bash
# release.sh Step 0: 健康度门禁
python3 ToT/sop/health-check.py | tee /tmp/health.txt
SCORE=$(python3 ToT/sop/health-check.py --json | python3 -c "import sys,json;print(json.load(sys.stdin)['overall_score'])")
if [ "$SCORE" -lt 60 ]; then
    echo "❌ 健康度异常 ($SCORE/100)，发布被阻止"
    exit 1
fi
```

## 设计决策

| 选项 | 决定 | 理由 |
|---|---|---|
| 5 维度 | Drift/Snapshot/API/Freshness/Consistency | 覆盖「代码对齐 + 累积 + 覆盖 + 新鲜 + 一致」|
| 权重 | 30/15/25/20/10 | Drift+API 是核心，其余次要 |
| Freshness 用 git log | ✅ | 比文件系统 mtime 准确（多人协作） |
| Consistency 看概念 | 10 个核心概念 | 简单可解释，避免过度工程 |
| 不引入第三方包 | ✅ | 与其他 sop 脚本保持一致（仅 stdlib）|

## 输出格式

- **文本**：进度条 + 维度详情 + 综合分 + 改进建议
- **JSON**：结构化数据，可保存到 `ToT/sop/snapshots/_health_*.json` 做趋势跟踪

## 后续

- [ ] 健康度趋势跟踪（diff vs baseline）
- [ ] release.sh Step 0 健康度门禁
- [ ] GitLab/Jenkins 集成（已在 Phase 4 取消远程 GitHub Actions）
- [ ] 月度健康度报告（自动生成 markdown）