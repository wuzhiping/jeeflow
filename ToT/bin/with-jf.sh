#!/bin/bash
# with-jf.sh —— 自动检测并 export REPO_ROOT（让 SOP 文档不用手动设环境变量）
#
# 用法（3 种）：
#   1. source 一次，会话内生效
#      $ source ToT/bin/with-jf.sh
#      $ python3 $REPO_ROOT/ToT/sop/ea-compliance.py
#
#   2. 单行 inline
#      $ source <(curl .../with-jf.sh)   # 如果远程拉取
#
#   3. 用 jf wrapper（推荐）
#      $ ./ToT/bin/jf python3 ToT/sop/ea-compliance.py
#
# 自动检测逻辑（按优先级）：
#   1. 已 export REPO_ROOT 且目录合法 → 用之
#   2. git rev-parse --show-toplevel（如果在 git repo 内）
#   3. 从本文件位置反推（ToT/bin/with-jf.sh → 项目根 = ../../..）
#   4. 当前 pwd（兜底）

# 函数：定位 REPO_ROOT
_jf_detect_repo_root() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
    # ToT/bin/with-jf.sh → 项目根是 ../../..
    local detected=""

    # 优先级 1：已 export
    if [ -n "$REPO_ROOT" ] && [ -d "$REPO_ROOT/ToT" ]; then
        detected="$REPO_ROOT"
    fi

    # 优先级 2：git
    if [ -z "$detected" ]; then
        detected=$(git rev-parse --show-toplevel 2>/dev/null)
        if [ -n "$detected" ] && [ ! -d "$detected/ToT" ]; then
            detected=""
        fi
    fi

    # 优先级 3：本文件位置反推（script_dir = ToT/bin → ../../ = 项目根）
    if [ -z "$detected" ]; then
        detected="$(dirname "$(dirname "$script_dir")")"
    fi

    # 优先级 4：当前目录兜底
    if [ -z "$detected" ] || [ ! -d "$detected/ToT" ]; then
        detected="$(pwd)"
    fi

    echo "$detected"
}

# 检测并 export
DETECTED=$(_jf_detect_repo_root)
if [ ! -d "$DETECTED/ToT" ]; then
    echo "ERROR: 无法定位项目根（DETECTED=$DETECTED，但 $DETECTED/ToT 不存在）" >&2
    echo "       请手动 export REPO_ROOT=/path/to/project" >&2
    return 1
fi

export REPO_ROOT="$DETECTED"
export PATH="$REPO_ROOT/ToT/sop:$REPO_ROOT/ToT/bin:$PATH"

# 友好提示（仅当 source 时打印）
if [ "${BASH_SOURCE[0]}" != "$0" ]; then
    echo "✓ REPO_ROOT=$REPO_ROOT (exported)"
fi