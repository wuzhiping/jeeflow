#!/usr/bin/env bash
# sla/check_spi_dev.sh — spi/dev 数据完整性检查 (重构 v26+v29 后)
#
# 用法: bash sla/check_spi_dev.sh
# 依赖: SPI_FOLDER=dev
# 输出: stdout (人读) + sla/last_spi_dev_check.json (机读)
#
# 检查项:
#   1. 22 DictProxy 全部存在
#   2. 2 helpers (search_users, search_depts) 可调用
#   3. verify() 4 类检查 PASS
#   4. v27↔v29 互逆 0 mismatch

set -e

SPI_FOLDER="${SPI_FOLDER:-dev}"
PYTHON="${PYTHON:-python3}"
JSON_OUT="sla/last_spi_dev_check.json"

echo "=== spi/dev 检查 (SPI_FOLDER=$SPI_FOLDER) ==="

cd /opt/jupyter/src/RD/projects/jeeFlow

$PYTHON << PYEOF
import os, sys, json
os.environ["SPI_FOLDER"] = "${SPI_FOLDER}"
sys.path.insert(0, "/opt/jupyter/src/RD/projects/jeeFlow")

import spi.dev.data as d

results = {}

# 1. DictProxy 检查
dictproxy_names = [
    "SPI_USERS", "SPI_ROLES", "SPI_DICTS", "SPI_ROLE_TO_USERS",
    "SPI_DEPT_LEADERS", "SPI_DEPT_MAIN_LEADERS", "SPI_FIND_USER_BY_ROLE_DEPT",
    "SPI_DEPTS_TREE", "SPI_USERS_BY_DEPT", "SPI_DEPT_LEADER_BY_USER",
    "SPI_DEPT_ANCESTORS", "SPI_DEPT_DESCENDANTS", "SPI_DEPT_MAIN_LEADER_BY_USER",
    "SPI_USER_DEPT_CHAIN", "SPI_USER_LEADER_CHAIN", "SPI_USERS_BY_LEVEL",
    "SPI_USERS_BY_DEPT_ROLE", "SPI_USER_DEPT_ROLE",
    "SPI_USERS_FULL", "SPI_DEPT_FULL_INFO", "SPI_DEPT_MEMBERS_FULL",
    "SPI_USERS_WITH_ROLES",
]
present = sum(1 for n in dictproxy_names if hasattr(d, n))
results["dictproxy_count"] = present
results["dictproxy_expected"] = len(dictproxy_names)
results["dictproxy_pass"] = present == len(dictproxy_names)

# 2. helpers 检查
try:
    users = d.search_users("周")
    depts = d.search_depts("前端")
    results["search_users_result"] = users
    results["search_depts_result"] = depts
    results["helpers_pass"] = True
except Exception as e:
    results["helpers_pass"] = False
    results["helpers_error"] = str(e)

# 3. verify() 检查
v = d.verify()
results["verify_ok"] = v["ok"]
results["verify_errors"] = len(v["errors"])
results["verify_warnings"] = len(v["warnings"])
results["verify_pass"] = v["ok"] and len(v["errors"]) == 0

# 4. v27↔v29 互逆
mismatch = 0
for (dept, role), uids in d.SPI_USERS_BY_DEPT_ROLE.items():
    for uid in uids:
        if (dept, role) not in d.SPI_USER_DEPT_ROLE.get(uid, []):
            mismatch += 1
results["v27_v29_mismatch"] = mismatch
results["inverse_pass"] = mismatch == 0

# 输出
results["spi_folder"] = "${SPI_FOLDER}"
results["total_pass"] = sum([
    results["dictproxy_pass"],
    results["helpers_pass"],
    results["verify_pass"],
    results["inverse_pass"],
])

print(f"  DictProxy: {results['dictproxy_count']}/{results['dictproxy_expected']} ({'✅' if results['dictproxy_pass'] else '❌'})")
print(f"  Helpers: {'✅' if results['helpers_pass'] else '❌'}")
print(f"  verify(): ok={results['verify_ok']}, errors={results['verify_errors']}, warnings={results['verify_warnings']} ({'✅' if results['verify_pass'] else '❌'})")
print(f"  v27↔v29 互逆: mismatch={results['v27_v29_mismatch']} ({'✅' if results['inverse_pass'] else '❌'})")
print(f"  TOTAL: {results['total_pass']}/4 {'✅ ALL PASS' if results['total_pass'] == 4 else '❌ FAIL'}")

with open("${JSON_OUT}", "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
PYEOF

echo
echo "JSON: ${JSON_OUT}"