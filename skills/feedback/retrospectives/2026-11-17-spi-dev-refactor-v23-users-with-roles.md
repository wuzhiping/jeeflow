# 2026-11-17 spi/dev 重构 v23 · 用户角色反向 (USERS_WITH_ROLES)

> **重构日期**: 2026-11-17 (W47 Day 5)
> **状态**: ✅ **published** · 19 DictProxy + 9 SPI 函数 + 2 helpers + CLI v22 不动
> **关联**: `spi/dev/data.py` 新增 `SPI_USERS_WITH_ROLES`
> **下一里程碑**: v24 CLI 扩展 (4 命令)

---

## 1. 重构动机

**反向映射缺失**: v18 修复 ROLE_TO_USERS 一致性后, 数据层有:
- `ROLE_TO_USERS` (role_code → [uids]) - 正向
- 但没有 `USER_TO_ROLES` (uid → [role_codes]) - 反向

**实战场景**:
- "查周磊有哪些角色?" (用户视角)
- "查所有 P7 员工的角色分布?"
- v22 CLI `show-user` 即将要展示用户角色 (v24 准备)

---

## 2. 改动范围

### 2.1 新增 DictProxy

| 常量 | 类型 | 用途 |
| --- | --- | --- |
| `SPI_USERS_WITH_ROLES` | `dict[str, list[str]]` | uid → [role_codes] |

### 2.2 核心算法 (4 行)

```python
SPI_USERS_WITH_ROLES = {}
for role_code, uids in ROLE_TO_USERS.items():
    for uid in uids:
        SPI_USERS_WITH_ROLES.setdefault(uid, []).append(role_code)
```

**原理**: 双向遍历正向映射, 反向累积. DRY, 复用 ROLE_TO_USERS.

---

## 3. 测试 (4/4 PASS)

| # | 场景 | 期望 | 实测 |
| --- | --- | --- | --- |
| 1 | 基本查询 (周磊) | 1 角色 [fe_engineer] | ✅ |
| 2 | 多角色用户 (王强 u_rd_dir) | 2 角色 [rd_director, rd_engineer] | ✅ |
| 3 | 13 用户全覆盖 | 所有用户都有 ≥1 角色 | ✅ |
| 4 | 反向一致性 | \|SPI_USERS_WITH_ROLES\| = \|ROLE_TO_USERS\| 唯一 uid 总数 | ✅ |

---

## 4. 关键代码片段

```python
# spi/dev/data.py
SPI_USERS_WITH_ROLES: Dict[str, List[str]] = {}
for _role, _uids in ROLE_TO_USERS.items():
    for _uid in _uids:
        SPI_USERS_WITH_ROLES.setdefault(_uid, []).append(_role)
```

---

## 5. 经验教训

1. **反向映射补全**: 正向 → 反向是数据层常见需求, v23 补全
2. **4 行算法**: 简单累积模式, 避免建通用反向工厂函数 (YAGNI)
3. **一致性校验**: 13 用户全覆盖 (v18 修复后), 与 ROLE_TO_USERS 互逆
4. **为 v16 USERS_FULL 铺路**: SPI_USERS_WITH_ROLES 是 USERS_FULL 的输入之一

---

**复盘作者**: hermes · 2026-11-17
**复盘状态**: published
**关联**: v22 CLI retrospective / v24 retrospective / v16 USERS_FULL retrospective