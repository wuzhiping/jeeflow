# SOP: 环境配置管理 (env-config)

> **所属**：组织 SOP 集（与 `customer-data-reset` 互补）
> **场景**：管理流程服务器配置（URL / backend / SSH 等），避免散落硬编码
> **永久规则**：见 `ToT/README.md` §1 + §11
> **配套工具**：`ToT/sop/server_config.py`（配置加载器）

---

## 1. 适用场景

| ✅ 适用 | ❌ 不适用 |
|--------|-----------|
| 修改客户服务器 URL（如 `abc.feg.cn` → 新域名） | 引擎代码本身 |
| 切换默认目标（local-pg ↔ customer-test） | 临时调试（用环境变量即可） |
| 新增 / 移除环境（如生产环境） | 备份策略 |
| 自动化脚本统一读 URL | — |

## 2. 单一真相源

**所有脚本 / SOP / 文档必须读 `ToT/config/servers.json`，不硬编码 URL。**

```
ToT/
├── config/
│   └── servers.json      ← 唯一真相源（4 server 完整定义）
└── sop/
    └── server_config.py  ← 加载器（CLI + API）
```

### servers.json 字段

| 字段 | 必填 | 用途 |
|------|------|------|
| `servers.<name>.url` | ✅* | server URL（生产环境可 null） |
| `servers.<name>.backend` | ✅ | memory / pg |
| `servers.<name>.purpose` | ✅ | 用途描述 |
| `servers.<name>.spi_folder` | ✅ | 关联 SPI 文件夹 |
| `servers.<name>.share_pg_with` | ❌ | 共享 PG 的 server 名列表 |
| `servers.<name>.ssh` | ❌ | SSH 接入信息（无 AI 权限） |
| `servers.<name>.notes` | ❌ | 备注（启动命令等） |
| `active` | ✅ | 默认 active server 名 |
| `default_target` | ✅ | 默认目标（= active） |
| `default_spi_folder` | ✅ | 默认 SPI 文件夹 |

## 3. 执行步骤

### Step 1 · 修改配置（添加/切换/移除）

```bash
# 编辑
$EDITOR ToT/config/servers.json

# 验证
python3 ToT/sop/server_config.py --list

# 期望：4 server 全部存在 + active 指向期望的 server
```

### Step 2 · 切换默认目标（无需改代码）

```json
// 在 servers.json 中修改
{
  "active": "customer-test",     // ← 改成 "local-pg" / "customer-test" 等
  "default_target": "customer-test"
}
```

所有脚本（demo_*.py / ea-compliance.py）下次跑会自动用新 active。

### Step 3 · 跑合规检查

```bash
python3 ToT/sop/ea-compliance.py
# §9.6 配置集中化：4 项必须全 PASS
```

### Step 4 · 文档同步

修改 `servers.json` 后，需要更新：

| 文件 | 同步位置 |
|------|----------|
| `ToT/ea/roadmap.md §7` | 三环境拓扑表 |
| `ToT/HANDBOOK.md` | 快速开始 |
| `ToT/ea/PPT.md` | Slide 6 / 9 数据 |

## 4. 风险与回滚

| 风险 | 缓解 |
|------|------|
| 误改 active 切到生产（如果有） | active 默认指向 test；修改前先核对 |
| servers.json 损坏 | git 备份 + 留档 SOP（commit 前必须通过 JSON 校验） |
| 第三方脚本不读 config | §9.6.3 合规检查会失败 |
| 客户服务器域名变更 | 改 servers.json 即可；老留档保留旧 URL（历史） |

## 5. 完整命令清单

```bash
# === 查询 ===
python3 ToT/sop/server_config.py                # 显示 active URL
python3 ToT/sop/server_config.py --active        # 显示 active 名
python3 ToT/sop/server_config.py --list         # 列出所有 server
python3 ToT/sop/server_config.py customer-test   # 显示指定 URL

# === 在脚本中使用 ===
python3 -c "
import sys; sys.path.insert(0, 'ToT/sop')
from server_config import get_url
print(get_url('customer-test'))
"

# === 验证合规 ===
python3 ToT/sop/ea-compliance.py   # §9.6 必须 4/4
```

## 6. 与其他 SOP 的关系

| SOP | 关系 |
|-----|------|
| `customer-data-reset` | reset 客户服务器 = 修改 config 中 "customer-test" 的目标 |
| `engine-deploy` | 引擎代码 push = 不影响 config（config 是数据不是代码） |
| `ea-compliance` | §9.6 验证 config 一致性 |
| `customer-data-reset` SOP 中的 curl 命令 | 仍可硬编码 URL（历史）；新脚本推荐读 config |

## 7. 关联文档

- `ToT/config/servers.json` — 配置本体
- `ToT/sop/server_config.py` — 加载器
- `ToT/ea/roadmap.md §7` — 三环境拓扑
- `ToT/HANDBOOK.md` — 快速开始

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-22** | **初稿**：单一真相源（`ToT/config/servers.json`）+ 加载器（`server_config.py`）+ §9.6 合规检查（4 项） + 切换流程 + 风险回滚 + 与其他 SOP 关系。 |