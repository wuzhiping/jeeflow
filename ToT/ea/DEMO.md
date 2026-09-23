# EA DEMO · 团队培训实战手册

> **目的**：让团队成员 30 分钟内掌握 EA 体系的核心工具
> **方式**：3 个实战 demo（可直接复制运行）
> **前置**：已读 `ToT/HANDBOOK.md` + `ToT/GETTING_STARTED.md`

---

## Demo 1 · 5 分钟快速上手（Hello TDD）

### 目标
跑通 tdd-flow，看到 dashboard

### 步骤

```bash
# 1. 启动本地引擎（memory 后端）
cd ~/projects/jeeFlow
(nohup python3 -m uvicorn main:app --port 8101 > /tmp/uvicorn.log 2>&1 &)
sleep 5
curl -s http://127.0.0.1:8101/healthz

# 2. 跑 tdd-flow（dry-run 模式，0.16s）
./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
    ToT/flows/invoice-approval.json --dry-run

# 3. 跑实跑 + dashboard（0.7s）
./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
    ToT/flows/invoice-approval.json \
    --scenarios 'small:{"amount":500}|big:{"amount":8000}|reject:{"amount":8000}:5:金额异常' \
    --top-vars '{"tf_manager":"u_bob","tf_treasurer":"u_carol"}' \
    --report-html ToT/tdd/dashboard.html

# 4. 打开 dashboard
open ToT/tdd/dashboard.html  # macOS
xdg-open ToT/tdd/dashboard.html  # Linux
```

### 期望结果
- ✅ dry-run 0.16s，3 scenarios PASSED
- ✅ 实跑 0.7s，3 scenarios PASSED
- ✅ dashboard.html 含 sparkline + trend + filter 按钮

---

## Demo 2 · 15 分钟端到端（新流程）

### 目标
设计 + 部署 + 测试一个新流程（如：请假审批 leave-approval）

### 步骤

```bash
# 1. 用 flow_designer.py 设计（5 问交互）
./ToT/bin/jf python3 ToT/sop/flow_designer.py
# 回答：leave-approval / 请假审批 / submit-approve / employee+manager / no
# → 生成 ToT/flows/leave-approval.json (50% 评分)

# 2. 编辑 leave-approval.json 完善：
#    - decision 节点加 expr
#    - 加 job_card_url 等

# 3. 跑完整性检查
./ToT/bin/jf python3 ToT/sop/flow_completeness.py ToT/flows/leave-approval.json
# → 显示 50% / 缺失文档 / Job Cards / baseline

# 4. 写 5 个文档
mkdir ToT/flows/leave-approval/job_cards
# 参考 ToT/flows/invoice-approval/{README,ROLES,NODES,CHANGELOG,RESPONSES}.md

# 5. 写 Job Cards（4 张）
# 参考 ToT/flows/invoice-approval/job_cards/

# 6. 加到 tests.json
# 编辑 ToT/tdd/tests.json，加 leave-approval 条目

# 7. 跑 tdd-flow（应 100%）
./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
    --tests-file ToT/tdd/tests.json --all-flows \
    --report-html ToT/tdd/dashboard.html

# 8. save-baseline
./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
    ToT/flows/leave-approval.json \
    --scenarios 'happy:{"days":1}|big:{"days":10}|reject:{"days":5}:5:材料不全' \
    --save-baseline
```

### 期望结果
- ✅ leave-approval.json 部署到引擎
- ✅ completeness 100%（6 层全过）
- ✅ 3 scenarios 全过，DONE
- ✅ baseline 自动生成

---

## Demo 3 · 20 分钟 CI 集成（端到端实战）

### 目标
把 EA 工具集成到 GitHub Actions（也可适配 GitLab CI/Jenkins）

### 步骤

#### 1. 创建 `.github/workflows/tdd.yml`

```yaml
name: TDD Regression

on:
  pull_request:
  push:
    branches: [main]

jobs:
  tdd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # git diff 需要历史

      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Start engine
        run: |
          nohup python3 -m uvicorn main:app --port 8101 &
          sleep 5

      - name: TDD PR check (dry-run)
        run: |
          ./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
            --tests-file ToT/tdd/tests.json --all-flows --only-changed --dry-run

      - name: TDD merge check (baseline-only)
        if: github.event_name == 'pull_request'
        run: |
          ./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
            --tests-file ToT/tdd/tests.json --all-flows --baseline-only

      - name: TDD full regression
        if: github.event_name == 'push'
        run: |
          ./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
            --tests-file ToT/tdd/tests.json --all-flows \
            --report-json dashboard.json \
            --report-html dashboard.html

      - name: Upload dashboard
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: tdd-dashboard
          path: |
            dashboard.json
            dashboard.html
```

#### 2. 本地测试

```bash
# 模拟 PR（改一个 flow）
echo "test" >> ToT/flows/invoice-approval.json
./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
    --tests-file ToT/tdd/tests.json --all-flows --only-changed --dry-run

# 恢复
git checkout -- ToT/flows/invoice-approval.json
```

#### 3. Push 触发 CI

```bash
git add .github/workflows/tdd.yml
git commit -m "ci: add TDD regression workflow"
git push
```

### 期望结果
- ✅ PR 阶段只跑改动的 flow（节省时间）
- ✅ merge 阶段 baseline-only 检查（快速）
- ✅ push 阶段完整回归 + dashboard artifact
- ✅ PR 评论自动附 dashboard.html 链接

---

## 常见问题 FAQ

### Q1: tdd-flow 找不到 flow.json？
**A**: 检查路径是否用绝对路径，或 `cd` 到项目根目录。

### Q2: dashboard.html sparkline 全灰？
**A**: history 中没有完整 run（缺 `passed_scenarios`）。重跑 tdd-flow 即可修复。

### Q3: only-changed 跑了所有 flow？
**A**: git 未追踪文件（含 untracked）。`git add` 后再跑，或用 `--tests-file` 限定。

### Q4: baseline 对比显示差异但实际相同？
**A**: 检查 instance_id / timestamp（已忽略）。如果仍显示差异，看 diff 输出逐字段对比。

### Q5: actor resolver 解析失败（`operator xxx not allowed`）？
**A**: actor 名是 role 名（"主管"/"出纳"）。改用：
- `applicant`（内置占位符）
- `tf_<role>`（顶级变量 + tf_manager="u_bob"）

---

## 进阶话题（30 分钟深入）

### Topic 1: 引擎 Bug 修复
详见 `ToT/ea/iterations/2026-09-23_applicant-bug.md`（substr → word boundary 修复）

### Topic 2: Decision Mem 协议
详见 `ToT/flows/fdep/RESPONSES.md` + 任意 `job_cards/*.md`

### Topic 3: 3 阶段环境流水线
详见 `ToT/sop/env-pipeline.md` + `ToT/sop/promote.py`

### Topic 4: pickup API + executor
详见 `ToT/sop/executor-api.md`

---

## 实战演练（60 分钟动手）

### 演练 1: 完整端到端（30 分钟）
1. 选一个真实业务场景（如"差旅审批"）
2. 用 flow_designer.py 设计
3. 跑 completeness 看到 50%
4. 补齐 5 文档 + Job Cards + baseline
5. 跑回 100%
6. 加到 tests.json
7. 跑 --all-flows 看到 dashboard

### 演练 2: Bug 修复流程（20 分钟）
1. 故意改 fdep.json 一个 expr
2. 跑 tdd-flow 看到 FAILED
3. 看 dashboard diff
4. 修复 + 重跑 → PASSED

### 演练 3: CI 集成（10 分钟）
1. 改 workflow 文件
2. push
3. 看 GitHub Actions 运行
4. 下载 artifact 看 dashboard.html

---

## 关键命令速查

```bash
# 完整性检查
./ToT/bin/jf python3 ToT/sop/flow_completeness.py <flow>.json

# EA 合规
./ToT/bin/jf python3 ToT/sop/ea-compliance.py

# 干跑
./ToT/bin/jf python3 ToT/sop/tdd-flow.py <flow>.json --dry-run

# 单流程实跑 + dashboard
./ToT/bin/jf python3 ToT/sop/tdd-flow.py <flow>.json --scenarios '...' --report-html dash.html

# 全部 flow 一键跑
./ToT/bin/jf python3 ToT/sop/tdd-flow.py --tests-file tests.json --all-flows

# only-changed
./ToT/bin/jf python3 ToT/sop/tdd-flow.py --tests-file tests.json --all-flows --only-changed

# baseline-only
./ToT/bin/jf python3 ToT/sop/tdd-flow.py --tests-file tests.json --all-flows --baseline-only

# 角色分配测试
./ToT/bin/jf python3 ToT/sop/promote.py list

# 设计新流程
./ToT/bin/jf python3 ToT/sop/flow_designer.py
```

---

## 成功标志

完成 3 个 demo 后，你应该能：

- ✅ 独立跑通 tdd-flow 各种模式
- ✅ 设计一个新流程并达 100% completeness
- ✅ 在 CI 中跑 EA 工具
- ✅ 解释 dashboard 各项指标
- ✅ 修复 actor resolver / decision mem 等常见问题

如果遇到难题：
- 看 `ToT/ea/iterations/`（27+ 个 iteration 记录）
- 看 `ToT/ea/roadmap.md`（架构 + 30 个 Pattern）
- 看 `ToT/README.md`（工作规范）

---

## 下一步学习路径

1. **了解引擎**：`vendor/jeeflow/engine.py` `_resolve_actors` / `_merge_exec_into_instance`
2. **了解 SPI**：`vendor/jeeflow/spi.py`（actor / org resolver）
3. **了解 SOP**：`ToT/sop/`（14 个 SOP + 9 个工具）
4. **了解 EA**：`ToT/ea/roadmap.md` + `ToT/ea/iterations/README.md`（26+ 圈飞轮索引）