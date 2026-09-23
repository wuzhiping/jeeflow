#!/usr/bin/env python3
"""flow-lint.py — 流程定义组织合规校验

依据：ToT/sop/flow-folder.md + ToT/README.md#10

检查项：
  1. JSON 路径必须在 ToT/flows/ 下
  2. JSON 顶层 name 字段 == 文件名去掉 .json 后 toLower()
  3. 同名文件夹 ToT/flows/<NAME>/ 必须存在
  4. 同名文件夹内必须含 4 个文件：README/ROLES/NODES/CHANGELOG
  5. NODES.md 必须包含 JSON 中所有 node.id 的工作说明
  6. ROLES.md 必须包含 JSON 中所有非空 properties.assignee 的角色清单

用法：
    python3 ToT/sop/flow-lint.py ToT/flows/fdep.json
    python3 ToT/sop/flow-lint.py ToT/flows/*.json

退出码：
    0 - 全部通过
    1 - 有 error（合规失败，必须修复）
    2 - 只有 warning
"""
import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def check_path(json_path: Path) -> tuple[list[str], list[str]]:
    """检查路径与 name 字段"""
    errors = []
    warnings = []

    # 1. 路径必须在 ToT/flows/ 下
    try:
        rel = json_path.relative_to(PROJECT_ROOT / "ToT" / "flows")
    except ValueError:
        errors.append(f"❌ 路径必须在 ToT/flows/ 下，实际: {json_path}")
        return errors, warnings

    # 2. 文件名本身必须小写（不允许 FDEP.json 这种全大写或混合大小写）
    if json_path.stem != json_path.stem.lower():
        errors.append(
            f"❌ 文件名必须全小写: '{json_path.name}' → 请用 '{json_path.stem.lower()}.json'"
        )

    # 3. name == 文件名去掉 .json 后 toLower() (此时 stem 已确保小写)
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"❌ JSON 解析失败: {e}")
        return errors, warnings

    expected_name = json_path.stem.lower()
    actual_name = (data.get("name") or "").strip()
    if actual_name != expected_name:
        errors.append(
            f"❌ name 字段不匹配: 期望 '{expected_name}' (来自文件名 {json_path.name})，实际 '{actual_name}'"
        )

    return errors, warnings


def check_folder(json_path: Path) -> tuple[list[str], list[str]]:
    """检查同名文件夹与 4 文件"""
    errors = []
    warnings = []

    folder = json_path.parent / json_path.stem  # 同名文件夹用文件名原大小写
    if not folder.exists():
        errors.append(f"❌ 同名文件夹缺失: {folder}")
        return errors, warnings

    required = ["README.md", "ROLES.md", "NODES.md", "CHANGELOG.md"]
    for fname in required:
        fpath = folder / fname
        if not fpath.exists():
            errors.append(f"❌ 必备文件缺失: {fpath}")
        elif fpath.stat().st_size == 0:
            warnings.append(f"⚠️  文件为空: {fpath}")

    return errors, warnings


def check_nodes_md(json_path: Path) -> tuple[list[str], list[str]]:
    """检查 NODES.md 覆盖所有 node.id"""
    errors = []
    warnings = []

    data = json.loads(json_path.read_text(encoding="utf-8"))
    nodes_md = json_path.parent / json_path.stem / "NODES.md"
    if not nodes_md.exists():
        return errors, warnings  # 已由 check_folder 报错

    md_content = nodes_md.read_text(encoding="utf-8")
    node_ids = [n["id"] for n in data.get("nodes", []) if n.get("id")]

    for nid in node_ids:
        # 节点 ID 在 NODES.md 中以 ## <id> 或 `<id>` 形式出现
        pattern_id = re.escape(nid)
        if not re.search(rf"##\s+{pattern_id}\b|`{pattern_id}`", md_content):
            errors.append(f"❌ NODES.md 缺节点工作说明: {nid}")

    return errors, warnings


def check_roles_md(json_path: Path) -> tuple[list[str], list[str]]:
    """检查 ROLES.md 覆盖所有非空 assignee"""
    errors = []
    warnings = []

    data = json.loads(json_path.read_text(encoding="utf-8"))
    roles_md = json_path.parent / json_path.stem / "ROLES.md"
    if not roles_md.exists():
        return errors, warnings

    md_content = roles_md.read_text(encoding="utf-8")
    assignees = set()
    for n in data.get("nodes", []):
        props = n.get("properties", {})
        a = props.get("assignee")
        if a:
            assignees.add(a)

    for assignee in sorted(assignees):
        pattern = re.escape(assignee)
        if not re.search(rf"\b{pattern}\b|`{pattern}`", md_content):
            errors.append(f"❌ ROLES.md 缺角色说明: {assignee}")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="流程定义组织合规校验")
    parser.add_argument("files", nargs="+", help="flow JSON 文件路径（可多个）")
    args = parser.parse_args()

    overall_ok = True
    for f in args.files:
        path = Path(f).resolve()
        print(f"=== {path.name} ===")
        if not path.exists():
            print(f"  ❌ 文件不存在")
            overall_ok = False
            continue

        all_errors = []
        all_warnings = []

        for check_fn in (check_path, check_folder, check_nodes_md, check_roles_md):
            try:
                errs, warns = check_fn(path)
            except Exception as e:
                errs = [f"❌ {check_fn.__name__} 异常: {e}"]
                warns = []
            all_errors.extend(errs)
            all_warnings.extend(warns)

        for e in all_errors:
            print(f"  {e}")
        for w in all_warnings:
            print(f"  {w}")

        if not all_errors:
            n_warns = len(all_warnings)
            print(f"  ✅ 通过 ({n_warns} warnings)" if n_warns else "  ✅ 通过")
        else:
            print(f"  ❌ 失败 ({len(all_errors)} errors)")
            overall_ok = False

    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
