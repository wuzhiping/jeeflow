#!/usr/bin/env python3
"""validate_flow.py — flow JSON schema + topology validator.

仅 stdlib（json/sys/os/argparse），不引入新依赖。
检查项：
  1. JSON 可解析（防 `]`/`}` 截断）
  2. 顶层含 name / nodes / edges
  3. 节点 id 唯一，type ∈ {snaker:start|end|task|decision|fork|join|custom}
  4. 边 sourceNodeId / targetNodeId 在 nodes 中存在
  5. 拓扑：start 入度 0；end 出度 0
  6. 决策出边可含 expr；非 decision 出边若带 expr 仅警告
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALID_NODE_TYPES = {
    "snaker:start",
    "snaker:end",
    "snaker:task",
    "snaker:decision",
    "snaker:fork",
    "snaker:join",
    "snaker:custom",
}


def _load(path: Path) -> tuple[dict | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"read error: {exc}"
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return None, f"JSON parse error at line {exc.lineno} col {exc.colno}: {exc.msg}"


def _validate(data: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for top in ("name", "nodes", "edges"):
        if top not in data:
            errors.append(f"missing top-level field: {top!r}")

    if errors:
        return errors, warnings

    nodes = data["nodes"]
    edges = data["edges"]

    if not isinstance(nodes, list) or not isinstance(edges, list):
        errors.append("'nodes' and 'edges' must be lists")
        return errors, warnings

    seen_ids: dict[str, int] = {}
    type_counts = {t: 0 for t in VALID_NODE_TYPES}
    in_degree: dict[str, int] = {n.get("id", ""): 0 for n in nodes}
    out_degree: dict[str, int] = {n.get("id", ""): 0 for n in nodes}

    for idx, n in enumerate(nodes):
        nid = n.get("id")
        ntype = n.get("type")
        if not nid:
            errors.append(f"nodes[{idx}]: missing 'id'")
            continue
        if nid in seen_ids:
            errors.append(f"nodes[{idx}]: duplicate id {nid!r} (also at index {seen_ids[nid]})")
        else:
            seen_ids[nid] = idx
        if ntype not in VALID_NODE_TYPES:
            errors.append(f"nodes[{idx}] {nid!r}: unknown type {ntype!r}")
        else:
            type_counts[ntype] += 1
        if not isinstance(n.get("properties", {}), dict):
            errors.append(f"nodes[{idx}] {nid!r}: 'properties' must be an object")

    for eidx, e in enumerate(edges):
        src = e.get("sourceNodeId")
        tgt = e.get("targetNodeId")
        if src not in seen_ids:
            errors.append(f"edges[{eidx}]: sourceNodeId {src!r} not in nodes")
        else:
            out_degree[src] += 1
        if tgt not in seen_ids:
            errors.append(f"edges[{eidx}]: targetNodeId {tgt!r} not in nodes")
        else:
            in_degree[tgt] += 1
        props = e.get("properties", {})
        if not isinstance(props, dict):
            errors.append(f"edges[{eidx}]: 'properties' must be an object")
            continue
        has_expr = "expr" in props and str(props.get("expr") or "").strip() != ""
        if has_expr and seen_ids.get(src) is not None:
            src_idx = seen_ids[src]
            src_type = nodes[src_idx].get("type")
            if src_type != "snaker:decision":
                warnings.append(
                    f"edges[{eidx}]: non-decision source {src!r} ({src_type}) "
                    f"carries expr — engine._follow_edges does not evaluate expr"
                )

    for nid, deg in in_degree.items():
        if deg == 0 and nodes[seen_ids[nid]].get("type") == "snaker:start":
            pass
    starts = [nid for nid, idx in seen_ids.items() if nodes[idx].get("type") == "snaker:start"]
    ends = [nid for nid, idx in seen_ids.items() if nodes[idx].get("type") == "snaker:end"]
    if not starts:
        errors.append("no snaker:start node found")
    if not ends:
        errors.append("no snaker:end node found")
    for nid in starts:
        if in_degree.get(nid, 0) != 0:
            errors.append(f"start node {nid!r} must have in-degree 0, got {in_degree[nid]}")
    for nid in ends:
        if out_degree.get(nid, 0) != 0:
            errors.append(f"end node {nid!r} must have out-degree 0, got {out_degree[nid]}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate flow JSON (schema + topology).")
    parser.add_argument("files", nargs="+", help="flow JSON file(s)")
    args = parser.parse_args()

    overall_ok = True
    for f in args.files:
        path = Path(f)
        print(f"=== {path} ===")
        if not path.exists():
            print(f"  ERROR: file not found")
            overall_ok = False
            continue
        data, err = _load(path)
        if err:
            print(f"  ERROR: {err}")
            overall_ok = False
            continue
        errors, warnings = _validate(data)
        if errors:
            overall_ok = False
            for e in errors:
                print(f"  ERROR: {e}")
        else:
            print(f"  OK ({len(data['nodes'])} nodes, {len(data['edges'])} edges)")
        for w in warnings:
            print(f"  WARN:  {w}")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
