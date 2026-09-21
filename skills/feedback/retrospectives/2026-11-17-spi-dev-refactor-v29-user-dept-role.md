# 2026-11-17 spi/dev 重构 v29 · 用户部门角色反向 (USER_DEPT_ROLE)

> **重构日期**: 2026-11-17 (W47 Day 5)
> **状态**: ✅ **published** · 5/5 PASS · **互逆检查 0 mismatch** · 22 DictProxy + 2 helpers + 9 SPI 函数 + dispatcher CLI/API + main_common 双端不变
> **关联**: `spi/dev/data.py` 新增 `SPI_USER_DEPT_ROLE` (uid → [(dept_id, role_code)])
> **互逆**: 与 v27 `SPI_USERS_BY_DEPT_ROLE` 互为反向
> **下一里程碑**: Phase 10 (Q1 2027)

---

## 1. 重构动机

**v27 二维聚合的反向缺失**:
- `SPI_USERS_BY_DEPT_ROLE` (dept_id, role_code) → [uids] - 正向
- 但没有 `SPI_USER_DEPT_ROLE` uid → [(dept_id, role_code)] - 反向

**实战场景**:
- "周磊在哪些部门担任哪些角色?" (用户视角, 跨部门任职)
- v16 SPI_USERS_FULL 的 "roles" 字段是简单列表, 缺 (dept, role) 元组信息
- v25 FastAPI `_data_show_user(uid)` 即将展示 (dept, role) 列表

---

## 2. 改动范围

### 2.1 新增 DictProxy

| 常量 | 类型 | 用途 |
| --- | --- | --- |
| `SPI_USER_DEPT_ROLE` | `dict[str, list[tuple[str, str]]]` | uid → [(dept_id, role_code)] |

### 2.2 核心算法

```python
SPI_USER_DEPT_ROLE = {}
for (dept_id, role_code), uids in SPI_USERS_BY_DEPT_ROLE.items():
    for uid in uids:
        SPI_USER_DEPT_ROLE.setdefault(uid, []).append((dept_id, role_code))
```

**原理**: 直接反向 v27, 4 行算法.

### 2.3 verify() summary 加 1 字段

`summary["user_dept_role_count"] = len(SPI_USER_DEPT_ROLE)` (应 = 13 用户).

---

## 3. 测试 (5/5 PASS)

| # | 场景 | 期望 | 实测 |
| --- | --- | --- | --- |
| 1 | 基本查询 (周磊 u_fe_eng) | [(D02, fe_engineer)] | ✅ |
| 2 | 检查特定组合 (u_rd_dir 在 D01 + D99) | [(D01, rd_director), (D99, rd_director)] | ✅ |
| 3 | 减员 (移除 1 用户) | 13 → 12 用户 | ✅ |
| 4 | 角色移除 (1 user 移除 1 角色) | 对应 tuple 不出现 | ✅ |
| 5 | **互逆检查**: 反向 v27 | **0 mismatch** | ✅ |

---

## 4. 互逆不变量 (关键质量门)

```python
# 互逆检查 0 mismatch
def check_inverse():
    for uid, pairs in SPI_USER_DEPT_ROLE.items():
        for dept_id, role_code in pairs:
            assert uid in SPI_USERS_BY_DEPT_ROLE[(dept_id, role_code)]
    for (dept_id, role_code), uids in SPI_USERS_BY_DEPT_ROLE.items():
        for uid in uids:
            assert (dept_id, role_code) in SPI_USER_DEPT_ROLE[uid]
    return True  # 0 mismatch
```

**价值**: 互逆不变量是数据完整性的硬证据, v29 之后所有派生常量都必须维护此性质.

---

## 5. 累计 DictProxy 总览 (22)

```
v8: SPI_DEPTS_LEV (后被 v9 替换)
v9: SPI_DEPTS_TREE
v10: verify()
v11: SPI_USERS_BY_DEPT, SPI_DEPT_LEADER_BY_USER
v12: SPI_DEPT_ANCESTORS, SPI_DEPT_DESCENDANTS
v13: SPI_DEPT_MAIN_LEADER_BY_USER, SPI_USER_DEPT_CHAIN
v14: SPI_USER_LEADER_CHAIN
v15: SPI_USERS_BY_LEVEL
v16: SPI_USERS_FULL
v17: SPI_DEPT_FULL_INFO
v18: verify() 扩展 (C4)
v19: SPI_DEPT_MEMBERS_FULL
v20: search_users()
v21: search_depts()
v22: CLI 入口
v23: SPI_USERS_WITH_ROLES
v24: CLI 扩展
v25: FastAPI 路由
v26: dispatcher
v27: SPI_USERS_BY_DEPT_ROLE
v28: main_common 双端
v29: SPI_USER_DEPT_ROLE (v27 互逆) ← 本次
```

---

## 6. 设计决策

### 6.1 tuple value vs 嵌套 dict

- **tuple**: `[(D02, fe_engineer), (D01, tech_lead)]` 紧凑, 顺序敏感 (dept 层次)
- **嵌套**: `{"D02": ["fe_engineer"]}` 多一跳

**决策**: tuple value, 与 v27 对称.

### 6.2 互逆不变量作为质量门

- **测试**: 5/5 PASS 包括互逆检查
- **价值**: 派生常量的一致性硬证据
- **可推广**: 所有反向派生 (v11/v13/v17/v19/v27) 都应建立互逆检查

---

## 7. 关键代码片段

```python
# spi/dev/data.py
SPI_USER_DEPT_ROLE: Dict[str, List[Tuple[str, str]]] = {}
for (_dept_id, _role), _uids in SPI_USERS_BY_DEPT_ROLE.items():
    for _uid in _uids:
        SPI_USER_DEPT_ROLE.setdefault(_uid, []).append((_dept_id, _role))
```

---

## 8. 经验教训

1. **互逆不变量**: v27 ↔ v29 互为反向, 0 mismatch 是质量门
2. **派生对称**: 二维聚合 (v27) + 反向 (v29) 是完整闭环
3. **22 DictProxy**: 数据层达到饱和, 后续更可能是 helpers (search/sort) 而非新 DictProxy
4. **为 Phase 10 铺路**: 数据层稳定, 后续重点是上游应用 (新流程模式 + 客户集成)

---

**复盘作者**: hermes · 2026-11-17
**复盘状态**: published
**关联**: v27 dept-role-2d retrospective / v23 USERS_WITH_ROLES retrospective / Phase 10 启动清单