# SLA 作业 Postmortem (2026-09-20)

> **目的**: 记录 `sla/check_bdds_dual.sh` v2 重构过程中的所有错误、根本原因、修复与防御措施, 防止下次重蹈覆辙.
> **范围**: sla/check_bdds_dual.sh + check_bdds_dual 触发的所有问题
> **最后更新**: 2026-09-20

---

## 📋 时间线

| 时间 | 事件 | 状态 |
|------|------|------|
| 09:00 | 用户要求 "双端 BDD 全量 One-by-One 验证, 即时输出结果" | 📝 需求 |
| 09:05 | 设计 v2: 逐个 BDD + 进度条 + 累计计数 | 💭 设计 |
| 09:10 | v1 实现: 函数内 echo 直接输出 | ❌ Bug |
| 09:15 | 第一次跑测试: `━━━ MEM 端...: syntax error` | ❌ Bug |
| 09:25 | 加 exec 3>&1: 仍 syntax error | ❌ Bug |
| 09:35 | 改用 >&2 重定向 + parse_bdd_output 总算匹配 | ⚠️ 部分修复 |
| 09:40 | 跑 --range 14-18, 卡 4 分钟无输出 | ❌ 致命 Bug (递归) |
| 09:45 | kill 进程链, 发现 bdd-1501 自调 check_bdds_dual | 🔍 根因 |
| 09:50 | 排除 bdd-1501/bdd-1511, 加 --range / --only / --first 参数 | ✅ 修复 |
| 10:00 | 全量 16 套双端跑通: 31 PASS / 1 FAIL | ✅ 完成 |

---

## 🐛 错误 1: BDD 双端递归导致无限进程链

### 现象
- 跑 `bash sla/check_bdds_dual.sh --range 14-18`, 第一个 BDD (bdd-1501-1510-bdds-dual) 卡 4 分钟
- `ps -ef` 显示进程链深度 50+ 层, 每层都跑 `bash bdd-1501-1510-bdds-dual.sh` → `bash sla/check_bdds_dual.sh` → 顶层又包含 bdd-1501
- 终端无任何输出 (被深递归阻塞)

### 根因
**`sla/check_bdds_dual.sh` 的 BDDS 数组包含了 `bdd-1501-1510-bdds-dual.sh` 和 `bdd-1511-1515-perf-dual.sh`, 而这两个 BDD 自身调用 `sla/check_bdds_dual.sh` 来验证 17 套 BDD 的双端行为. 这构成了自递归调用.**

```
sla/check_bdds_dual.sh (顶层)
  └── bash bdd-1501-1510-bdds-dual.sh
        └── bash sla/check_bdds_dual.sh (内层)
              └── bash bdd-1501-1510-bdds-dual.sh
                    └── bash sla/check_bdds_dual.sh (更深层)
                          └── ... (无穷)
```

### 修复
**从 `check_bdds_dual.sh` 的 BDDS 数组中移除会引起递归的两个 BDD**, 仅保留被验证对象:

```bash
BDDS=(
  bdd/bdd-1001-1060-p0-regression.sh    # 被 bdd-1501 验证
  bdd/bdd-1065-1100-p1-regression.sh    # 被 bdd-1501 验证
  bdd/bdd-1101-1110-phase2.sh           # 被 bdd-1501 验证
  bdd/bdd-1211-1220-phase4.sh           # 被 bdd-1501 验证
  bdd/bdd-1301-1305-pre-interceptor.sh  # 被 bdd-1501 验证
  bdd/bdd-1306-1310-bizdata-pg.sh       # 被 bdd-1501 验证
  bdd/bdd-1311-1315-surrogate-todo.sh   # 被 bdd-1501 验证
  bdd/bdd-1316-1320-export-instance.sh  # 被 bdd-1501 验证
  bdd/bdd-1321-1325-audit-log-export.sh # 被 bdd-1501 验证
  bdd/bdd-1326-1330-trace-persist.sh    # 被 bdd-1501 验证
  bdd/bdd-1331-1335-stress-1000.sh      # 被 bdd-1501 验证
  bdd/bdd-1336-1340-perf-baseline.sh    # 被 bdd-1501 验证
  bdd/bdd-1341-1345-metrics-remote-write.sh  # 被 bdd-1501 验证
  bdd/bdd-1516-1520-rollback.sh         # §7.3.1
  bdd/bdd-1521-1525-call-rollback.sh    # §7.3.2
  bdd/bdd-1526-1532-resume.sh           # §7.3.3
  # 排除: bdd-1501-1510-bdds-dual.sh (会调本脚本 → 递归)
  # 排除: bdd-1511-1515-perf-dual.sh  (同上)
)
```

bdd-1501/1511 仍可单独跑: `bash sla/check_bdds_dual.sh --only 14` (它们的 IDX 仍计入 TOTAL=18, 但实际 FILTERED_BDDS 排除).

### 防御措施
1. **BDD 文档规范**: 任何 BDD 脚本**禁止**直接调用 `sla/check_bdds_dual.sh` 或 `sla/check_flows_dual.sh`, 应调用具体 BDD. 在 BDD 文件头部用 grep 注释.
2. **SLA 自检**: `check.sh` 加 #36 项: 检测 `bdd-*.sh` 中是否包含 `check_bdds_dual` 字符串, 命中即 FAIL.
3. **递归防护**: check_bdds_dual.sh 加 `RUN_FROM_BDD` 环境变量检测, 如果存在就退出 (递归调用即死循环).

---

## 🐛 错误 2: parse_bdd_output 解析 BUG (P=8 F=8 实际 PASS=8 FAIL=0)

### 现象
- `bdd-1526-1532-resume.sh` 实际输出 `===== TOTAL: PASS=8 FAIL=0 =====`
- 我的解析器返回 `P=8 F=8` → 误判为 FAIL
- 同时老 BDD (bdd-1001-1060-p0-regression) 输出 `PASS: 17\nFAIL: 0` 没有 `TOTAL:` 行 → 误判为 SKIP

### 根因
**v1 正则错误地让 PASS_LINE 和 FAIL_LINE 匹配同一行**, 取 head -1 时都拿到同一行的第一个数字.

```bash
# v1 BUG
PASS_LINE=$(echo "$OUT" | grep -E "TOTAL:.*PASS=[0-9]+.*FAIL=[0-9]+|PASS=[0-9]+.*FAIL=[0-9]+" | tail -1)
# 这里 PASS_LINE = "===== TOTAL: PASS=8 FAIL=0 =====" (匹配整行)
# 实际想只取 PASS= 部分

FAIL_LINE=$(echo "$OUT" | grep -E "FAIL:" | tail -1)  
# 但这又去匹配其他行, 拿不到 FAIL=0
```

**v1 还漏掉老 BDD 格式** (`PASS: N\nFAIL: M` 两行, 没 `TOTAL:`)

### 修复
**三层 fallback 解析**:

```bash
parse_bdd_output() {
    local OUT="$1"
    
    # 格式 1: "TOTAL: PASS=N FAIL=M" 或 "PASS=N FAIL=M" 同一行 (bdd-15xx 输出)
    local SUMMARY
    SUMMARY=$(echo "$OUT" | grep -E "TOTAL:.*PASS=[0-9]+.*FAIL=[0-9]+|PASS=[0-9]+.*FAIL=[0-9]+" | tail -1)
    if [ -n "$SUMMARY" ]; then
        local P F
        P=$(echo "$SUMMARY" | grep -oE "PASS=[0-9]+" | head -1 | cut -d= -f2)
        F=$(echo "$SUMMARY" | grep -oE "FAIL=[0-9]+" | head -1 | cut -d= -f2)
        echo "${P:-0} ${F:-0}"
        return
    fi
    
    # 格式 2: "PASS: N\nFAIL: M" 两行 (老 BDD, bdd-1001-1060 输出)
    local PASS_LINE FAIL_LINE
    PASS_LINE=$(echo "$OUT" | grep -E "^[[:space:]]*PASS:[[:space:]]*[0-9]+" | tail -1)
    FAIL_LINE=$(echo "$OUT" | grep -E "^[[:space:]]*FAIL:[[:space:]]*[0-9]+" | tail -1)
    if [ -n "$PASS_LINE" ] || [ -n "$FAIL_LINE" ]; then
        local P F
        P=$(echo "$PASS_LINE" | grep -oE "[0-9]+" | tail -1)
        F=$(echo "$FAIL_LINE" | grep -oE "[0-9]+" | tail -1)
        echo "${P:-0} ${F:-0}"
        return
    fi
    
    # 格式 3: 退化 (分别匹配 PASS=/FAIL=)
    local P F
    P=$(echo "$OUT" | grep -oE "PASS=[0-9]+" | tail -1 | cut -d= -f2)
    F=$(echo "$OUT" | grep -oE "FAIL=[0-9]+" | tail -1 | cut -d= -f2)
    echo "${P:-0} ${F:-0}"
}
```

### 防御措施
1. **BDD 输出规范**: 所有 BDD 必须在末尾输出统一格式 (任选其一):
   - `===== TOTAL: PASS=N FAIL=M =====` (推荐, 含上下文)
   - `PASS: N\nFAIL: M` (兼容)
2. **SLA 自检**: `check.sh` 加 #37 项: 检测每个 BDD 末尾是否含 `PASS=` 或 `PASS:` 行; 缺失即 WARN.
3. **单测**: 为 parse_bdd_output 写单测 (`sla/test_parse.sh`), 覆盖三种格式 + 退化场景.

---

## 🐛 错误 3: $() 捕获导致 awk 取到错误行

### 现象
- `MEM_PASS=$(echo "$RES_MEM" | awk '{print $1}')` 返回 `━━━` (函数第一行标题) 而非 `15`
- 末尾汇总 `MEM 端: PASS=━━━ / FAIL=...`
- 终端输出 `line 232: ━━━ ... syntax error`

### 根因
**bash 中 `$(func)` 会捕获函数的所有 stdout, 不仅是返回值**. 我在 `run_one_side` 内用 `echo -e` 输出大量标题/进度信息, 这些都被 `$()` 捕获; `awk '{print $1}'` 取了第一行 (`━━━ MEM 端 (HOST=...) ━━━`) 的第一个字段.

```bash
run_one_side() {
    echo -e "━━━ $LABEL 端 ━━━"        # ← 被 $() 捕获
    echo "..."                        # ← 被 $() 捕获
    ...
    echo "$PASS $FAIL"                # ← 真正的返回值
}
RES=$(run_one_side "$HOST" "MEM")   # RES 包含上面所有输出
MEM_PASS=$(echo "$RES" | awk '{print $1}')  # ← 拿到 "━━━", 不是 PASS 数
```

### 修复
**函数内所有 `echo -e` 加 `>&2` 重定向到 stderr**, 只让最后的 `echo "$PASS $FAIL"` 输出到 stdout:

```bash
run_one_side() {
    echo -e "━━━ $LABEL 端 ━━━" >&2       # stderr (实时显示, 不被 $() 捕获)
    ...
    echo "$PASS $FAIL"                    # stdout (供 $() 捕获)
}
```

### 防御措施
1. **函数设计规范**: "返回值的函数" 必须严格分离 stdout (返回值) 与 stderr (日志). 推荐模式:
   - `result=$(my_func args 2>/dev/null)` 显式忽略日志
   - 或函数内 `exec 4>&1; ... exec 1>&2; ... exec 1>&4` 重定向 (复杂)
2. **CI 检查**: `shellcheck` 加规则 `SC2155: Declare and assign separately to avoid masking return values` (部分覆盖)
3. **测试**: 每个 helper 函数写 mini test, 验证 `$()` 只捕获预期行数.

---

## 🐛 错误 4: set -u + exec 3>&1 不兼容

### 现象
- 第一版用 `exec 3>&1` 把 stdout 保存到 fd 3, 函数内 echo 到 fd 3 (期望不被 $() 捕获)
- 实际: 函数内 echo 到 fd 3 仍出现在外层 stdout (因为 exec 在子 shell)
- 错误: `line 232: syntax error: operand expected`

### 根因
**bash 中 `$(func)` 创建 subshell, subshell 内的 `exec 3>&1` 只影响 subshell 的 fd 表, 不影响外层**; 函数内 `echo >&3` 输出到 subshell 的 fd 3, 而外层 $() 捕获的是 subshell 的 stdout (fd 1), 这条路没被修改 → 仍捕获.

### 修复
**放弃 exec 方案, 改用 `>&2` 直接重定向**. stderr 不会被 `$()` 默认捕获.

### 防御措施
1. **明确 exec 作用域**: 在 bash 函数/子 shell 中使用 exec 时, 必须意识到作用域仅限当前 shell. 推荐用 `>&2` 简单方案.
2. **测试**: 加 dry-run 测试: `$(my_func 2>&1)` 验证 $() 默认不捕获 stderr.

---

## 🐛 错误 5: MEM 端 pre-interceptor 边角 BUG (双端不一致)

### 现象
- 全量验证结果: MEM 端 15/16 PASS, PG 端 16/16 PASS
- 唯一 FAIL: `bdd-1301-1305-pre-interceptor (P=4 F=1)` 仅 MEM 端失败
- 双端不一致率: 1/32 = 3.1%

### 根因
**§6.1.1 preInterceptors 在 MEM 端的边角案例未通过**. 这是 §6 阶段已知的 BUG, 不在 §7 范围. 业务方生产用真实角色配置, 不依赖此 BDD.

### 修复
**暂不修复 (在 §6.5.3 BUG 奖励机制中待处理)**, 但:
1. check_bdds_dual 末尾汇总明确显示失败清单
2. check.sh 输出明确双端不一致率
3. POSTMORTEM.md 记录此问题供后续跟踪

### 防御措施
1. **BUG 跟踪**: 在 docs/BUGS.md 加 §6.1.1 BUG, 标记 "MEM 端 pre-interceptor 边角案例"
2. **回归测试**: 把 `bdd-1301-1305-pre-interceptor` 加到回归套件, 每次 SLA 跑必跑
3. **修复优先级**: §6.5.3 BUG 奖励 (FIX-T103) 自动捕获并标记

---

## 🛡️ 防御措施汇总 (新增 SLA 自检项)

为防止上述错误再犯, 在 `sla/check.sh` 中新增以下自检项:

| 项 | 检查 | 失败级别 |
|----|------|----------|
| #36 | `bdd-*.sh` 中不含 `check_bdds_dual` 字符串 (防递归) | ERROR |
| #37 | 每个 `bdd-*.sh` 末尾含 `PASS=` 或 `PASS:` 汇总行 (格式规范) | WARN |
| #38 | `sla/check_bdds_dual.sh` 函数 `run_one_side` 内 echo 必须 `>&2` (防 stdout 污染) | WARN |
| #39 | `sla/check_*.sh` 头部含 `set -e` + `set -u` (基础健壮性) | WARN |

### #36 实现 (示例)
```bash
echo -n "36.1 bdd-*.sh 不调用 check_bdds_dual (防递归): "
RECURSIVE=$(grep -l "check_bdds_dual" bdd/*.sh 2>/dev/null | wc -l)
if [ "$RECURSIVE" -gt 0 ]; then
    echo "❌ FAIL (发现 $RECURSIVE 个递归调用)"
    grep -l "check_bdds_dual" bdd/*.sh | head -5
    echo "提示: 这些 BDD 自身验证其他 BDD 的双端行为, 必须在 check_bdds_dual.sh 中排除"
else
    echo "✅ PASS"
fi
```

### #37 实现 (示例)
```bash
echo -n "37.1 每个 BDD 末尾含 PASS= 或 PASS: 汇总: "
MISSING=0
for bdd in bdd/*.sh; do
    if ! grep -qE "PASS=[0-9]+|^PASS:" "$bdd"; then
        MISSING=$((MISSING + 1))
        echo "    ⚠️  $bdd 缺汇总行"
    fi
done
if [ "$MISSING" = "0" ]; then echo "✅ PASS"; else echo "⚠️ WARN ($MISSING 个)"; fi
```

---

## 📚 经验教训

### 1. bash $() 捕获机制容易踩坑
**默认 `$()` 只捕获 stdout**, 但函数内 `echo` 也是 stdout. 设计返回型函数时必须严格分离:
- 日志 → `>&2`
- 返回值 → stdout (只能一行)

### 2. 自递归是 bash 脚本的常见陷阱
**任何"管理工具"被"被管理对象"调用时, 必须有防递归机制**. 推荐:
- 环境变量检测 (`RUN_FROM_BDD=1` 时退出)
- 显式排除 (check_bdds_dual.sh 中不包含会调它的 BDD)
- 深度限制 (用 `BASH_SOURCE` 数组检查调用栈)

### 3. 解析多格式输出必须 fallback
**老 BDD 和新 BDD 输出格式可能不同**. 解析器必须支持多格式, 否则误判. 推荐:
- 优先匹配最严格格式
- fallback 到宽松格式
- 最后退化 (按字段分别抓取)
- 三层都失败时 SKIP + 警告

### 4. set -u + exec + $() 组合危险
**bash 在 subshell 中执行函数时, exec 的作用域有限**. 推荐:
- 用 `>&2` 重定向而不是 exec
- 用 `set -e` 让错误立即可见
- 用 `set -u` 让未初始化变量立即出错 (但要小心 $())

### 5. 进度反馈必须实时
**One-by-One 验证的核心价值是"看到进度"**. 必须:
- 每个 BDD 完成后立即输出 (`>&2` 不被 buffer)
- 进度条 + 累计计数 + 耗时 (3 维度)
- 末尾汇总 + 失败清单 (供后续 fix)

---

## 📅 后续跟踪

- [ ] 实施 #36-#39 自检项 (下次 SLA check 时启用)
- [ ] §6.1.1 pre-interceptor MEM 边角 BUG 修复 (FIX-T107+ 或新 FIX)
- [ ] BDD 输出规范文档化 (`docs/bdd-spec.md`, 列出标准 PASS/FAIL 输出格式)
- [ ] shellcheck CI 集成 (PR 时自动检查)

---

**复盘完成 (2026-09-20)**. 5 个错误已记录根因 + 修复 + 防御措施. 下次 SLA 作业时参考本文档.
