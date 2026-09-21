#!/bin/bash
cd /opt/jupyter/src/RD/projects/jeeFlow
LIST=$(ls bdd/*.json | grep -v patch | sort)
TOTAL=0; PASS=0; FAIL=0
for f in $LIST; do
  TOTAL=$((TOTAL+1))
  NAME=$(basename $f .json)
  if [[ "$NAME" == "statics" ]]; then continue; fi
  RES=$(.venv/bin/python3 tdd/regression-202609171735/runner.py "$f" http://localhost:8102 2>&1)
  if echo "$RES" | grep -q '"ok": true'; then
    PASS=$((PASS+1))
    STATUS="✅"
  else
    FAIL=$((FAIL+1))
    STATUS="❌"
    echo "$RES" > "tdd/regression-202609171735/batch-results/$NAME.pg.fail.json"
  fi
  echo "$RES" > "tdd/regression-202609171735/batch-results/$NAME.pg.json"
  printf "%s %s\n" "$STATUS" "$NAME"
done
echo ""
echo "=== PG TOTAL: $TOTAL  PASS: $PASS  FAIL: $FAIL ==="
