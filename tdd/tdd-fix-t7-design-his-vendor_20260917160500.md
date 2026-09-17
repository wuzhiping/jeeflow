# TDD FIX-T7: vendor/jeeflow/facade.py 添加 _processDesignHis_page

- **时间**：2026-09-17 16:05:00
- **修复位置**：`vendor/jeeflow/facade.py:_processDesignHis_page`（新方法）
- **去掉补丁**：main.py + main_pg.py `_processDesignHis_page` monkey patch
- **服务**：main.py（PID 3482188）

## 1. 问题（§65）

`/wf/processDesignHis/page` API 返回 "未知 action"，因为 jeeflow facade.py 没有 `_processDesignHis_*` 方法。

## 2. 上游修复（vendor/jeeflow/facade.py）

```python
async def _processDesignHis_page(self, args: dict) -> dict:
    """FIX-T7 (2026-09-17)：设计历史分页（v1.1.0 wf_process_design_his 表）"""
    ext = self._ext_repo()
    page_num = self._to_int(args.get("pageNum")) or 1
    page_size = self._to_int(args.get("pageSize")) or 10
    m_design_id = args.get("m_processDesignId") or args.get("m_designId")
    design_id_filter = self._to_int(m_design_id) if m_design_id else None

    rows_out = []
    if hasattr(ext, "_designHis"):  # MemoryExtRepository
        for did, his_list in ext._designHis.items():
            ...
    elif hasattr(ext, "list_design_his"):  # JdbcProcessExtRepository
        for did in (ext._designs.keys() if hasattr(ext, "_designs") else []):
            for h in await ext.list_design_his(did):
                ...
    rows_out.sort(key=lambda r: -(r["id"] or 0))
    return self._page_data(page_rows, total, page_num, page_size)
```

**双后端兼容**：自动检测 `ext._designHis`（memory）或 `ext.list_design_his()`（JDBC）。

## 3. 测试结果

部署 3 个不同版本：

```
v1 design_id=9
v2 design_id=11
v3 design_id=13
```

`POST /wf/processDesignHis/page`：

```
total: 3
  id=14 designId=13 v3
  id=12 designId=11 v2
  id=10 designId=9  v1
```

`m_processDesignId=9` 过滤：

```
total: 1   ✅
```

## 4. 关键发现

1. **vendor 修改独立生效**：去掉 main.py + main_pg.py monkey patch 后仍工作
2. **后端兼容**：memory + jdbc 后端都覆盖
3. **过滤参数**：`m_processDesignId` 或 `m_designId` 都支持
4. **累积读**：每次 deploy/save 都新增 his 条目

## 5. 测试报告

- vendor 上游修复：✅
- 不依赖 main.py + main_pg.py monkey patch
- 与 FIX-T6 模式一致（去掉临时补丁，移到 vendor 上游）
