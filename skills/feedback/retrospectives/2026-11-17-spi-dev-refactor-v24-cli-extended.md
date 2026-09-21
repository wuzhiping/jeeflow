# 2026-11-17 spi/dev 重构 v24 · CLI 子命令扩展 (4 命令)

> **重构日期**: 2026-11-17 (W47 Day 5)
> **状态**: ✅ **published** · 20 DictProxy + 9 SPI 函数 + 2 helpers + CLI v22 不动
> **关联**: `spi/dev/cli.py` 从 80 → 217 行
> **下一里程碑**: v25 FastAPI 路由

---

## 1. 重构动机

**v22 CLI 只支持 verify/status/help**, 实战中开发者经常需要:
- "列所有用户" → 当前需 `python -c "from spi.dev.data import SPI_USERS; print(list(SPI_USERS.keys()))"`
- "查周磊完整档案" → 当前需多行 import
- "列所有部门" → 同上
- "查 D02 详情" → 同上

**目标**: CLI 必须支持 4 个查询命令, 覆盖 22 DictProxy (v23 后是 20) 的核心数据.

---

## 2. 改动范围

### 2.1 新增 4 命令

| 命令 | 输出 | 退出码 |
| --- | --- | --- |
| `list-users` | 表格 13 用户 (uid, name, post, level) | 0=OK, 2=ERROR |
| `show-user <uid>` | 用户完整档案 (复用 v16 SPI_USERS_FULL) | 0=OK, 1=uid 不存在, 2=缺参数 |
| `list-depts` | 表格 5 部门 (dept_id, name, size, leader) | 0=OK |
| `show-dept <dept_id>` | 部门详情 + 成员 (复用 v17/v19 DEPT_FULL_INFO + DEPT_MEMBERS_FULL) | 0=OK, 1=dept_id 不存在, 2=缺参数 |

### 2.2 文件变化

| 文件 | v22 | v24 | 增量 |
| --- | --- | --- | --- |
| `spi/dev/cli.py` | 80 行 | 217 行 | +137 行 |

---

## 3. 测试 (8/8 PASS)

| # | 命令 | 期望 | 实测 |
| --- | --- | --- | --- |
| 1 | `list-users` | 13 行表格 | ✅ |
| 2 | `show-user u_fe_eng` | 周磊 13 字段档案 | ✅ |
| 3 | `show-user u_nonexistent` | exit 1 + "User not found" | ✅ |
| 4 | `show-user` (缺参数) | exit 2 + argparse 报错 | ✅ |
| 5 | `list-depts` | 5 行表格 | ✅ |
| 6 | `show-dept D02` | D02 info + 3 members | ✅ |
| 7 | `show-dept D99_nonexistent` | exit 1 + "Dept not found" | ✅ |
| 8 | `show-dept` (缺参数) | exit 2 + argparse 报错 | ✅ |

---

## 4. 设计决策

### 4.1 表格输出 (vs JSON)

- **表格**: 人类可读, terminal 友好, `column -t` 进一步美化
- **JSON**: 机器友好, 适合管道处理 (`| jq`)

**决策**: 默认表格 (人类), 预留 `--json` flag (v25+ 可选).

### 4.2 错误处理三态 (0/1/2)

- **0** = OK
- **1** = 数据/查询错误 (uid 不存在)
- **2** = 参数/语法错误 (缺参数)

**CI 友好**: bash `if cmd; then ...` 直接判断.

---

## 5. 关键代码片段

```python
def cmd_show_user(args) -> int:
    uid = args.uid
    if uid not in SPI_USERS:
        print(f"❌ User not found: {uid}")
        return 1
    user = SPI_USERS_FULL[uid]  # 复用 v16 集成视图
    for k, v in user.items():
        print(f"  {k}: {v}")
    return 0
```

---

## 6. 经验教训

1. **CLI 复用 SPI_USERS_FULL**: 不重复实现, 单一数据源
2. **三态退出码**: OK / 数据错 / 参数错, CI 直接判断
3. **表格优先**: 人类可读优于 JSON 紧凑
4. **为 v25 API 铺路**: 同一 `_data_*` 函数即将被 API 复用

---

**复盘作者**: hermes · 2026-11-17
**复盘状态**: published
**关联**: v22 CLI retrospective / v25 FastAPI retrospective / v26 dispatcher retrospective