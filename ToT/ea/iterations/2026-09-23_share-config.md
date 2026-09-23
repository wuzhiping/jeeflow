# Iteration #30 · 2026-09-23 · W39 · share config 集中化 · archive_flow endpoint 真相源

> **驱动**：`ToT/sop/archive_flow.py` 内 `SHARE_URL = "http://10.17.1.26:12345/share/file/"` 与下载 URL 模板 `https://abc.feg.com.tw/share/select/?code={code}` 都是硬编码，违反"§9.6 配置集中化"原则。
> **核心成果**：✅ **`ToT/config/share.json`** 单一真相源 + `archive_flow.py` 全程读 config + `ea-compliance §9.6.5` 自动校验。

---

## 1. 时间线（~15 分钟）

| 时段 | 工作 |
|------|------|
| 0~3 min | 创建 `ToT/config/share.json`（v1.0 schema） |
| 3~8 min | 改 `archive_flow.py`（`load_share_config()` + 移除硬编码 URL + 改 `--expire-value`） |
| 8~10 min | 更新 `archive-flow.md`（§9 配置说明 + v0.2 changelog） |
| 10~12 min | 加 `ea-compliance §9.6.5` 检查 |
| 12~15 min | dry-run × 3 + ea-compliance + tdd-flow 回归 |

---

## 2. 单一真相源：`ToT/config/share.json`

```json
{
  "$schema_version": "1.0",
  "comment": "外部文件分享服务配置 —— archive_flow.py 的 endpoint 真相源",
  "share": {
    "upload_url": "http://10.17.1.26:12345/share/file/",
    "download_url_template": "https://abc.feg.com.tw/share/select/?code={code}",
    "expire_unit": "day",
    "supported_expire_units": ["day", "hour", "minute"],
    "default_expire_value": 7,
    "max_expire_value": 365
  }
}
```

### 2.1 与 `servers.json` 的职责划分

| 配置 | 职责 | 加载器 |
|------|------|--------|
| `ToT/config/servers.json` | 流程引擎 server 流水线（local-memory / local-pg / org-server / customer-test） | `server_config.py` |
| **`ToT/config/share.json`**（新） | 外部文件分享服务（file-share skill endpoint） | **`archive_flow.load_share_config()`** |

两者互补、不重叠，未来新增外部服务（email / notification / etc.）可平行新建。

---

## 3. archive_flow.py 改造

### 3.1 移除硬编码

| 行 | 改前 | 改后 |
|----|------|------|
| 27 | `SHARE_URL = "http://10.17.1.26:12345/share/file/"` | ❌ 删除 |
| 30 | `SPI_API = os.environ.get("SPI_API", ...)` | ✅ 保留（env 优先） |
| 331 | `url = f"https://abc.feg.com.tw/share/select/?code={code}"` | `url = download_template.format(code=code)` |
| 518 | `log(f"   下载: https://abc.feg.com.tw/share/select/?code={code}")` | `log(f"   下载: {share_config['download_url_template'].format(code=code)}")` |

### 3.2 新增 loader

```python
def load_share_config(path: Path = SHARE_CONFIG_PATH) -> dict:
    """加载 share.json（archive_flow 的 share endpoint 真相源）"""
    if not path.exists():
        raise FileNotFoundError(f"share.json not found at {path}")
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    if "share" not in cfg:
        raise KeyError(f"share.json missing 'share' block at {path}")
    return cfg["share"]
```

### 3.3 CLI 改动

| 参数 | 改前 | 改后 |
|------|------|------|
| `--expire-days 7` | 唯一过期参数 | 改为**兼容旧版**（标记 `[兼容旧版]`） |
| — | — | **新增** `--expire-value`（语义更准，单位由 share.json 决定） |

`upload_to_share()` 现在签名：

```python
def upload_to_share(tar_path, expire_value=None, share_config=None):
    cfg = share_config or load_share_config()
    upload_url = cfg["upload_url"]
    download_template = cfg["download_url_template"]
    expire_unit = cfg.get("expire_unit", "day")
    if expire_value is None:
        expire_value = cfg.get("default_expire_value", 7)
    # ... curl POST upload_url + form ...
    url = download_template.format(code=code)
```

---

## 4. ea-compliance §9.6.5 新增检查

```python
# 5. share.json 存在且合法（archive_flow 的 endpoint 真相源）
share_exists = SHARE_CONFIG_PATH.exists()
share_valid = False
share_fields = []
if share_exists:
    try:
        sc = json.loads(SHARE_CONFIG_PATH.read_text(encoding="utf-8"))
        s = sc.get("share", {})
        share_valid = (
            "upload_url" in s
            and "download_url_template" in s
            and "{code}" in s["download_url_template"]
        )
        share_fields = list(s.keys())
    except Exception:
        pass
items.append(check_item("config", "9.6.5", "ToT/config/share.json 存在且合法（archive_flow 真相源）",
                         share_exists and share_valid,
                         f"fields={share_fields}" if share_valid else "missing or invalid"))
```

§9.6 从 4 项升级为 **5 项**。

---

## 5. 验证证据

### 5.1 dry-run × 3

| 命令 | 输出 |
|------|------|
| `archive_flow.py invoice-approval --dry-run --no-upload` | `share endpoint: http://10.17.1.26:12345/share/file/` + `expire: 7 day` |
| `archive_flow.py invoice-approval --dry-run --no-upload --expire-value 30` | `expire: 30 day` |
| `archive_flow.py invoice-approval --dry-run --no-upload --expire-days 14` | `expire: 14 day`（兼容旧版） |

### 5.2 ea-compliance：43 → **44/44 PASS**

```
§9.6 配置集中化: 5/5 PASS
  ✓ 9.6.1: ToT/config/servers.json 存在且合法
  ✓ 9.6.2: server_config.py 加载器存在
  ✓ 9.6.3: ea-compliance.py 不硬编码 URL（读 config）
  ✓ 9.6.4: config 含 customer-test 配置
  ✓ 9.6.5: ToT/config/share.json 存在且合法（archive_flow 真相源）
OVERALL: 44/44 PASS (100.0%)
```

### 5.3 tdd-flow 回归：2/2 flows 6/6 scenarios

```
flows: 2/2 PASSED
scenarios: 6/6 OK
all_passed: True
```

---

## 6. 闭环示意

```
┌── "archive_flow.py SHARE_URL 写死了" ──┐
↓                          │
读 env-config SOP §2 原则： │
"所有脚本不硬编码 URL"       │
↓                          │
新建 ToT/config/share.json  │
↓                          │
改 archive_flow.py 加载     │
↓                          │
✓ dry-run × 3 全对          │
✓ ea-compliance 44/44      │
✓ tdd-flow 2/2 flows        │
↓                          │
→ 飞轮第 30 圈 ✅            │
```

---

## 7. 度量（飞轮 30 圈累积）

| 指标 | Iter#29 | **Iter#30** |
|------|---------|-------------|
| §9 检查项 | 43 | **44** |
| **share.json** | ❌ | **✅ v1.0（upload + download + expire）** |
| **archive_flow 硬编码 URL** | 2 处 | **0 处** |
| 配置数 | 1 (servers.json) | **2 (+share.json)** |
| 工具数 | 10 | **10** |
| SOP 数 | 15 | **15**（archive-flow.md 升级 v0.2） |

**关键变化**：从"share endpoint 散落硬编码"→"share.json 单一真相源 + 自动校验"。

---

## 8. 经验沉淀

### 8.1 配置集中化原则的延展

- **Servers 与 Share 是不同域**：servers.json 管"流程引擎 server 流水线"，share.json 管"外部文件分享服务"，应分文件不合并
- **CLI 参数语义化**：从 `--expire-days` → `--expire-value` + `expire_unit` 来自 config，避免"单位由参数名决定"的歧义
- **向后兼容**：保留 `--expire-days` 标记 `[兼容旧版]`，避免破坏既有调用方（CI / 留档脚本）

### 8.2 §9.6 检查的演进

| Iter | 检查项 | 检查数 |
|------|--------|--------|
| #19 | servers.json 存在 + 合法 | 1 |
| #20 | server_config.py loader | 2 |
| #21 | ea-compliance.py 不硬编码 | 3 |
| #22 | 含 customer-test | 4 |
| **#30** | **share.json 存在 + 合法** | **5** |

原则："凡是脚本可能依赖的外部端点，都要有 §9.6 检查"。

### 8.3 通用化模板

未来新增外部服务（email / notification / monitoring）时：
1. 新建 `ToT/config/<service>.json`（含 endpoint + auth + 必要字段）
2. SOP 工具 `load_<service>_config()` 加载（轻量时 inline 即可）
4. 加 `§9.6.X` 检查（`exists and valid`）
3. 改 SOP 工具用 config 替换硬编码

---

## 9. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第三十轮迭代 · W39 share config 集中化**：① **新建 `ToT/config/share.json`**（v1.0：upload_url + download_url_template + expire_unit + default_expire_value + max_expire_value）；② **`archive_flow.py` 移除 2 处硬编码 URL**（`SHARE_URL` + 下载模板），新增 `load_share_config()` loader；③ **CLI `--expire-value` 替代 `--expire-days`**（兼容旧版）；④ **`archive-flow.md` §9 + v0.2 changelog**；⑤ **`ea-compliance §9.6.5`** 新增 share.json 存在合法检查（§9.6 4 → 5 项）；⑥ **dry-run × 3 全对**；⑦ **ea-compliance 44/44 PASS**；⑧ **tdd-flow 回归 2/2 flows 6/6 scenarios**；⑨ 配置数 1 → 2；⑩ 新增 iterations/2026-09-23_share-config.md。 |