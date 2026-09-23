# 2026-11-17 spi 重构 v28 · spi 路由移到 main_common.py (双端共用)

> **重构日期**: 2026-11-17 (W47 Day 5)
> **状态**: ✅ **published** · 4/4 PASS · 21 DictProxy + 2 helpers + 9 SPI 函数 + verify() 不动
> **关联**: `main_common.py` 新增 `register_spi_routes(app)` 函数 · main.py + main_pg.py 同步集成
> **下一里程碑**: v29 USER_DEPT_ROLE (互逆)

---

## 1. 重构动机

**v26 dispatcher 后的痛点**:
- main.py + main_pg.py 都直接 `from spi.api import router; app.include_router(router)`
- 双端注册代码重复
- 与 `register_routes(app)` (业务 facade) 和 `install_metrics_endpoint(app)` (Prometheus) 模式不一致

**目标**: 提取 `register_spi_routes(app)` 到 main_common.py, 双端统一调用.

---

## 2. 改动范围

### 2.1 main_common.py 改动

```python
# main_common.py (新增函数, 1175 行文件中加约 10 行)
def register_spi_routes(app: FastAPI) -> None:
    """v28 新增: SPI 路由注册, 双端共用"""
    from spi.api import router as spi_router
    app.include_router(spi_router)
```

### 2.2 main.py 改动

```python
# main.py
- from spi.api import router as spi_router
- app.include_router(spi_router)
+ from main_common import register_spi_routes
+ register_spi_routes(app)
```

### 2.3 main_pg.py 改动 (PG 端 v28 首次集成)

```python
# main_pg.py (类似 main.py 改动)
+ from main_common import register_spi_routes
+ register_spi_routes(app)
```

### 2.4 验证 (4/4 PASS)

| # | 场景 | 期望 | 实测 |
| --- | --- | --- | --- |
| 1 | main_common.py 导入 | 无 ImportError | ✅ |
| 2 | main.py 注册 | 6 路由生效 | ✅ |
| 3 | main_pg.py 注册 (8102) | 6 路由生效 | ✅ |
| 4 | 双端 curl /api/spi/users | 同响应 (SPI_FOLDER 决定数据源) | ✅ |

---

## 3. 设计决策

### 3.1 register_spi_routes(app) 函数签名

- **参数**: `app: FastAPI` (与 `register_routes(app)` 对齐)
- **返回**: `None` (只注册, 无返回值)
- **位置**: `main_common.py` (与 `register_routes`, `install_metrics_endpoint` 同级)

### 3.2 为什么不是 main_common.py 直接 include_router?

- **模式一致**: `register_routes(app)` + `install_metrics_endpoint(app)` + `register_spi_routes(app)` 三个函数同形
- **扩展性**: 未来 `register_spi_routes` 可能加参数 (e.g. prefix, tags)
- **延迟导入**: `from spi.api import router` 在函数内部, 启动 main_common 不触发 spi 导入

---

## 4. main.py vs main_pg.py 对齐

| 函数 | main.py (8101) | main_pg.py (8102) |
| --- | --- | --- |
| `register_routes(app)` | ✅ (业务 facade) | ✅ |
| `install_metrics_endpoint(app)` | ✅ (Prometheus) | ✅ |
| `register_spi_routes(app)` | ✅ (v28 新增) | ✅ (v28 新增) |

**双端 100% 对齐**: 9 业务路由 + 6 SPI 路由 + Prometheus metrics 全部一致.

---

## 5. 关键代码片段

### 5.1 main_common.py

```python
def register_spi_routes(app: FastAPI) -> None:
    """v28 新增: SPI 路由注册, 双端共用. 跟随 SPI_FOLDER."""
    from spi.api import router as spi_router
    app.include_router(spi_router)
```

### 5.2 main.py + main_pg.py (同形)

```python
from main_common import (
    register_routes,
    install_metrics_endpoint,
    register_spi_routes,  # v28 新增
)

register_routes(app)
install_metrics_endpoint(app)
register_spi_routes(app)  # v28 新增
```

---

## 6. 经验教训

1. **双端共用模式**: register_* 函数收口到 main_common.py
2. **延迟导入**: `from spi.api` 在函数内, 不污染 main_common.py 启动
3. **PG 端首次集成**: v28 把 SPI 路由带到 8102 端口, PG backend 完整覆盖
4. **为未来铺路**: register_spi_routes 可加参数 (prefix/tags/auth)

---

**复盘作者**: hermes · 2026-11-17
**复盘状态**: published
**关联**: v26 dispatcher retrospective / v25 FastAPI retrospective / v29 USER_DEPT_ROLE retrospective