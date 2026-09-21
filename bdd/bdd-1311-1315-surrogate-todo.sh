#!/bin/bash
# BDD #1311-#1315: §6.1.3 委托关系自动影响 todoList actor (FIX-T96 2026-09-20)
# 覆盖: surrogate 自动展开 + todoList + doneList
# 注意: 使用 in-process 模式 (绕过 startAndExecute 自动完成), 因 main.py 内存版 / reset 后 ID 重置

set -e
PASS=0
FAIL=0
RESULTS=""

assert_eq() {
  local desc="$1" actual="$2" expected="$3"
  if [ "$actual" = "$expected" ]; then
    PASS=$((PASS + 1))
    RESULTS="$RESULTS\n✅ #$1 [$desc]"
  else
    FAIL=$((FAIL + 1))
    RESULTS="$RESULTS\n❌ #$1 [$desc]  expected=$expected actual=$actual"
  fi
}

# 跑 in-process 测试
RESULT=$(.venv/bin/python /tmp/test_surrogate_full.py 2>&1)
echo "$RESULT" > /tmp/test_surrogate_full.log

# 从输出提取计数
USER1_CNT=$(echo "$RESULT" | grep "USER1_CNT=" | cut -d= -f2)
USER2_CNT=$(echo "$RESULT" | grep "USER2_CNT=" | cut -d= -f2)
USER3_CNT=$(echo "$RESULT" | grep "USER3_CNT=" | cut -d= -f2)
USER1_DONE=$(echo "$RESULT" | grep "USER1_DONE=" | cut -d= -f2)
USER2_DONE=$(echo "$RESULT" | grep "USER2_DONE=" | cut -d= -f2)

echo "USER1=$USER1_CNT USER2=$USER2_CNT USER3=$USER3_CNT"
echo "USER1_DONE=$USER1_DONE USER2_DONE=$USER2_DONE"

# 断言
[ "$USER1_CNT" = "1" ] && assert_eq "1311 user1 todoList=1 (委托方)" "1" "1" || assert_eq "1311 user1 todoList=1" "0" "1"
[ "$USER2_CNT" = "1" ] && assert_eq "1312 user2 todoList=1 (代理人自动展开)" "1" "1" || assert_eq "1312 user2 todoList=1" "0" "1"
[ "$USER3_CNT" = "0" ] && assert_eq "1313 user3 todoList=0 (无委托)" "0" "0" || assert_eq "1313 user3 todoList=0" "1" "0"

echo "=========================================="
echo "BDD §6.1.3 surrogate 自动展开："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
