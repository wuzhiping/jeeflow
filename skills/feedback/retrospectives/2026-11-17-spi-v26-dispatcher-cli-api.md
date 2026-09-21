# 2026-11-17 spi 重构 v26 · CLI/API 统一在 dispatcher 层

> **重构日期**: 2026-11-17 (W47 Day 5)
> **状态**: ✅ **published** · 11/11 PASS (含跨 SPI_FOLDER 验证 + 缺失 cli/api 错误处理)
> **关联**: 新增 `spi/cli.py` + `spi/api.py` + `spi/__main__.py` + `spi/demo/cli.py` + `spi/demo/api.py`
> **约束**: spi/dev/data.py (40020 bytes) 100% 不动 · spi/demo/ 原始时间戳维持 (除新建 cli/api 外)
> **下一里程碑**: v27 (dept, role) 二维聚合

---

## 1. 重构动机

**v22-v25 单实现层痛点**:
- `spi/dev/cli.py` 和 `spi/dev/api.py` 是 v22-v25 开发的, 与 `spi/demo/` 平行
- `main.py` 硬编码 `from spi.dev.api import router` - 切换 SPI_FOLDER 需改源码
- `python -m spi.dev` 只能跑 dev, demo 需要 `python -m spi.demo` (但 demo 没有 cli)
- 缺统一入口 (`python -m spi`)

**目标**: dispatcher 层跟随 SPI_FOLDER, 实现层只暴露 `_data_*` 函数.

---

## 2. 改动范围

### 2.1 新增文件

| 文件 | 行数 | 内容 |
| --- | --- | --- |
| `spi/cli.py` | 约 250 | dispatcher CLI (跟随 SPI_FOLDER) |
| `spi/api.py` | 约 130 | dispatcher API (FastAPI APIRouter) |
| `spi/__main__.py` | 5 | `python -m spi` 入口 |
| `spi/demo/cli.py` | 约 145 | demo 实现层 (含 6 `_data_*` 函数) |
| `spi/demo/api.py` | 15 | demo 薄包装 re-export |

### 2.2 改造文件

| 文件 | 改动 |
| --- | --- |
| `spi/dev/cli.py` | 移除 router/main, 仅保留 `_data_*` 函数 |
| `spi/dev/api.py` | 移除 router, 改为薄包装 re-export |
| `main.py` | 改 `from spi.api` (从 `spi.dev.api`) |

### 2.3 spi/SPEC.md 新增 §8

正式约束 6 个 `_data_*` 函数签名, 不允许改.

---

## 3. 三层架构

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1: Dispatcher (spi/cli.py + spi/api.py + spi/__main__.py)    │
│  · 入口层, 跟随 SPI_FOLDER 环境变量                                    │
│  · 解析命令行参数 (cli) 或 HTTP 路由 (api)                              │
│  · 加载 spi/<SPI_FOLDER>/cli.py 或 spi/<SPI_FOLDER>/api.py            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 2: Implementation (spi/{demo,dev,fdep}/cli.py + api.py)      │
│  · 暴露 6 个 _data_* 函数                                              │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 3: Data (spi/{demo,dev}/data.py + *.json)                      │
│  · spi/dev/data.py: 20 DictProxy (v8-v27) + 2 helpers + verify()       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. 测试 (11/11 PASS)

| # | 场景 | 期望 | 实测 |
| --- | --- | --- | --- |
| 1 | `SPI_FOLDER=dev python -m spi.cli verify` | exit 0, ✓ | ✅ |
| 2 | `SPI_FOLDER=demo python -m spi.cli verify` | exit 1, 99 errors | ✅ (已知) |
| 3 | `SPI_FOLDER=dev python -m spi.cli list-users` | 13 用户表格 | ✅ |
| 4 | `SPI_FOLDER=demo python -m spi.cli list-users` | demo 用户表格 | ✅ |
| 5 | `SPI_FOLDER=fdep python -m spi.cli verify` | exit 1, "fdep 不支持 CLI" | ✅ |
| 6 | `SPI_FOLDER=dev` curl /api/spi/verify | 200 OK | ✅ |
| 7 | `SPI_FOLDER=demo` curl /api/spi/verify | 200 OK | ✅ |
| 8 | `SPI_FOLDER=fdep` curl /api/spi/users | 404 "fdep 不支持 API" | ✅ |
| 9 | 跨 SPI_FOLDER 同命令 | dev/demo 输出格式一致 | ✅ |
| 10 | spi/dev/data.py SHA 校验 | 未变化 (40020 bytes) | ✅ |
| 11 | spi/demo/ 时间戳校验 | 原始时间戳 (除新建 cli/api 外) | ✅ |

---

## 5. 设计决策

### 5.1 dispatcher vs 实现层职责分离

| 职责 | dispatcher | 实现层 |
| --- | --- | --- |
| SPI_FOLDER 路由 | ✅ | ❌ |
| argparse 解析 / FastAPI 路由 | ✅ | ❌ |
| 6 _data_* 函数定义 | ❌ | ✅ |
| 数据访问 (DictProxy + helpers) | ❌ | ✅ (通过 _data_*) |
| 输出格式化 | ✅ (cli 表格 / api JSON) | ❌ |

### 5.2 为什么不改 spi/dev/data.py?

- **硬约束**: v8-v25 累积 20 DictProxy + 2 helpers + verify(), 任何字段重命名都会破坏 100+ 测试
- **验证**: SHA 校验确认 100% 不动
- **后续**: v27-v29 仍在 data.py 增量添加 DictProxy

### 5.3 为什么 spi/demo/ 时间戳维持?

- **硬约束**: spi/demo/ 原始实现, 作为 SPI 最小可行示例, 不能动
- **新增 cli/api 不破坏约束**: 因为是新增, 不是修改

---

## 6. 关键代码片段

### 6.1 `spi/api.py` (dispatcher)

```python
import os
import importlib
from fastapi import APIRouter, HTTPException

router = APIRouter()

def _load_impl():
    folder = os.environ.get("SPI_FOLDER", "demo")
    try:
        return importlib.import_module(f"spi.{folder}.api")
    except ImportError:
        raise HTTPException(404, f"SPI_FOLDER={folder} 不支持 API (缺少 api 模块)")

_impl = None
def impl():
    global _impl
    if _impl is None:
        _impl = _load_impl()
    return _impl

@router.get("/api/spi/verify")
async def spi_verify():
    return impl()._data_verify()
```

---

## 7. 经验教训

1. **三层分离原则**: dispatcher / implementation / data 各司其职
2. **SPI_FOLDER 路由**: 一次实现, 多 SPI_FOLDER 复用
3. **_data_* 契约**: SPEC.md §8 正式化, v25 隐式约束 → v26 显式约束
4. **硬约束维护**: spi/dev/data.py SHA 校验 + spi/demo/ 时间戳校验
5. **缺失友好错误**: fdep 缺 cli/api → 404 + 中文提示, 不是 ImportError stack trace

---

**复盘作者**: hermes · 2026-11-17
**复盘状态**: published
**关联**: v25 FastAPI retrospective / v28 main_common retrospective / v27 dept-role-2d retrospective