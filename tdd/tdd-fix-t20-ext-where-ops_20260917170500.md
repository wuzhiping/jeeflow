# TDD FIX-T20: vendor/jeeflow/repository/ext.py _build_ext_where 操作符扩展

- **时间**：2026-09-17 17:05:00
- **修复位置**：`vendor/jeeflow/repository/ext.py:_build_ext_where` (FIX-T20 段)
- **背景**：`_build_where`（主表）支持 EQ/NE/LIKE/LLIKE/RLIKE/GT/GE/LT/LE/IN/NIN，但 `_build_ext_where`（扩展表 design/surrogate）只支持 EQ/LIKE/LLIKE/RLIKE/IN
- **服务**：main.py（8101）+ main_pg.py（8102）

## 1. 上游修复

```python
op = c.operator.upper()
if op == "EQ":
    sql += f" AND {c.column} = ?"; args.append(val)
elif op == "NE":                                                # FIX-T20 新增
    sql += f" AND {c.column} <> ?"; args.append(val)
elif op == "LIKE":
    sql += f" AND {c.column} LIKE ?"; args.append(f"%{val}%")
elif op == "LLIKE":
    sql += f" AND {c.column} LIKE ?"; args.append(f"%{val}")
elif op == "RLIKE":
    sql += f" AND {c.column} LIKE ?"; args.append(f"{val}%")
elif op == "GT":                                                # FIX-T20 新增
    sql += f" AND {c.column} > ?"; args.append(val)
elif op == "GE":                                                # FIX-T20 新增
    sql += f" AND {c.column} >= ?"; args.append(val)
elif op == "LT":                                                # FIX-T20 新增
    sql += f" AND {c.column} < ?"; args.append(val)
elif op == "LE":                                                # FIX-T20 新增
    sql += f" AND {c.column} <= ?"; args.append(val)
elif op in ("IN", "NIN"):                                       # FIX-T20 NIN 新增
    if isinstance(val, (list, tuple)) and len(val) > 0:
        marks = ",".join(["?"] * len(val))
        sql += f" AND {c.column} IN ({marks})" if op == "IN" else f" AND {c.column} NOT IN ({marks})"
        args.extend(val)
```

## 2. 测试结果

```
PG m_NE_name="01-simple": total=3 (排除 01-simple)
PG m_LIKE_name="-": total=3 (匹配 '-')
PG m_NIN_name=["01-simple","t18-pg3"]: total=2 (排除两者)
memory m_NE_name="01-simple": total=2
```

## 3. 关键发现

1. **前后端一致**：design/surrogate 扩展表查询与主表查询支持相同操作符
2. **NIN 反向 IN**：NOT IN 语法
3. **业务场景**：白名单过滤（m_EQ）、范围查询（m_GT/m_LT）、排除列表（m_NIN）