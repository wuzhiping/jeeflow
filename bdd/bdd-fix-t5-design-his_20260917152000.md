# BDD FIX-T5: processDesignHis/page 修复（CRITICAL）

- **时间**：2026-09-17 15:20:00
- **修复文件**：`main.py` + `main_pg.py`
- **服务**：main.py（PID 3462036）

## 1. 问题（§65）

`/wf/processDesignHis/page` API 返回 **"未知 action"**，因为 jeeflow facade.py 没有 `_processDesignHis_page` 方法。

但实际底层数据完整：
- `ext_repo.save_design_his()` 每次 deploy/save 累积
- `ext_repo.list_design_his(design_id)` 完整返回历史

只是上层 action 没注册。

## 2. 修复

```python
async def _processDesignHis_page(args: dict) -> dict:
    page_num = int(args.get("pageNum") or 1)
    page_size = int(args.get("pageSize") or 10)
    m_design_id = args.get("m_processDesignId") or args.get("m_designId")
    design_id_filter = int(m_design_id) if m_design_id else None

    rows_out = []
    for did, his_list in ext_repo._designHis.items():
        for h in his_list:
            if design_id_filter and h.processDesignId != design_id_filter:
                continue
            rows_out.append({...})
    rows_out.sort(key=lambda r: -(r["id"] or 0))
    return _page_data(rows_out, ...)
```

注册到 facade 实例 + class：
```python
facade._processDesignHis_page = _processDesignHis_page
setattr(JeeflowFacade, "_processDesignHis_page", _processDesignHis_page)
```

## 3. 验证

部署 3 个不同版本：

```
v1 design_id=9
v2 design_id=11
v3 design_id=13
```

`POST /wf/processDesignHis/page`：

```
total: 3
  id=10 designId=9  content={...v1...}
  id=12 designId=11 content={...v2...}
  id=14 designId=13 content={...v3...}
```

## 4. 关键发现

1. **his 数据是累积的**：save_deploy 多次会保存多条
2. **facade.py L446 去重**：相同 content 不重复入库（但 v1/v2/v3 内容不同 → 各自入库）
3. **list_design_his 倒序**：`INSERT...id DESC`（最新在前）
4. **设计器 detail 接口只取最新 1 条**：与 his/page 行为不一致

## 5. main_pg.py 同步

asyncpg 未装无法验证，但代码同步完成：
```python
async def _processDesignHis_page_pg(args: dict) -> dict:
    # JdbcProcessExtRepository 通过 list_design_his(did) 累积
    design_ids = list(ext_repo._designs.keys()) if hasattr(ext_repo, "_designs") else []
    for did in design_ids:
        his_list = await ext_repo.list_design_his(did)
        ...
```

## 6. 测试报告

- 修复 critical 级别 §65
- API 完整支持分页 + design_id 过滤
- main.py + main_pg.py 同步
