#!/usr/bin/env python3
"""spi-verify.py — SPI 组织数据完整性校验脚本

用途：每次修改 spi/<folder>/jsons/*.json 后必跑，CI / 手工均可。
依据：ToT/sop/spi-verify.md

用法：
    SPI_FOLDER=dev python3 ToT/sop/spi-verify.py
    SPI_FOLDER=fdep python3 ToT/sop/spi-verify.py

退出码：
    0 - 全部通过
    1 - 有 error（数据不可用）
    2 - 有 warning（数据可用，但需人工复核）

历史：本脚本由 ToT/README v0.9 流程固化而来，2026-09-22 首次落地。
"""
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SPI_FOLDER = os.environ.get("SPI_FOLDER", "dev")

# 让脚本可在任意 cwd 下运行
sys.path.insert(0, str(PROJECT_ROOT))


def _section(title: str):
    print()
    print(f"=== {title} ===")


def main() -> int:
    print(f"# spi-verify.py")
    print(f"# SPI_FOLDER = {SPI_FOLDER}")
    print(f"# 项目根     = {PROJECT_ROOT}")

    # === 1. 加载 SPI 并运行内置 verify ===
    try:
        spi_data = __import__(f"spi.{SPI_FOLDER}.data", fromlist=["verify"])
    except Exception as e:
        print(f"\n❌ 无法加载 spi.{SPI_FOLDER}.data: {e}")
        return 1

    if not hasattr(spi_data, "verify"):
        print(f"\n⚠️  spi.{SPI_FOLDER}.data 没有 verify() 方法（仅 spi/dev 实现）")
        print(f"   本 SOP 对该 SPI_FOLDER 仅做基础 JSON 校验 + FDEP 回归点（如适用）")
        result = {"ok": True, "errors": [], "warnings": [
            f"spi.{SPI_FOLDER}.data 缺少 verify()，跳过内置校验"
        ], "summary": {}}
    else:
        result = spi_data.verify()
    _section(f"[{SPI_FOLDER}] spi 内置 verify()")
    print(f"ok       : {result['ok']}")
    print(f"errors   : {len(result['errors'])}")
    print(f"warnings : {len(result['warnings'])}")

    for e in result["errors"]:
        print(f"  ❌ ERROR  {e}")
    for w in result["warnings"]:
        print(f"  ⚠️  WARN   {w}")

    # summary
    _section("summary")
    for k, v in result["summary"].items():
        print(f"  {k}: {v}")

    # === 2. FDEP 专属回归点（如果 SPI_FOLDER=dev 才执行）===
    fdep_invariants_ok = True
    if SPI_FOLDER == "dev":
        _section("FDEP 回归点 (spi/dev 专属)")
        try:
            users = spi_data.SPI_USERS
            tree = spi_data.SPI_DEPTS_TREE
            dept_chain = spi_data.SPI_USER_DEPT_CHAIN
            r2u = spi_data.SPI_ROLE_TO_USERS
            roles = spi_data.SPI_ROLES

            checks = []

            # 2.1 DFDEP 部门存在
            checks.append((
                "DFDEP 部门存在",
                "DFDEP" in tree,
                f"tree keys = {sorted(tree.keys())}"
            ))

            # 2.2 DFDEP 为顶层根（parent_id = null）
            if "DFDEP" in tree:
                # tree 只含 root，从 SPI_DEPT_FULL_INFO 取 parent_id
                dfdep_full = spi_data.SPI_DEPT_FULL_INFO.get("DFDEP", {})
                checks.append((
                    "DFDEP.parent_id = null",
                    dfdep_full.get("parent_id") is None,
                    f"parent_id = {dfdep_full.get('parent_id')}"
                ))
                checks.append((
                    "DFDEP.leader = u_fdp_pm",
                    dfdep_full.get("leader") == "u_fdp_pm",
                    f"leader = {dfdep_full.get('leader')}"
                ))
                checks.append((
                    "DFDEP.main_leader = u_fdp_pm",
                    dfdep_full.get("main_leader") == "u_fdp_pm",
                    f"main_leader = {dfdep_full.get('main_leader')}"
                ))

            # 2.3 u_fdp_pm 用户存在且 deptId = DFDEP
            if "u_fdp_pm" in users:
                checks.append((
                    "u_fdp_pm.deptId = DFDEP",
                    users["u_fdp_pm"].get("deptId") == "DFDEP",
                    f"deptId = {users['u_fdp_pm'].get('deptId')}"
                ))
                checks.append((
                    "u_fdp_pm.dept_chain = [DFDEP]",
                    dept_chain.get("u_fdp_pm") == ["DFDEP"],
                    f"chain = {dept_chain.get('u_fdp_pm')}"
                ))
            else:
                checks.append(("u_fdp_pm 用户存在", False, "user not found"))

            # 2.4 6 个 fdep_* 角色全部存在
            fdep_roles = ["fdep_intake", "fdep_rml", "fdep_arch", "fdep_dev", "fdep_review", "fdep_kb"]
            for r in fdep_roles:
                checks.append((
                    f"ROLE 存在: {r}",
                    r in roles,
                    f"ROLE_TO_USERS = {r2u.get(r)}"
                ))
                checks.append((
                    f"ROLE_TO_USERS[{r}] = [u_fdp_pm]",
                    r2u.get(r) == ["u_fdp_pm"],
                    f"actual = {r2u.get(r)}"
                ))

            # 输出
            for name, ok, detail in checks:
                mark = "✓" if ok else "❌"
                print(f"  {mark} {name:40s} | {detail}")
                if not ok:
                    fdep_invariants_ok = False

        except Exception as e:
            print(f"  ❌ FDEP 回归点执行异常: {e}")
            fdep_invariants_ok = False

    # === 3. 总评 ===
    _section("总评")
    overall_ok = result["ok"] and fdep_invariants_ok
    has_warnings = len(result["warnings"]) > 0

    if overall_ok and not has_warnings:
        print(f"✅ PASSED — SPI_FOLDER={SPI_FOLDER} 数据完整，可继续使用")
        return 0
    elif overall_ok and has_warnings:
        print(f"⚠️  PASSED WITH WARNINGS — SPI_FOLDER={SPI_FOLDER} 数据可用，但有 {len(result['warnings'])} 条警告需复核")
        return 2
    else:
        print(f"❌ FAILED — SPI_FOLDER={SPI_FOLDER} 数据有 error，**禁止使用**，需先修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
