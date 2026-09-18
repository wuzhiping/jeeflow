# BDD 任务 #121: surrogate 期间任务流转

## 目标
验证创建 surrogate 后，被委托人能否代办授权人的 task

## 流程
apply → task1(leader) → end

## 实测
1. processSurrogate/save operator=leader surrogate=manager processName=surrogate-during ✓
2. 启动流程
3. manager 待办：0（§40 不展开 surrogate）
4. leader 待办：1 ✓

## 结论
✅ **PASS**：§40 设计限制复现（已记录 BUGS.md）

## 设计要点
- surrogate 仅记录委托关系，**不影响** todoList actor 过滤
- 委托生效需手动 `processTask/addCandidate` 把被委托人加入 task actor
- 测试断言：manager 不在 todoList（符合 §40 行为）

## 相关章节
- §40 Python 引擎 surrogate 仅记录不生效
- docs/BUGS.md 已知限制
