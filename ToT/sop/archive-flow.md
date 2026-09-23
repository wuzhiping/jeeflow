# archive-flow SOP · 流程归档与分享

> **目的**：流程测试完成后，**归档**所有相关产出文件，**打包分享**，**清理本地临时数据**
> **用途**：1. 后续继续改流程测试 2. 转交 QA 在其他环境测试 3. DEV 复现 BUG 4. 多环境兼容性测试 5. 历史快照
> **触发时机**：流程达成 100% completeness + 所有 scenarios PASSED 后

---

## 1. 5 步流程概览

```
Step 1: 收集 SPI 背景数据（组织架构 + 用户信息）
  ↓
Step 2: 生成测试使用改进报告（含流程信息 + 背景数据 + 测试结果 + 改进建议）
  ↓
Step 3: 打包文件到 tar.gz（流程定义 + 文档 + 测试数据 + log + 报告）
  ↓
Step 4: 用 file-share skill 上传，返回取件码
  ↓
Step 5: 清理本地测试数据（invoice-approval 的 tdd/test_*.json 等）
```

---

## 2. 工具脚本

### 2.1 主脚本：`ToT/sop/archive_flow.py`

```bash
# 用法
./ToT/bin/jf python3 ToT/sop/archive_flow.py <flow-id> [--clean]

# 示例：归档 invoice-approval 并清理
./ToT/bin/jf python3 ToT/sop/archive_flow.py invoice-approval --clean

# 示例：仅归档不清理（保留本地数据）
./ToT/bin/jf python3 ToT/sop/archive_flow.py fdep
```

### 2.2 自动完成
1. **调用 SPI API** 获取组织架构图 + 用户信息（背景数据）
2. **读 tests.json** 获取该 flow 的 scenarios 配置
3. **读最新 dashboard.json** 获取最近测试结果
4. **生成报告**：`archive/<datetime>_<flow-id>/report.md`
5. **打包**：`archive/<datetime>_<flow-id>.tar.gz`
6. **file-share 上传**：返回取件码
7. **（--clean 时）清理**该 flow 的 tdd/test_<flow-id>*.json/md + baseline

---

## 3. 报告模板

### 3.1 章节结构
1. **流程基本信息**：name / displayName / version / node count / edge count
2. **测试结果**：scenarios / passed / failed / elapsed
3. **组织架构图**：部门树 + 关键角色（来自 SPI）
4. **关键用户**：参与流程的角色对应用户
5. **改进建议**：基于 27+ 圈飞轮经验沉淀
6. **附件清单**：tar.gz 内文件清单

### 3.2 示例输出（部分）
```markdown
# 流程测试报告 · invoice-approval · 2026-09-23

## 1. 流程基本信息
- name: invoice-approval
- displayName: 发票审批
- version: 0.6
- 节点: 6 / 边: 6

## 2. 测试结果（最近 5 次跑）
- 平均通过率: 100% (6/6 scenarios)
- 平均耗时: 0.7s

## 3. 组织架构图（来自 SPI /api/spi/depts）
研发部 (D01) ── leader=u_rd_dir, main_leader=u_cto
├── 前端组 (D02) ── leader=u_fe_lead
└── 后端组 (D03) ── leader=u_be_lead
└── 架构组 (D04) ── leader=u_arch

## 4. 关键用户
| 角色 | 用户 | 部门 | 岗位 |
|------|------|------|------|
| 员工 | u_alice | D01 | 工程师 |
| 主管 | tf_manager (u_bob) | -- | -- |
| 出纳 | tf_treasurer (u_carol) | -- | -- |

## 5. 改进建议
- ✅ 已使用 actor resolver 3 种语法
- ⚠️ submit 节点建议改用统一 form template
- 💡 可加 baseline 自动重生成 cron job
```

---

## 4. 打包内容清单

```
archive/2026-09-23_invoice-approval/
├── report.md                                  # 测试使用改进报告
├── flows/
│   ├── invoice-approval.json                  # 流程定义
│   └── invoice-approval/                      # 流程文档目录
│       ├── README.md
│       ├── ROLES.md
│       ├── NODES.md
│       ├── CHANGELOG.md
│       ├── RESPONSES.md
│       └── job_cards/
│           ├── job_card_submit.md
│           ├── job_card_decision_amount.md
│           ├── job_card_approve.md
│           └── job_card_pay.md
├── tdd/
│   ├── test_invoice-approval_baseline_v0_1_*.json   # 最新 baseline
│   ├── test_invoice-approval_baseline_v0_1_*.md     # 最新 baseline md
│   └── test_invoice-approval_*.json                  # 最近几次跑（不含已清理的）
├── tests.json                                   # tests.json 中该 flow 的配置
└── logs/
    └── tdd-flow-runs.log                        # 最近运行的 log（可选）
```

---

## 5. 取件码使用

```
✅ 上传成功：<flow-id>.tar.gz
取件码: 654321
下载链接: https://abc.feg.com.tw/share/select/?code=654321
有效期: 7 天
```

---

## 6. CI 集成（可选）

```yaml
- name: Archive flow on release
  if: startsWith(github.ref, 'refs/tags/v')
  run: |
    FLOW_ID=$(echo ${{ github.ref }} | sed 's|refs/tags/v||')
    ./ToT/bin/jf python3 ToT/sop/archive_flow.py $FLOW_ID --clean
```

---

## 7. 注意事项

- **清理前必须确认**：`--clean` 不可逆，会删除本地 baseline + test results
- **baseline 保留**：建议保留最近 3 个 baseline，旧的可以删
- **环境依赖**：SPI API 必须可用（要启动 engine + SPI_FOLDER）
- **file-share 有效期**：默认 7 天，可在脚本中改 `--expire_value=30`

---

## 8. 相关文档

- [`ToT/sop/flow-completeness.md`]（跑 100% 之前用）
- [`ToT/sop/tdd-flow.md`]（test baseline 来源）
- [`ToT/ea/DEMO.md`]（团队培训）

---

## 9. 配置文件（v0.2 起）

### 9.1 单一真相源：`ToT/config/share.json`

upload endpoint、download URL template、过期默认值等**不再硬编码**，全部从 `ToT/config/share.json` 读取：

```json
{
  "share": {
    "upload_url": "http://10.17.1.26:12345/share/file/",
    "download_url_template": "https://abc.feg.com.tw/share/select/?code={code}",
    "expire_unit": "day",
    "default_expire_value": 7,
    "max_expire_value": 365
  }
}
```

### 9.2 切换分享服务

```bash
# 编辑 endpoint
$EDITOR ToT/config/share.json

# 验证（dry-run 不实际上传）
./ToT/bin/jf python3 ToT/sop/archive_flow.py <flow-id> --dry-run

# 期望输出包含：share endpoint: <你填的 upload_url>
```

### 9.3 CLI 过期参数

| 参数 | 含义 | 默认 |
|------|------|------|
| `--expire-value N` | 过期数值 | `share.json` 的 `default_expire_value` (7) |
| `--expire-days N` | [兼容旧版] 等同 `--expire-value` | 同上 |

`expire_unit`（day/hour/minute）由 `share.json` 统一控制，避免脚本和配置不一致。

### 9.4 与 `servers.json` 的关系

| 配置 | 职责 |
|------|------|
| `ToT/config/servers.json` | 流程引擎 server 流水线（local-memory / local-pg / org-server / customer-test） |
| `ToT/config/share.json` | 外部文件分享服务（file-share skill 的 endpoint） |

两者互补，不重叠。修改其中任一文件不影响另一个。

---

## 10. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **初稿**：5 步流程 + 报告模板（8 章节）+ CLI（`--clean` / `--expire-days` / `--no-upload`）。 |
| **v0.2** | **2026-09-23** | **配置集中化**：① 新增 `ToT/config/share.json`（upload_url / download_url_template / expire_unit / default_expire_value）；② `archive_flow.py` 移除硬编码 `SHARE_URL` + 下载 URL；③ 新增 `load_share_config()` 加载器；④ CLI 改 `--expire-value`（兼容 `--expire-days`）；⑤ §9.6.5 ea-compliance 检查 share.json 存在；⑥ ea-compliance 44/44 PASS。 |