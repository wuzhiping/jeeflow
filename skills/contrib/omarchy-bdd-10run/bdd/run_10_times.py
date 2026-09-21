#!/usr/bin/env python3
"""Run BDD test 10 times and collect results"""
import json
import subprocess
import sys
import time
from datetime import datetime

FLOW = "flows/01-simple.json"
ASSIGNEES = "bdd/test-simple-assignees.json"
VARS = "bdd/test-simple-vars.json"
SCENE = "bdd/test-simple-scene.json"
OPERATOR = "user1"
RUNS = 10

results = []

for i in range(RUNS):
    print(f"\n=== Run {i+1}/{RUNS} ===")
    try:
        # Run the test
        cmd = [
            sys.executable, "bdd/bdd_run.py",
            FLOW, OPERATOR, ASSIGNEES, VARS, SCENE
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="/home/shwoo/Work/jeeflow", timeout=60)
        
        # Parse output
        output_lines = result.stdout.strip().split('\n')
        run_data = {
            "run": i + 1,
            "timestamp": datetime.now().isoformat(),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
        # Extract key info from output
        for line in output_lines:
            if line.startswith('{"verify"'):
                run_data["verify"] = json.loads(line)
            elif line.startswith('{"reset"'):
                run_data["deploy"] = json.loads(line)
            elif line.startswith('{"start"'):
                run_data["start"] = json.loads(line)
            elif line.startswith('{"step"'):
                if "steps" not in run_data:
                    run_data["steps"] = []
                run_data["steps"].append(json.loads(line))
            elif line.startswith('{"final"'):
                run_data["final"] = json.loads(line)
        
        results.append(run_data)
        
        # Print summary
        if run_data.get("final", {}).get("final", {}).get("state") == 20:
            print(f"  ✅ PASS - Instance: {run_data.get('start', {}).get('start', {}).get('data', {}).get('processInstanceId')}")
        else:
            print(f"  ❌ FAIL")
            
        time.sleep(0.5)
        
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        results.append({
            "run": i + 1,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        })

# Save results
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"bdd/test-results-{timestamp}.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n=== Results saved to {output_file} ===")

# Summary
passed = sum(1 for r in results if r.get("final", {}).get("final", {}).get("state") == 20)
failed = sum(1 for r in results if r.get("final", {}).get("final", {}).get("state") != 20 and "final" in r)
errors = sum(1 for r in results if "error" in r)

print(f"Passed: {passed}, Failed: {failed}, Errors: {errors}")

# Generate report
report = f"""# BDD Test Report - Simple Approval Flow (10 Runs)

**Test Flow**: `flows/01-simple.json` (simple approval)
**Test Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Environment**: Memory mode (port 8101)
**Total Runs**: {RUNS}

## Summary
- ✅ Passed: {passed}
- ❌ Failed: {failed}
- ⚠️ Errors: {errors}

## Run Details
"""
for r in results:
    if "error" in r:
        report += f"\n### Run {r['run']} - ERROR\n"
        report += f"- Error: {r['error']}\n"
    else:
        state = r.get("final", {}).get("final", {}).get("state", "unknown")
        inst_id = r.get("start", {}).get("start", {}).get("data", {}).get("processInstanceId", "unknown")
        report += f"\n### Run {r['run']}\n"
        report += f"- Instance ID: {inst_id}\n"
        report += f"- Final State: {state} ({'PASS' if state == 20 else 'FAIL'})\n"
        if "verify" in r:
            verify = r["verify"].get("verify", {})
            if verify != "SKIPPED":
                report += f"- Verify Errors: {verify.get('errors', 'none')}\n"
                report += f"- Verify Warnings: {verify.get('warnings', 'none')}\n"

report_file = f"bdd/test-report-{timestamp}.md"
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(report)

print(f"Report saved to {report_file}")