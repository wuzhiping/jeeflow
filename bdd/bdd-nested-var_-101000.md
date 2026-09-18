# BDD 任务 #114: 嵌套对象变量

## 目标
验证 `f_meta={"level":3, "tags":["urgent","vip"]}` 嵌套对象能否保存

## 流程
apply → end

## 实测
启动传 `f_meta={"level": 3, "tags": ["urgent", "vip"]}`

- start code=0
- processInstance/detail `f_meta` = `{"level": 3, "tags": ["urgent", "vip"]}` ✓

## 结论
✅ **PASS**：嵌套对象 + 数组变量完整保存

## 设计要点
- startAndExecute 顶层 JSON 自动序列化
- 内存后端 dict 直接存引用
- PG 后端 JSONB 字段也能存（但需确认）
