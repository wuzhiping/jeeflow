# Iteration #32 · 2026-09-23 · W41 · 渐进式推进（4 步收档）

> **驱动**：主线重启后按"循序渐进"原则推进 4 个最小有效动作
> **核心成果**：✅ **A 归档回归 + C 脚本容错 + roadmap §9.7-9.9 补写 + D 跨环境测试** —— 全部 4 项均验证无 regression

---

## 1. 时间线（~30 分钟 / 4 步）

| 步骤 | 动作 | 结果 |
|------|------|------|
| **A** | 跑 `archive_flow` invoice-approval（验证 Iter#30 share.json 改动） | 取件码 27913 + md5 round-trip 一致 |
| **C** | 修 `issue_from_share_file_flow.py` 容错（3 道防线） | 999999 拒绝创建 issue + 重复检测已通 |
| **补写** | `ToT/ea/roadmap.md` §9.7-9.9 文档化 | roadmap 与 ea-compliance 现已对齐 |
| **D** | 跨环境兼容性测试（healthz + fdep getLastByName） | local-memory ↔ customer-test 结构一致 |

---

## 2. A · archive-flow 归档回归

### 2.1 触发
主线重启后第一个动作——验证 Iter#30 的 share.json 改动全链路 work。

### 2.2 执行
```bash
./ToT/bin/jf python3 ToT/sop/archive_flow.py invoice-approval
```

### 2.3 结果
- **取件码**: `27913`
- **下载 URL**: `https://abc.feg.com.tw/share/select/?code=27913`
- **tar.gz**: 21701 bytes
- **md5 round-trip**: `b7fe1cb2d3f0bea4d8bdb8f316ce374b`（原始=下载，✅ 完全一致）
- **share endpoint 显示**：`http://10.17.1.26:12345/share/file/ (from ToT/config/share.json)`
- **expire**：`7 day`（来自 `share.json.default_expire_value`）

### 2.4 Iter#30 回归验证
- ✅ `archive_flow.py` 不再硬编码 `SHARE_URL`
- ✅ `archive_flow.py` 不再硬编码下载 URL 模板
- ✅ `cli --expire-value` 接受 share.json 配置驱动
- ✅ ea-compliance §9.6.5 自动检查 share.json 存在合法

---

## 3. C · 脚本容错修复

### 3.1 触发
上次跑 `issue_from_share_file_flow.py 999999` 发现 bug——file-share 返回 JSON 错误响应（54 bytes）被脚本误判为"裸文件"，仍建立 issue。

### 3.2 根因
`step3_download` 第 104-106 行：
```python
if not target.exists() or target.stat().st_size < 100:
    log(f"❌ 下载失败：文件太小或不存在")
    return download_url, target.stat().st_size if target.exists() else 0, ""  # ← bug：download_url 仍 truthy
```
`main()` 检查 `if not download_url` 漏过（string truthy），仍走后续流程。

### 3.3 修复
1. **size < 100 → return (None, 0, "")**：直接拒绝
2. **HTTP status code 检查**（`curl -w "\n%{http_code}"`，4xx/5xx 拒绝）
3. **JSON 错误响应检测**（前 100 字节含 `{"code":` 开头，拒绝）

### 3.4 测试
| 输入 | 结果 |
|------|------|
| `999999`（未知取件码）| ❌ 文件过小（54 bytes）+ 显示内容预览 `{"code":404,...}` + 不创建 issue ✅ |
| `75829`（重复取件码）| 重复检测分支正常触发 ✅ |

---

## 4. roadmap §9.7-9.9 补写

### 4.1 触发
roadmap.md §9 之前只有 9.1-9.5 + 9.6（Iter#30 加），缺 9.7-9.9。ea-compliance 已实现但文档缺失。

### 4.2 内容
按 §9.6 风格镜像化 3 节，每节含"演进 / 原则"quote + 检查项列表：

| 节 | 项数 | 来源 |
|----|------|------|
| §9.7 环境流水线 | 4 | v1.4（Iter#6）|
| §9.8 路径可移植性 | 4 | v1.5（Iter#7）|
| §9.9 自动化 REPO_ROOT | 4 | v1.6（Iter#8）|

### 4.3 验证
roadmap §9 现 9 节齐全 45 项；ea-compliance 仍 44/44 PASS（实现与文档对齐）。

---

## 5. D · 跨环境兼容性测试（轻量）

### 5.1 触发
验证 fdep 在 local-memory 和 customer-test 上结构兼容。

### 5.2 状态盘点
| server | 状态 | fdep 部署 |
|--------|------|-----------|
| local-memory (8101) | ✅ UP, pg=down | defineId=20 |
| local-pg (8102) | ❌ 未启动 | — |
| org-server | ⏸ URL 占位 | — |
| customer-test | ✅ UP, pg=ok | defineId=1790050655064000 |

### 5.3 fdep getLastByName 跨环境比对
| 字段 | local-memory | customer-test | 一致 |
|------|--------------|---------------|------|
| name | fdep | fdep | ✅ |
| displayName | jeeFlow 协作主流程... | 同 | ✅ |
| type | collaboration | collaboration | ✅ |
| state | 1 (active) | 1 (active) | ✅ |
| **version** | 0 | 1 | ⚠ 演化差异 |
| **defineId** | 20 | 1790050655064000 | 不同（系统差异）|

### 5.4 结论
✅ **跨环境结构一致**；id/version 演化差异是预期（不同 PG 实例不同雪花 id）。

---

## 6. 度量（飞轮 32 圈累积）

| 指标 | #31 | **#32** |
|------|-----|---------|
| §9 检查项 | 44 | **44**（实现与文档对齐） |
| §9 节数 | 6 (9.1-9.6) | **9 (9.1-9.9)** |
| roadmap 文档完整度 | 缺 §9.7-9.9 | **§9 齐全** |
| archive-flow 取件码 | 75829 | **27913** + round-trip md5 一致 |
| 容错防线 | 1 (size < 100) | **3 (HTTP code / size / JSON)** |
| 跨环境迭代数 | 0 | **2 (local-memory + customer-test)** |
| skills 数 | 1 | **1** |
| EA roadmap 版本 | v3.8 | **v3.8** |

---

## 7. 闭环示意

```
┌── 主线重启：循序渐进 ─────────┐
↓                       │
A · archive-flow 回归     │ → Iter#30 改动 work
↓                       │
C · 修脚本容错            │ → 3 道防线
↓                       │
补 roadmap §9.7-9.9     │ → 文档与实现对齐
↓                       │
D · 跨环境 healthz        │ → 结构兼容验证
↓                       │
→ 飞轮第 32 圈 ✅           │
```

---

## 8. 经验沉淀

### 8.1 渐进式推进原则
- **A → C → B → D 顺序**：从小到大、从已有到新增、从轻量到重量
- **每个动作可独立验证**：失败不阻断下一步
- **git status 始终干净**：每次只动 1-3 个文件

### 8.2 容错修复的边界
- **3 道防线**：HTTP code / size / JSON 响应（前 100 字节）
- **优先 fail-fast**：JSON 检测放在 size 之后，但 size 检测已能 reject 大多数错误
- **错误信息透明**：显示响应内容预览便于调试

### 8.3 文档与实现的对齐
- **roadmap §9 vs ea-compliance §9.x.x**：之前缺 9.7-9.9，roadmap 与实现不对齐
- **维护节奏**：每次加新 §9.x 检查项时同步更新 roadmap
- **校验方式**：ea-compliance.py 跑通即视为 roadmap 现状可信

### 8.4 跨环境兼容性的最小验证
- **healthz**：最轻量，仅验证 server 存活
- **getLastByName**：验证流程定义内容一致（结构性）
- **同 scenario 跑**：完整业务验证（更重量，本轮未做）

---

## 9. 后续路线

| 路线 | 状态 |
|------|------|
| A · archive-flow 归档 | ✅ Iter#32 完成 |
| C · 修脚本容错 | ✅ Iter#32 完成 |
| roadmap §9.7-9.9 | ✅ Iter#32 完成 |
| D · 跨环境 healthz | ✅ Iter#32 完成（轻量） |
| B · 设计第 3 流程 | ⏸ 待下次会话 |
| 跨环境 scenario 跑 | ⏸ 待下次会话 |
| local-pg 启动 + 跨环境全跑 | ⏸ 待有 server 时 |

---

## 10. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第三十二轮迭代 · W41 渐进式推进（4 步收档）**：① **A · archive-flow 归档**：invoice-approval v0.6 取件码 27913，md5 round-trip 一致，验证 Iter#30 share.json 改动；② **C · 修 issue_from_share_file_flow.py 容错**：3 道防线（HTTP code / size < 100 / JSON 响应），999999 拒绝创建 issue；③ **roadmap §9.7-9.9 补写**：3 节齐全 12 项（环境流水线 / 路径可移植性 / 自动化 REPO_ROOT），roadmap 与 ea-compliance 对齐；④ **D · 跨环境测试**（healthz + fdep getLastByName）：local-memory ↔ customer-test 结构一致（name/displayName/type/state 同，version 演化差异 0 vs 1，defineId 系统差异）；⑤ **ea-compliance 44/44 PASS**（实现与文档对齐）；⑥ **git status 干净**：仅预期修改 + 新增 archive tar.gz；⑦ 新增 iterations/2026-09-23_progressive-push.md；⑧ iterations/README.md 刷新 31 → 32 圈。 |