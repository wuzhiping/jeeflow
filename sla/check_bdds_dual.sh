#!/usr/bin/env bash
# sla/check_bdds_dual.sh — 双端 BDD 全量 One-by-One 验证 (SLA §7.2.1 FIX-T105 + 2026-09-20 规范)
# 用法: bash sla/check_bdds_dual.sh [MEM_HOST:PORT] [PG_HOST:PORT]
#   默认: MEM=localhost:8101, PG=localhost:8102
#
# 作业规范 (2026-09-20 修订):
#   1. 双端 (MEM + PG) 必跑, 缺一不可
#   2. One-by-One 验证: 逐个 BDD 跑, 跑完立即输出结果 (不批量汇总)
#   3. 每条结果含: BDD 编号 + 耗时 + PASS/FAIL + 累计计数 + 进度条
#   4. 颜色输出: PASS=绿, FAIL=红, 警告=黄
#   5. 末尾汇总: MEM/PG 双端 PASS 数 + 失败清单 + 总耗时

set -e

# 参数解析: --only IDX / --first N / --skip-pre-N / --help
ONLY_IDX=""     # 只跑指定 BDD (1-based index)
FIRST_N=""       # 只跑前 N 个
SKIP_PRE=""      # 跳过前 N 个
SKIP_POST=""     # 跳过末尾 N 个
RANGE_START=""   # 范围起始 (1-based, 含)
RANGE_END=""     # 范围结束 (1-based, 含)
MEM="http://localhost:8101"
PG="http://localhost:8102"
SHOW_HELP=0

print_help() {
    cat <<EOF
用法: bash sla/check_bdds_dual.sh [选项] [MEM_HOST:PORT] [PG_HOST:PORT]

选项:
  --only IDX        只跑第 IDX 个 BDD (1-based), 双端都跑
  --first N          只跑前 N 个 BDD
  --skip-pre N       跳过前 N 个 BDD
  --skip-post N      跳过末尾 N 个 BDD
  --range A-B        跑 IDX 在 A..B 范围的 BDD (含两端)
  --help             显示此帮助

示例:
  bash sla/check_bdds_dual.sh                          # 全量双端验证
  bash sla/check_bdds_dual.sh --first 3                # 只跑前 3 个
  bash sla/check_bdds_dual.sh --only 18                # 只跑第 18 个 (§7.3.3)
  bash sla/check_bdds_dual.sh --range 14-18               # 跑 §7 (5 个 BDD)
  bash sla/check_bdds_dual.sh http://host1:8101 http://host2:8102
EOF
}

ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --only)     ONLY_IDX="$2"; shift 2;;
        --first)    FIRST_N="$2"; shift 2;;
        --skip-pre) SKIP_PRE="$2"; shift 2;;
        --skip-post) SKIP_POST="$2"; shift 2;;
        --range) RANGE_START="${2%-*}"; RANGE_END="${2#*-}"; shift 2;;
        --help|-h)  SHOW_HELP=1; shift;;
        http://*)   if [ -z "${MEM_OVERRIDE:-}" ]; then MEM_OVERRIDE="$1"; else PG="$1"; fi; shift;;
        *)          echo "未知参数: $1"; exit 2;;
    esac
done

[ "$SHOW_HELP" = "1" ] && { print_help; exit 0; }
[ -n "${MEM_OVERRIDE:-}" ] && MEM="$MEM_OVERRIDE"

# 颜色定义 (无 TTY 时禁用)
if [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    C_RED='\033[31m'
    C_GREEN='\033[32m'
    C_YELLOW='\033[33m'
    C_CYAN='\033[36m'
    C_BOLD='\033[1m'
    C_DIM='\033[2m'
    C_RESET='\033[0m'
else
    C_RED=''; C_GREEN=''; C_YELLOW=''; C_CYAN=''; C_BOLD=''; C_DIM=''; C_RESET=''
fi

# 18 套 BDD (按编号顺序)
BDDS=(
  bdd/bdd-1001-1060-p0-regression.sh
  bdd/bdd-1065-1100-p1-regression.sh
  bdd/bdd-1101-1110-phase2.sh
  bdd/bdd-1211-1220-phase4.sh
  bdd/bdd-1301-1305-pre-interceptor.sh
  bdd/bdd-1306-1310-bizdata-pg.sh
  bdd/bdd-1311-1315-surrogate-todo.sh
  bdd/bdd-1316-1320-export-instance.sh
  bdd/bdd-1321-1325-audit-log-export.sh
  bdd/bdd-1326-1330-trace-persist.sh
  bdd/bdd-1331-1335-stress-1000.sh
  bdd/bdd-1336-1340-perf-baseline.sh
  bdd/bdd-1341-1345-metrics-remote-write.sh
  bdd/bdd-1516-1520-rollback.sh
  bdd/bdd-1521-1525-call-rollback.sh
  bdd/bdd-1526-1532-resume.sh
)
# 注: bdd-1501-1510-bdds-dual.sh 和 bdd-1511-1515-perf-dual.sh 自己跑双端 check_bdds_dual.sh, 会引发递归.
#     默认排除, 但可通过 --include-bdds-1501 单独跑.
TOTAL=${#BDDS[@]}
TOTAL_TASKS=$((TOTAL * 2))  # MEM + PG = 2 端
TOTAL_TASKS=$((TOTAL * 2))  # MEM + PG = 2 端

# 打印进度条
progress_bar() {
    local cur=$1
    local total=$2
    local width=40
    local filled=$(( cur * width / total ))
    local empty=$(( width - filled ))
    printf "["
    for ((i=0; i<filled; i++)); do printf "█"; done
    for ((i=0; i<empty; i++)); do printf "░"; done
    printf "] %d/%d" "$cur" "$total"
}

# 解析 BDD 输出 (兼容多种 PASS/FAIL 格式)
parse_bdd_output() {
    local OUT="$1"
    local P F

    # 格式 1: "TOTAL: PASS=N FAIL=M" 或 "PASS=N FAIL=M" 同一行
    local SUMMARY
    SUMMARY=$(echo "$OUT" | grep -E "TOTAL:.*PASS=[0-9]+.*FAIL=[0-9]+|PASS=[0-9]+.*FAIL=[0-9]+" | tail -1)
    if [ -n "$SUMMARY" ]; then
        P=$(echo "$SUMMARY" | grep -oE "PASS=[0-9]+" | head -1 | cut -d= -f2)
        F=$(echo "$SUMMARY" | grep -oE "FAIL=[0-9]+" | head -1 | cut -d= -f2)
        echo "${P:-0} ${F:-0}"
        return
    fi

    # 格式 2: "PASS: N\nFAIL: M" (老 BDD, 两行)
    local PASS_LINE FAIL_LINE
    PASS_LINE=$(echo "$OUT" | grep -E "^[[:space:]]*PASS:[[:space:]]*[0-9]+" | tail -1)
    FAIL_LINE=$(echo "$OUT" | grep -E "^[[:space:]]*FAIL:[[:space:]]*[0-9]+" | tail -1)
    if [ -n "$PASS_LINE" ] || [ -n "$FAIL_LINE" ]; then
        P=$(echo "$PASS_LINE" | grep -oE "[0-9]+" | tail -1)
        F=$(echo "$FAIL_LINE" | grep -oE "[0-9]+" | tail -1)
        echo "${P:-0} ${F:-0}"
        return
    fi

    # 格式 3: 分别匹配 PASS=/FAIL= (取最后一个)
    P=$(echo "$OUT" | grep -oE "PASS=[0-9]+" | tail -1 | cut -d= -f2)
    F=$(echo "$OUT" | grep -oE "FAIL=[0-9]+" | tail -1 | cut -d= -f2)
    echo "${P:-0} ${F:-0}"
}

echo ""
echo -e "${C_BOLD}═══════════════════════════════════════════════════════════════${C_RESET}"
echo -e "${C_BOLD}  jeeFlow SLA 双端 BDD 全量验证 (One-by-One)${C_RESET}"
echo -e "${C_BOLD}═══════════════════════════════════════════════════════════════${C_RESET}"
echo -e "  ${C_CYAN}MEM${C_RESET}: $MEM"
echo -e "  ${C_CYAN}PG${C_RESET}:  $PG"
echo -e "  ${C_CYAN}BDD 套数${C_RESET}: $TOTAL (可 --first N / --only IDX 过滤, 双端 = $TOTAL_TASKS 验证)"
echo -e "  ${C_CYAN}作业规范${C_RESET}: One-by-One, 即时输出, 累计计数"
echo -e "${C_BOLD}═══════════════════════════════════════════════════════════════${C_RESET}"
echo ""

# 单端 One-by-One 跑 BDD, 即时输出
run_one_side() {
    local HOST=$1
    local LABEL=$2
    local PASS=0
    local FAIL=0
    local FAILED_LIST=""
    local TASK_NUM=0
    local START_TIME=$(date +%s)

    # 应用过滤器
    FILTERED_BDDS=()
    IDX=0
    for bdd in "${BDDS[@]}"; do
        IDX=$((IDX + 1))
        if [ -n "$ONLY_IDX" ] && [ "$IDX" != "$ONLY_IDX" ]; then continue; fi
        if [ -n "$FIRST_N" ] && [ "$IDX" -gt "$FIRST_N" ]; then continue; fi
        if [ -n "$SKIP_PRE" ] && [ "$IDX" -le "$SKIP_PRE" ]; then continue; fi
        if [ -n "$SKIP_POST" ] && [ "$IDX" -gt "$(${#BDDS[@]} - SKIP_POST)" ]; then continue; fi
        if [ -n "$RANGE_START" ] && [ "$IDX" -lt "$RANGE_START" ]; then continue; fi
        if [ -n "$RANGE_END" ] && [ "$IDX" -gt "$RANGE_END" ]; then continue; fi
        FILTERED_BDDS+=("$bdd")
    done
    ACTUAL_TOTAL=${#FILTERED_BDDS[@]}

    echo -e "${C_BOLD}━━━ $LABEL 端 (HOST=$HOST) ━━━${C_RESET}" >&2
    echo -e "  ${C_DIM}将跑 $ACTUAL_TOTAL 个 BDD${C_RESET}" >&2
    echo "" >&2

    for bdd in "${FILTERED_BDDS[@]}"; do
        TASK_NUM=$((TASK_NUM + 1))
        name=$(basename "$bdd" .sh)
        progress=$(progress_bar $TASK_NUM $ACTUAL_TOTAL)

        # 临时改 HOST
        cp "$bdd" "/tmp/${name}_orig.sh"
        sed -i "s|HOST=http://localhost:8101|HOST=$HOST|g" "$bdd"

        # 跑 + 计时
        local BDD_START=$(date +%s%3N)
        OUT=$(bash "$bdd" 2>&1)
        local BDD_END=$(date +%s%3N)
        local ELAPSED=$((BDD_END - BDD_START))

        # 解析
        read -r P F <<< "$(parse_bdd_output "$OUT")"

        # 还原
        cp "/tmp/${name}_orig.sh" "$bdd"
        rm -f "/tmp/${name}_orig.sh"

        # 即时输出
        if [ "$F" = "0" ] && [ "$P" -gt 0 ]; then
            PASS=$((PASS + 1))
            echo -e "  ${C_GREEN}✅ PASS${C_RESET}  $name  ${C_DIM}(P=$P F=$F, ${ELAPSED}ms)${C_RESET}  ${progress}" >&2
        elif [ "$F" != "0" ] && [ "$F" -gt 0 ]; then
            FAIL=$((FAIL + 1))
            FAILED_LIST="$FAILED_LIST\n    ❌ $name (P=$P F=$F)"
            echo -e "  ${C_RED}❌ FAIL${C_RESET}  $name  ${C_DIM}(P=$P F=$F, ${ELAPSED}ms)${C_RESET}  ${progress}" >&2
        else
            # 无 PASS 也无 FAIL (脚本异常)
            FAIL=$((FAIL + 1))
            FAILED_LIST="$FAILED_LIST\n    ⚠️  $name (无 PASS/FAIL 输出)"
            echo -e "  ${C_YELLOW}⚠️  SKIP${C_RESET}  $name  ${C_DIM}(无 PASS/FAIL, ${ELAPSED}ms)${C_RESET}  ${progress}" >&2
        fi

        # 累计进度
        local TOTAL_PASS=$((PASS + FAIL))
        echo -e "         ${C_DIM}累计: PASS=$PASS / FAIL=$FAIL / TOTAL=$TOTAL_PASS${C_RESET}" >&2
        echo "" >&2
    done

    local END_TIME=$(date +%s)
    local TOTAL_ELAPSED=$((END_TIME - START_TIME))
    echo -e "${C_BOLD}  $LABEL 端完成: PASS=$PASS / FAIL=$FAIL / TOTAL=$ACTUAL_TOTAL / 耗时=${TOTAL_ELAPSED}s${C_RESET}" >&2
    if [ -n "$FAILED_LIST" ]; then
        echo -e "  ${C_RED}失败清单:${C_RESET}$FAILED_LIST" >&2
    fi
    echo "" >&2

    # 恢复 stdout 输出 PASS FAIL 给上层 $()
        echo "$PASS $FAIL"
}

# 跑 MEM 端
RES_MEM=$(run_one_side "$MEM" "MEM")
MEM_PASS=$(echo "$RES_MEM" | awk '{print $1}')
MEM_FAIL=$(echo "$RES_MEM" | awk '{print $2}')

# 跑 PG 端
RES_PG=$(run_one_side "$PG" "PG")
PG_PASS=$(echo "$RES_PG" | awk '{print $1}')
PG_FAIL=$(echo "$RES_PG" | awk '{print $2}')

# 总汇总
TOTAL_PASS=$((MEM_PASS + PG_PASS))
TOTAL_FAIL=$((MEM_FAIL + PG_FAIL))
TOTAL_CHECK=$((TOTAL_PASS + TOTAL_FAIL))

echo -e "${C_BOLD}═══════════════════════════════════════════════════════════════${C_RESET}"
echo -e "${C_BOLD}  📊 SLA 双端 BDD 全量验证最终汇总${C_RESET}"
echo -e "${C_BOLD}═══════════════════════════════════════════════════════════════${C_RESET}"
echo -e "  ${C_CYAN}MEM 端${C_RESET}: ${C_GREEN}PASS=$MEM_PASS${C_RESET} / ${C_RED}FAIL=$MEM_FAIL${C_RESET} / TOTAL=$TOTAL"
echo -e "  ${C_CYAN}PG  端${C_RESET}: ${C_GREEN}PASS=$PG_PASS${C_RESET} / ${C_RED}FAIL=$PG_FAIL${C_RESET} / TOTAL=$TOTAL"
echo -e "  ${C_BOLD}总验证${C_RESET}: ${C_GREEN}PASS=$TOTAL_PASS${C_RESET} / ${C_RED}FAIL=$TOTAL_FAIL${C_RESET} / TOTAL=$TOTAL_CHECK"
echo -e "${C_BOLD}═══════════════════════════════════════════════════════════════${C_RESET}"

# 双端一致性判定
if [ "$MEM_FAIL" = "0" ] && [ "$PG_FAIL" = "0" ]; then
    echo -e "  ${C_GREEN}${C_BOLD}✅ 双端 BDD 全量 PASS, 双端一致性达成${C_RESET}"
    echo ""
    exit 0
else
    echo -e "  ${C_RED}${C_BOLD}❌ 双端 BDD 存在失败项, 需修复后重跑${C_RESET}"
    echo ""
    exit 1
fi
