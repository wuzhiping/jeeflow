# Iteration #28 · 2026-09-23 · W38 · archive-flow SOP · 流程归档与分享

> **驱动**：流程测试完成后需要跨环境分享 + 历史快照 + 本地清理
> **核心成果**：✅ **`ToT/sop/archive_flow.py`** 一键完成：报告生成 + 打包 + file-share 上传 + 清理

---

## 1. 时间线（~30 分钟）

| 时段 | 工作 |
|------|------|
| 0~10 min | 创建 `ToT/sop/archive-flow.md` SOP 文档 |
| 10~25 min | 实现 `ToT/sop/archive_flow.py` 工具脚本 |
| 25~30 min | 实跑 invoice-approval + file-share 上传 + 清理验证 |

---

## 2. SOP 5 步流程

```
Step 1: 收集 SPI 背景数据（组织架构图 + 用户信息）
  ↓
Step 2: 生成测试使用改进报告（含背景数据 + 测试结果 + 改进建议）
  ↓
Step 3: 打包文件到 tar.gz（流程定义 + 文档 + 测试数据 + 报告）
  ↓
Step 4: 用 file-share skill 上传，返回取件码
  ↓
Step 5: 清理本地测试数据（保留最近 3 个 baseline）
```

---

## 3. archive_flow.py 实现

### 3.1 主流程
```python
1. fetch_spi_users() → SPI /api/spi/users → 用户列表（背景）
2. fetch_spi_depts() → SPI /api/spi/depts → 部门树（背景）
3. fetch_test_results() → tests.json + dashboard.json → 配置 + 结果
4. fetch_flow_meta() → flow.json → node/edge 统计
5. collect_files() → 收集所有相关文件到 work_dir
6. generate_report() → 模板生成 report.md（8 章节）
7. create_archive() → tar -czvf 打包
8. upload_to_share() → curl POST /share/file/ → 取件码
9. cleanup_local() → 清理（保留最近 3 baseline）
```

### 3.2 CLI
```bash
./ToT/bin/jf python3 ToT/sop/archive_flow.py <flow-id> [--clean] [--expire-days N] [--no-upload]
```

---

## 4. 报告模板（8 章节）

1. **流程基本信息**：name / version / 节点 / 边数
2. **测试配置**：来自 tests.json
3. **测试结果**：baseline + dashboard 摘要
4. **组织架构图**：部门树（SPI /api/spi/depts）
5. **关键用户**：用户表（SPI /api/spi/users，含 uid/name/post/dept/roles）
6. **改进建议**：基于 27+ 圈 EA 飞轮经验
7. **附件清单**：tar.gz 内文件清单
8. （自动生成）

---

## 5. 测试证据（invoice-approval 实跑）

### 5.1 报告样例
```markdown
# 流程测试报告 · invoice-approval · 2026-09-23 08:09:39

## 1. 流程基本信息
- name: invoice-approval
- displayName: 发票审批：员工提交 → 财务初审 → 主管复核 → 出纳付款 → 完成
- version: 0.5
- 节点数: 6, 边数: 6
- 节点类型: {'start': 1, 'task': 3, 'decision': 1, 'end': 1}

## 4. 组织架构图（来自 SPI /api/spi/depts）
- 研发部 (D01) — size=3, leader=u_rd_dir, main_leader=u_cto
- 前端组 (D02) — size=3, leader=u_fe_lead, main_leader=u_rd_dir
- 后端组 (D03) — size=4, leader=u_be_lead, main_leader=u_rd_dir
- 架构组 (D04) — size=1, leader=u_arch, main_leader=u_cto
- 总经办 (D99) — size=2, leader=u_ceo, main_leader=u_ceo
- FDEP协作组 (DFDEP) — size=1, leader=u_fdp_pm, main_leader=u_fdp_pm

## 5. 关键用户（来自 SPI /api/spi/users）
| uid | 姓名 | 岗位 | 部门 | 角色 |
|-----|------|------|------|------|
| u_arch | 陈静 | 架构师 (P8) | D04 | architect |
| u_be_eng | 钱琳 | 后端工程师 (P5) | D03 | engineer |
| ... 14 个用户
```

### 5.2 file-share 上传
```
✅ 上传成功: 20260923-080949_invoice-approval.tar.gz
   取件码: 75829
   下载: https://abc.feg.com.tw/share/select/?code=75829
   有效期: 7 天
```

### 5.3 清理验证
```
清理前：118 个文件
清理后：6 个文件（保留 3 个最新 baseline × .json/.md）
       ✅ tests.json 仍能跑（baseline 对比无差异）
       ✅ ea-compliance 43/43 PASS
```

### 5.4 tar.gz 内容（33 个文件）
```
archive_invoice-approval/
├── report.md                                       # 测试使用改进报告
├── flows/
│   ├── invoice-approval.json                       # 流程定义
│   └── invoice-approval/                           # 文档
│       ├── README.md / ROLES.md / NODES.md
│       ├── CHANGELOG.md / RESPONSES.md
│       └── job_cards/ (4 张 Job Card)
├── tdd/
│   ├── test_invoice-approval_baseline_v0_3_*.json  # 3 个最新 baseline
│   ├── test_invoice-approval_baseline_v0_3_*.md
│   ├── test_invoice-approval_baseline_v0_4_*.json
│   ├── test_invoice-approval_baseline_v0_4_*.md
│   ├── test_invoice-approval_baseline_v0_5_*.json
│   ├── test_invoice-approval_baseline_v0_5_*.md
│   └── test_invoice-approval_2026*.json/md        # 最近几次跑
└── tests.json                                       # tests.json 完整
```

---

## 6. 闭环示意

```
┌── "流程测完需要分享 + 清理" ──┐
↓                       │
写 archive-flow.md SOP  │
↓                       │
写 archive_flow.py      │
↓                       │
实跑 invoice-approval   │
↓                       │
✓ SPI API 14 users + 6 depts  │
↓                       │
✓ 报告 + 打包 + file-share │
↓                       │
✓ 清理 112 个文件         │
↓                       │
→ 飞轮第 28 圈（归档）✅ │
```

---

## 7. 度量（飞轮 28 圈累积）

| 指标 | Iter#27 | **Iter#28** |
|------|---------|-------------|
| §9 检查项 | 43 | **43** |
| **archive SOP** | ❌ | **✅ archive-flow.md + archive_flow.py** |
| **file-share 集成** | ❌ | **✅ 取件码自动返回** |
| **本地清理** | ❌ | **✅ 112 文件自动清理** |
| 工具数 | 9 | **10 (+archive_flow)** |

**关键变化**：从"流程测完数据散乱"→"一键归档 + 分享 + 清理"。

---

## 8. 经验沉淀

### 8.1 archive SOP 设计原则
- **5 步流程**：背景 → 报告 → 打包 → 分享 → 清理
- **保留基线**：3 个最新 baseline + tests.json
- **背景数据**：SPI API 提供组织架构 + 用户信息作为参考
- **file-share 集成**：自动上传 + 返回取件码

### 8.2 报告模板设计原则
- **8 章节**：基本信息 + 配置 + 结果 + 组织 + 用户 + 改进 + 附件
- **可读性**：markdown + table + emoji（🟢🟡🔴）
- **可追溯**：每个数据点都有出处（SPI / tests.json / dashboard.json）

### 8.3 清理策略
- ✅ 删除所有 `test_<flow>_<ts>.json/md`（临时测试结果）
- ✅ 删除 baseline v0_1 ~ v0_(N-3)（旧 baseline）
- ✅ 保留 baseline v0_(N-2) ~ v0_N（最近 3 个）
- ✅ 保留 tests.json（CI 配置）
- ✅ 保留 dashboard.json / dashboard.html（最近一次 dashboard）

---

## 9. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第二十八轮迭代 · W38 archive-flow SOP**：① **`ToT/sop/archive-flow.md`** SOP 文档（5 步流程 + 报告模板）；② **`ToT/sop/archive_flow.py`** 工具脚本（SPI API + tests.json + dashboard + file-share + 清理）；③ **8 章节报告模板**（基本信息/配置/结果/组织/用户/改进/附件）；④ **file-share 集成**：cURL 上传 + 取件码自动返回；⑤ **实跑 invoice-approval**：14 users + 6 depts + 27 文件 → tar.gz 25364 bytes；⑥ **清理 112 个文件**（保留最近 3 个 baseline）；⑦ **取件码 75829**（7 天有效期）；⑧ **ea-compliance 43/43 PASS**；⑨ **SOP 数 14 → 15**；⑩ 新增 iterations/2026-09-23_archive-flow.md。 |