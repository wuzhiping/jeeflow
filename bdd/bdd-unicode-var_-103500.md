# BDD 任务 #119: 中文 + emoji 变量

## 目标
验证 `f_姓名`、`f_项目="🔥紧急项目"` 包含中文和 emoji 的变量能否保存

## 流程
apply → end

## 实测
启动传 `f_姓名="张三"` + `f_项目="🔥紧急项目"`

- start code=0
- processInstance/detail:
  - `f_姓名`: "张三" ✓
  - `f_项目`: "🔥紧急项目" ✓

## 结论
✅ **PASS**：中文 + Unicode emoji 变量完整保存

## 设计要点
- 流程变量支持任意 Unicode 字符
- Python 3 str 天然支持
- PG JSONB 字段也支持
- 实例 detail 返回 dict UTF-8 编码
