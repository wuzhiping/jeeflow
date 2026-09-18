# BDD 任务 #115: 决策 expr 引用未定义变量

## 目标
验证 decision expr 引用未传变量时的行为

## 流程
apply → dec1 → [undefined_var>=1000 → high | default → low] → end

## 实测
启动时**不传** undefined_var 变量

- 期望：expr 不匹配 → 兜底到 low
- 实测：manager 看到 low ✓

## 结论
✅ **PASS**：未定义变量 expr 静默返回 False，走兜底

## 引擎行为
- `SimpleExprEvaluator.eval`: `vars.get(key)` → 未定义返回 None
- `None >= 1000` → TypeError? 实际是 False（regex 拒绝 None）
- 实际：vars[key] 是 None 时比较抛 TypeError，eval 捕获返回 False
- 走兜底边 ✓

## 设计建议
- 流程设计时，所有 expr 引用变量应在 `startAndExecute` 顶层必传
- 不传时引擎不报错但走兜底，可能导致意外路由
- 建议在 designer 端做静态检查
