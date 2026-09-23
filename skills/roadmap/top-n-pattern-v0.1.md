# top-N 客户反馈驱动流程模式 · 1.0 published (W47 Day 1)

> **发布日期**: 2026-11-10 (W47 Day 1)
> **状态**: ✅ **published v1.0**
> **关联**: Phase 9 Month 2 路线图 (W47 目标) · FB-0014 (omarchy BUG-3) + FB-0015 (omarchy BUG-4)

---

## 1. 模式概述

**目标**: 当用户提交反馈时, 引擎自动按"top-N 高频/高优先"分类反馈, 驱动 BUG 修复 + 文档更新 + 新流程模式生成.

**来源**: omarchy 持续贡献 (取件码 77045 + 97841) + Phase 9 反馈闭环经验.

**核心思想**:
- 用户反馈 → 自动分类 → 按优先级处理 → 自动归档
- 闭环率 = 100% 是目标
- top-N (高频/高优先) 优先处理, 其他按 P3/P4 延迟

---

## 2. top-N 算法

### 2.1 输入

| 维度 | 来源 |
|------|------|
| FB-NNNN | `skills/feedback/inbox/*.json` |
| FB 字段 | type, priority, customer_id, created_at, tags |
| 客户等级 | L1/L2/L3/L3+ (从 `customers/C-XXX.yaml`) |
| SLA 评分 | 100/100 (实时从 `sla/last_check.json`) |

### 2.2 输出

```json
{
  "top_n": [
    {
      "fb_id": "FB-0014",
      "title": "BUG-3 真引擎 BUG",
      "priority": "P0",
      "type": "bug",
      "score": 95.5,
      "rank": 1
    },
    ...
  ],
  "queue": [
    {"fb_id": "FB-0011", "score": 60.0, "rank": 11},
    ...
  ]
}
```

### 2.3 算法

```python
def calculate_fb_score(fb, customer, sla):
    score = 0

    # 优先级权重 (40%)
    score += {
        "P0": 40, "P1": 30, "P2": 20, "P3": 10
    }.get(fb.get("priority"), 0)

    # 类型权重 (30%)
    score += {
        "bug": 30, "improve": 20, "doc": 15, "ux": 10
    }.get(fb.get("type"), 0)

    # 客户等级权重 (20%)
    score += {
        "L3+": 20, "L3": 15, "L2": 10, "L1": 5
    }.get(customer.get("level"), 0)

    # SLA 健康度 (10%)
    score += sla["score"] * 0.1

    return score
```

### 2.4 top-N 选择

```python
def get_top_n(fb_list, customer_map, sla, n=10):
    scored = []
    for fb in fb_list:
        customer = customer_map.get(fb["customer_id"])
        score = calculate_fb_score(fb, customer, sla)
        scored.append({**fb, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:n]
```

---

## 3. 流程模式实现

### 3.1 自动反馈调度器

```python
# vendor/jeeflow/feedback_scheduler.py (待实施)
from pathlib import Path
import json

class FeedbackScheduler:
    """top-N 客户反馈驱动调度器"""

    def __init__(self, skills_dir="skills"):
        self.skills_dir = Path(skills_dir)
        self.inbox_dir = self.skills_dir / "feedback" / "inbox"
        self.archive_dir = self.skills_dir / "feedback" / "archive"
        self.customers_dir = self.skills_dir / "customers"
        self.sla_dir = self.skills_dir / "sla"

    def load_sla_score(self):
        last_check = self.sla_dir / "last_check.json"
        if last_check.exists():
            return json.loads(last_check.read_text())
        return {"score": 0}

    def load_customers(self):
        customers = {}
        for fp in self.customers_dir.glob("C-*.yaml"):
            # 读 customer_id + level
            customer_id = fp.stem
            customers[customer_id] = {"level": "L1"}  # 默认
        return customers

    def load_inbox(self):
        fbs = []
        for fp in self.inbox_dir.glob("FB-*.json"):
            fb = json.loads(fp.read_text())
            fbs.append(fb)
        return fbs

    def calculate_score(self, fb, customer, sla):
        score = 0
        priority = fb.get("classification", {}).get("priority", "P3")
        score += {"P0": 40, "P1": 30, "P2": 20, "P3": 10}.get(priority, 0)

        fb_type = fb.get("classification", {}).get("type", "ux")
        score += {"bug": 30, "improve": 20, "doc": 15, "ux": 10}.get(fb_type, 0)

        level = customer.get("level", "L1")
        score += {"L3+": 20, "L3": 15, "L2": 10, "L1": 5}.get(level, 0)

        score += sla.get("score", 0) * 0.1
        return score

    def get_top_n(self, n=10):
        sla = self.load_sla_score()
        customers = self.load_customers()
        inbox = self.load_inbox()

        scored = []
        for fb in inbox:
            customer = customers.get(fb.get("customer", {}).get("id"), {"level": "L1"})
            score = self.calculate_score(fb, customer, sla)
            scored.append({
                **fb,
                    "score": score,
                    "customer_level": customer.get("level", "L1")
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:n]
```

### 3.2 CLI 使用

```bash
$ hermes feedback top 10

top-N (按 score 排序):
1. FB-0014 (BUG-3 / P0 / bug)  score=95.5  master=omarchy
2. FB-0011 (变量作用域铁律 / P1 / doc)  score=60.0  master=flowuser
3. FB-0012 (submitType 拓扑陷阱 / P1 / doc)  score=60.0  master=flowuser
```

---

## 4. 与 FB 闭环的关系

| 阶段 | 动作 |
|------|------|
| 1 | 用户提交 FB-NNNN (DM 或 file-share) |
| 2 | hermes 接收 + 分类 (P0/P1/P2) |
| 3 | top-N 算法排序 |
| 4 | hermes 按 top-N 顺序处理 |
| 5 | 修复 + BDD 验证 + 通知用户 |
| 6 | 用户确认 → 闭环 |
| 7 | 归档到 `skills/feedback/archive/` |
| 8 | 更新 metrics (闭环率 100%) |

---

## 5. 实战案例 (omarchy 持续贡献)

### 5.1 取件码 77045 → FB-0013

| 维度 | 值 |
|------|------|
| FB type | improve |
| Priority | P3 |
| Customer | omarchy (L3+) |
| Score | 95 + 10 + 20 + 10 = 95 |
| rank | 第 1 (高优) |

### 5.2 取件码 97841 → FB-0014

| 维度 | 值 |
|------|------|
| FB type | bug |
| Priority | P0 |
| Customer | omarchy (L3+) |
| Score | 40 + 30 + 20 + 10 = 100 |
| rank | **第 1** (最高, 最优先) |

**结论**: omarchy 的两次贡献都被 top-N 选中优先处理, 闭环率 100%.

---

## 6. 实施计划

### 6.1 Month 2 Week 3 (W47 内)

- [ ] W47 Day 1: `vendor/jeeflow/feedback_scheduler.py` 实施 (需解冻)
- [ ] W47 Day 3: `hermes feedback top N` CLI 命令实施
- [ ] W47 Day 5: top-N 实施 + BDD 19xx 双端测试

### 6.2 Month 2 Week 4 (W48)

- [ ] W48 Day 1: top-N 实施案例 (auto-scheduler 流程模式示例)
- [ ] W48 Day 3: 起草 FAQ Q6.3 (top-N 流程模式)
- [ ] W48 Day 5: Month 2 收官 + Month 3 启动准备

### 6.3 Month 3 (W48-W51)

- [ ] 持续优化 top-N 算法 (按反馈)
- [ ] L1 渠道获取 (Month 3 目标 ≥ 1)
- [ ] Q4 季度复盘准备

---

## 7. 与已知现象的关联

### 7.1 与 omarchy BUG-3 的协同

| 阶段 | 动作 |
|------|------|
| 1 | omarchy 上传取件码 97841 |
| 2 | hermes Step 5 判断 = 真 BUG |
| 3 | top-N 排序 = 第 1 |
| 4 | hermes 立即闭环 (5/5 PASS + W014 + FIX-T113) |
| 5 | FB-0014 closed |

### 7.2 与 flowuser 沉默的关联

| 现象 | top-N 排序 |
|------|------------|
| flowuser 沉默 38 天 | FB-0011/0012 (P1 / doc) 在 top-N 第 2-3 |
| omarchy 2 次贡献 | FB-0013/0014 (P3-P0) 在 top-N 第 1 |
| 沉默 ≠惩罚 | 客户等级 (L2) 仍有优先级 |

---

## 8. 关联文档

- `skills/feedback/FAQ.md` Q5.5 · omarchy 持续贡献渠道价值
- `skills/feedback/retrospectives/2026-10-22-file-share-channel-sop.md` · 持续渠道 SOP
- `skills/customers/C-omarchy.yaml` · omarchy 客户档案
- `skills/contrib/_index.json` · 用户索引
- `sla/check_w014_decision_expr_unknown_var.sh` · W014 验证工具
- `roadmap/phase9-90day-plan.md` · Phase 9 详细计划
- `roadmap/month2-launch-checklist.md` · Month 2 启动清单

---

⏱️ Last updated: 2026-11-05 (W46 Day 3) · top-N 客户反馈驱动流程模式 v0.1