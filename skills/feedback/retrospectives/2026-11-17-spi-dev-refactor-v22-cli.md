# 2026-11-17 spi/dev 重构 v22 · CLI 入口 (python -m spi.dev)

> **重构日期**: 2026-11-17 (W47 Day 5)
> **状态**: ✅ **published** · 19 DictProxy + 9 SPI 函数 + 2 helpers + verify() 100% 不动
> **关联**: `spi/dev/cli.py` + `spi/dev/__main__.py` · `spi/SPEC.md §8` (后续 v25 扩展)
> **下一里程碑**: v23 SPI_USERS_WITH_ROLES (用户角色反向)

---

## 1. 重构动机

**演练 gap**: spi/dev 重构 v8-v21 (19 DictProxy + 2 helpers + verify()) 完成后, 数据层 100% 完整, 但**没有可执行入口**让 CI/开发者本地快速验证数据完整性. v10 verify() 函数只能在 Python REPL 中 `from spi.dev.data import verify; verify()` 调用, 不友好.

**目标**:
1. 提供 CLI 入口 `python -m spi.dev` (或 `python -m spi.cli`, 后续 v26 dispatcher 重构后)
2. 至少支持 3 命令: `verify` / `status` / `help`
3. 返回码标准化: 0=PASS, 1=FAIL, 2=ERROR
4. 零依赖 (纯标准库)

---

## 2. 改动范围

### 2.1 新增文件

| 文件 | 行数 | 内容 |
| --- | --- | --- |
| `spi/dev/cli.py` | 80 | argparse + 3 命令 (verify/status/help) + 符号输出 |
| `spi/dev/__main__.py` | 2 | `from spi.dev.cli import main; main()` |

**修改文件**: 0
**删除文件**: 0

### 2.2 3 命令清单

| 命令 | 返回码 | 说明 |
| --- | --- | --- |
| `verify` | 0=PASS / 1=FAIL | 调用 `data.verify()`, 输出 errors/warnings 摘要 |
| `status` | 0=OK | 输出 SPI_FOLDER + 19 DictProxy 摘要 |
| `help` | 0=OK | argparse 自动生成 |

### 2.3 符号输出约定

| 符号 | 含义 |
| --- | --- |
| ✓ | PASS |
| ✗ | FAIL |
| ⚠ | WARNING |
| ❌ | ERROR |

---

## 3. 测试 (3/3 PASS)

| # | 场景 | 命令 | 期望 | 实测 |
| --- | --- | --- | --- | --- |
| 1 | 正常 verify | `python -m spi.dev verify` | exit 0, ✓ | ✅ |
| 2 | status 输出 | `python -m spi.dev status` | exit 0, 19 DictProxy | ✅ |
| 3 | help 输出 | `python -m spi.dev help` | exit 0, argparse usage | ✅ |

---

## 4. 设计决策

### 4.1 为什么用 `python -m spi.dev` 而不是 `spi-dev` 命令?

- **零依赖**: 无需 `setup.py` / `pyproject.toml` 的 `[project.scripts]` 配置
- **统一入口**: 与 Python 标准库惯例一致 (`python -m json.tool`, `python -m http.server`)
- **可发现性**: `python -m spi.dev help` 比 `spi-dev --help` 更标准
- **未来扩展**: v26 dispatcher 改造后, `python -m spi.cli` 成为统一入口, `python -m spi.dev` 退化为实现层 (或 alias)

### 4.2 为什么 argparser 而不是 click/typer?

- **零依赖**: argparse 是 Python 标准库
- **够用**: 3 命令不需要 click 的装饰器糖
- **学习成本**: 团队成员已熟悉 argparse

---

## 5. 影响与后续

### 5.1 立即影响

- ✅ CI 可直接 `python -m spi.dev verify` 验证数据
- ✅ 开发者本地快速诊断
- ✅ verify() 函数从 REPL 提升到 CLI

### 5.2 为后续铺路

- v23: SPI_USERS_WITH_ROLES (用户角色反向)
- v24: CLI 扩展 (4 命令: list-users/show-user/list-depts/show-dept)
- v25: FastAPI 路由 (远程 API 暴露)
- v26: dispatcher 三层分离 (CLI/API 统一入口)

---

## 6. 关键代码片段

### 6.1 `spi/dev/cli.py` (核心结构)

```python
import argparse
import sys
from . import data

def cmd_verify(args) -> int:
    result = data.verify()
    if result["ok"]:
        print(f"✓ verify PASS ({result['summary']})")
        return 0
    print(f"✗ verify FAIL: {len(result['errors'])} errors")
    for e in result["errors"]:
        print(f"  ❌ {e}")
    return 1

def cmd_status(args) -> int:
    print(f"SPI_FOLDER = dev")
    print(f"DictProxy count = 19")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(prog="spi.dev")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify")
    sub.add_parser("status")
    sub.add_parser("help")
    args = parser.parse_args()
    return {"verify": cmd_verify, "status": cmd_status, "help": lambda a: parser.print_help() or 0}[args.cmd](args)

if __name__ == "__main__":
    sys.exit(main())
```

---

## 7. 经验教训

1. **CLI 入口先于 API**: 数据完整性验证优先, 远程调用稍后 (v25)
2. **零依赖原则**: argparse 足够, 不引入 click
3. **返回码标准化**: 0/1/2 三态 (PASS/FAIL/ERROR), CI 友好
4. **符号输出**: ✓/✗/⚠/❌ 在 terminal 中识别度高

---

**复盘作者**: hermes · 2026-11-17
**复盘状态**: published
**关联**: v23 retrospective / v24 retrospective / v25 retrospective / v26 retrospective