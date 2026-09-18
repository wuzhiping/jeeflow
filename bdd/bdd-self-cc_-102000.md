# BDD 任务 #116: 自抄送

## 目标
验证 `f_ccActors=user1`（发起人抄送给自己）能否工作

## 流程
apply → end

## 实测
启动传 `f_ccActors="user1"`

- start code=0
- user1 ccList 1 条 ✓
- processInstance/ccList operator=user1 返回 1 条

## 结论
✅ **PASS**：自抄送正常工作

## 设计要点
- 抄送 actor 列表允许包含发起人自己
- 业务上"自抄送"用于留痕/审计
- 引擎无去重逻辑
