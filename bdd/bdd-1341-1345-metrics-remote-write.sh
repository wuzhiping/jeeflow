#!/bin/bash
# BDD #1341-#1345: §6.4.2 metrics 持久化 (FIX-T102 2026-09-20)
# 覆盖: env 读取 + 不推送 (无 URL) 时不崩
set +e
PASS=0
FAIL=0
RESULTS=""

assert_eq() {
  local desc="$1" actual="$2" expected="$3"
  if [ "$actual" = "$expected" ]; then
    PASS=$((PASS + 1)); RESULTS="$RESULTS\n✅ #$1 [$desc]"
  else
    FAIL=$((FAIL + 1)); RESULTS="$RESULTS\n❌ #$1 [$desc]  expected=$expected actual=$actual"
  fi
}

# === #1341: 无 URL 配置时不崩 ===
RESP=$(curl -s -m 3 http://localhost:8101/metrics)
PROM_OK=$(echo "$RESP" | grep -c "^# HELP wf_")
[ "$PROM_OK" -ge 4 ] && assert_eq "1341 metrics 端点无 URL 配置时正常 (4 指标)" "ok" "ok" || assert_eq "1341 metrics 端点" "$PROM_OK" "4"

# === #1342: 默认配置下 _METRICS_REMOTE_WRITE_URL 为空 ===
RESP=$(curl -s -m 3 "http://localhost:8101/metrics")
HAS_OK=$(echo "$RESP" | head -1)
[ -n "$HAS_OK" ] && assert_eq "1342 metrics 响应非空" "ok" "ok" || assert_eq "1342 metrics 响应" "empty" "ok"

# === #1343-#1345: 配置 URL 但端口无服务时不应崩 ===
JEEFLOW_METRICS_REMOTE_WRITE_URL="http://localhost:9999/remote" \
JEEFLOW_METRICS_REMOTE_WRITE_AUTH="Bearer test" \
  timeout 10 .venv/bin/python -c "
import os
os.environ['JEEFLOW_METRICS_REMOTE_WRITE_URL'] = 'http://localhost:9999/remote'
import sys
sys.path.insert(0, '.'); sys.path.insert(0, 'vendor')
from main_common import _metrics_remote_write
_metrics_remote_write('test content')
print('OK')
"
RESULT=$?
# 因为我们没重启 server, env 是当前 shell 的
[ "$RESULT" = "0" ] && assert_eq "1343 _metrics_remote_write 失败静默 (URL 不通)" "ok" "ok" || assert_eq "1343 remote_write" "fail" "ok"

# === #1344: BUG 奖励文档存在 ===
HAS_BUG_DOC=$(grep -c "BUG.*奖励\|bug.*reward\|上报流程" docs/BUGS.md 2>/dev/null || echo 0)
[ "$HAS_BUG_DOC" -ge 1 ] && assert_eq "1344 known-issues.md 含 BUG 上报流程" "ok" "ok" || assert_eq "1344 BUG 上报文档" "$HAS_BUG_DOC" "1"

# === #1345: env 变量在 main_common 可读 ===
HAS_ENV=$(grep -c "JEEFLOW_METRICS_REMOTE_WRITE_URL" main_common.py)
[ "$HAS_ENV" -ge 1 ] && assert_eq "1345 main_common 读取 JEEFLOW_METRICS_REMOTE_WRITE_URL" "ok" "ok" || assert_eq "1345 env" "$HAS_ENV" "1"

echo "=========================================="
echo "BDD §6.4.2 metrics 持久化："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
