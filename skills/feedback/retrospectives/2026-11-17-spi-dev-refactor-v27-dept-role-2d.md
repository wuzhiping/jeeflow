# 2026-11-17 spi/dev 重构 v27 · (dept, role) 二维聚合 (USERS_BY_DEPT_ROLE)

> **重构日期**: 2026-11-17 (W47 Day 5)
> **状态**: ✅ **published** · 20 DictProxy + 2 helpers + 9 SPI 函数 + verify() 不动
> **关联**: `spi/dev/data.py` 新增 `SPI_USERS_BY_DEPT_ROLE`
> **下一里程碑**: v28 main_common 双端集成

---

## 1. 重构动机

**复合查询缺失**: 实战中常需要 "某部门某角色的所有用户":
- "D02 部门的所有前端工程师?"
- "所有部门的所有 leader?"

当前需 2 步查询: `SPI_USERS_BY_DEPT["D02"]` ∩ `ROLE_TO_USERS["fe_engineer"]`, 不优雅.

**目标**: 一跳查询 `SPI_USERS_BY_DEPT_ROLE[(dept_id, role_code)] → [uids]`.

---

## 2. 改动范围

### 2.1 新增 DictProxy

| 常量 | 类型 | 用途 |
| --- | --- | --- |
| `SPI_USERS_BY_DEPT_ROLE` | `dict[tuple[str, str], list[str]]` | (dept_id, role_code) → [uids] |

### 2.2 核心算法

```python
SPI_USERS_BY_DEPT_ROLE = {}
for uid, user in SPI_USERS.items():
    dept_id = user["deptId"]  # 注意: 用 USERS[uid].deptId, 不是 SPI_USERS_BY_DEPT 反向
    for role_code in SPI_USERS_WITH_ROLES.get(uid, []):
        key = (dept_id, role_code)
        SPI_USERS_BY_DEPT_ROLE.setdefault(key, []).append(uid)
```

**Bug 修复**: 第一版用 `SPI_USERS_BY_DEPT` 反向查 dept_id, 但 `SPI_USERS_BY_DEPT[uid]` 返回的是 `[dept_id]` 列表, 需 `key[0]` 提取. 改用 `USERS[uid]["deptId"]` 直接拿.

### 2.3 verify() summary 加 1 字段

`summary["users_by_dept_role_count"] = len(SPI_USERS_BY_DEPT_ROLE)` (应 = 11).

---

## 3. 测试 (4/4 PASS)

| # | 场景 | 期望 | 实测 |
| --- | --- | --- | --- |
| 1 | D02 + fe_engineer | [u_fe_eng] | ✅ |
| 2 | 跨部门 senior | [u_rd_dir, u_ceo] | ✅ |
| 3 | 减员 (D02 移除 1 人) | 11 → 10 组合 | ✅ |
| 4 | 角色移除 (u_fe_eng 移除 fe_engineer) | 对应 key 变 [] | ✅ |

---

## 4. 跨 SPI_FOLDER 顺手补

`SPI_USERS_BY_DEPT_ROLE` 在 demo 也实现 (15 行), 但 demo 的 `ROLE_TO_USERS` 引用未在 SPI_ROLES 的角色 (99 errors 已知). demo 端 summary 字段保持一致.

---

## 5. 设计决策

### 5.1 tuple key vs 嵌套 dict

- **tuple**: `SPI_USERS_BY_DEPT_ROLE[("D02", "fe_engineer")]` 紧凑
- **嵌套**: `SPI_USERS_BY_DEPT_ROLE["D02"]["fe_engineer"]` 多一跳

**决策**: tuple key, 与 SQL `GROUP BY (dept_id, role_code)` 语义一致.

### 5.2 bug 修复: USERS[uid].deptId vs SPI_USERS_BY_DEPT 反向

- **错误**: `SPI_USERS_BY_DEPT` 是 `dept_id → [uids]`, 反向查 `SPI_USERS_BY_DEPT[uid]` 找不到 (uid 是 value 不是 key)
- **正确**: 直接 `USERS[uid]["deptId"]`, 单一数据源
- **教训**: 反向映射要双向, 不要假设单向

---

## 6. 关键代码片段

```python
# spi/dev/data.py
SPI_USERS_BY_DEPT_ROLE: Dict[Tuple[str, str], List[str]] = {}
for _uid, _user in SPI_USERS.items():
    _dept_id = _user["deptId"]
    for _role in SPI_USERS_WITH_ROLES.get(_uid, []):
        SPI_USERS_BY_DEPT_ROLE.setdefault((_dept_id, _role), []).append(_uid)
```

---

## 7. 经验教训

1. **二维聚合**: 复合查询常需二维 group by, SPI_USERS_BY_DEPT_ROLE 补全
2. **Bug 修复**: USERS[uid].deptId 单一数据源, 不反向查
3. **跨 SPI_FOLDER 一致**: demo 也补, verify() summary 字段对齐
4. **为 v29 互逆铺路**: SPI_USER_DEPT_ROLE 即将是 SPI_USERS_BY_DEPT_ROLE 的反向

---

**复盘作者**: hermes · 2026-11-17
**复盘状态**: published
**关联**: v23 USERS_WITH_ROLES retrospective / v29 USER_DEPT_ROLE retrospective