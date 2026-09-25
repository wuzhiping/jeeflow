#!/bin/bash
# release.sh — 发布前强制 ToT/docs 一致性 + 自动打 snapshot + diff + 更新 __version__
#
# 步骤：
#   1. 跑 doc-link-checker.py（必须 0 drift）
#   2. 更新 vendor/jeeflow/__init__.py:__version__/__git_sha__/__build_time__
#   3. 跑 doc-archive-snapshot.py 打 snapshot（带版本标签）
#   4. 跑 doc-vs-code-drift.py --latest 显示 vs 上一版的变化
#   5. 显示 CHANGELOG.md 最新段
#
# 用法：
#   bash ToT/sop/release.sh v1.10.0      # 正式版本
#   bash ToT/sop/release.sh                # 默认 snapshot-YYYY-MM-DD
#   bash ToT/sop/release.sh v1.10.0 --skip-version   # 仅打 snapshot 不改 __version__

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

LABEL="${1:-snapshot-$(date +%Y-%m-%d)}"
SKIP_VERSION="false"
[ "${2:-}" = "--skip-version" ] && SKIP_VERSION="true"

CHECKER="$REPO_ROOT/ToT/sop/doc-link-checker.py"
SNAPSHOT="$REPO_ROOT/ToT/sop/doc-archive-snapshot.py"
DIFF="$REPO_ROOT/ToT/sop/doc-vs-code-drift.py"
CHANGELOG="$REPO_ROOT/ToT/docs/CHANGELOG.md"
INIT_PY="$REPO_ROOT/vendor/jeeflow/__init__.py"
HEALTH_CHECK="$REPO_ROOT/ToT/sop/health-check.py"

# 从 LABEL 提取版本号（去掉 v 前缀）
VERSION="$(echo "$LABEL" | sed -E 's/^v//' | sed -E 's/-.*$//' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+' || echo "")"

# 获取 git sha
GIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
BUILD_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "=========================================="
echo "  ToT/docs Release Check"
echo "  Label: $LABEL"
[ -n "$VERSION" ] && echo "  Version: $VERSION"
echo "  Git SHA: $GIT_SHA"
echo "=========================================="
echo

echo "▶ Step 0: health-check.py（综合门禁，01/04 A6）"
HEALTH_OUTPUT=$(python3 "$HEALTH_CHECK" 2>&1)
echo "$HEALTH_OUTPUT" | tail -15
HEALTH_SCORE=$(python3 "$HEALTH_CHECK" --json 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['overall_score'])" 2>/dev/null || echo 0)
if [ "${HEALTH_SCORE:-0}" -lt 100 ]; then
    echo ""
    echo "❌ 健康度不达标 ($HEALTH_SCORE/100)，发布被阻止"
    echo "请修复退化维度（参考 health-check.py 输出）"
    exit 1
fi
echo

echo "▶ Step 1: doc-link-checker.py"
if ! python3 "$CHECKER"; then
    echo ""
    echo "❌ 发现 drift，发布被阻止"
    echo "请修复 ToT/docs/*.md 让引用行号对齐 vendor/jeeflow/*.py 实际代码"
    exit 1
fi
echo

if [ "$SKIP_VERSION" != "true" ] && [ -n "$VERSION" ]; then
    echo "▶ Step 2: 更新 vendor/jeeflow/__init__.py:__version__"
    sed -i "s/^__version__ = .*/__version__ = \"$VERSION\"/" "$INIT_PY"
    sed -i "s/^__version_full__ = .*/__version_full__ = \"${VERSION}+${GIT_SHA}\"/" "$INIT_PY"
    sed -i "s/^__git_sha__ = .*/__git_sha__ = \"$GIT_SHA\"/" "$INIT_PY"
    sed -i "s/^__build_time__ = .*/__build_time__ = \"$BUILD_TIME\"/" "$INIT_PY"
    echo "  ✅ vendor/jeeflow/__init__.py 已更新"
    PYTHONPATH="$REPO_ROOT/vendor${PYTHONPATH:+:$PYTHONPATH}" python3 -c "
import jeeflow
print(f'    version      = {jeeflow.__version__}')
print(f'    version_full = {jeeflow.__version_full__}')
print(f'    git_sha      = {jeeflow.__git_sha__}')
print(f'    build_time   = {jeeflow.__build_time__}')
" || echo "  ⚠️  PYTHONPATH 校验失败（vendor/ 未在 sys.path），但 __init__.py 已写入"
    echo
fi

echo "▶ Step 3: doc-archive-snapshot.py"
python3 "$SNAPSHOT" --label "$LABEL"
echo

echo "▶ Step 4: doc-vs-code-drift.py --latest"
python3 "$DIFF" --latest
echo

echo "▶ Step 5: CHANGELOG.md 累积状态"
SNAPS=$(ls "$REPO_ROOT/ToT/sop/snapshots" | wc -l)
echo "  总快照数：$SNAPS"
echo

echo "=========================================="
echo "  ✅ Release check 通过"
echo "  建议："
echo "    1. git add ToT/sop/snapshots/ vendor/jeeflow/__init__.py"
echo "    2. git commit -m 'release: $LABEL'"
echo "    3. git tag -a $LABEL -m 'release $LABEL'"
echo ""
echo "  验证 healthz 返回新版本："
echo "    curl http://localhost:8101/healthz"
echo "=========================================="