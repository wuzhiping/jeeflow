# ToT/sop/doc-link-checker.py

> **状态**：✅ 已建（2026-09-24）
> **首次扫描**：134 条引用，✅ 134 / ⚠️ 0 / ❌ 0

## 用途

自动化审计 `ToT/docs/**/*.md` 中所有 `vendor/jeeflow/<file>.py:<line>` 行号引用，对照实际代码核对。

## 用法

```bash
# 默认：扫描所有 ToT/docs/*.md（除 diffs.md），tolerance=5
python3 ToT/sop/doc-link-checker.py

# JSON 输出（供 CI 集成）
python3 ToT/sop/doc-link-checker.py --json

# 自定义 tolerance
python3 ToT/sop/doc-link-checker.py --tolerance 3

# 只扫一个文件
python3 ToT/sop/doc-link-checker.py --md-file ToT/docs/spec/06-facade.md
```

## 校验逻辑

1. 提取 .md 中所有 `vendor/jeeflow/<file>.py:<line>` 模式
2. 对每条引用：
   - 验证文件存在
   - 验证行号有效（≤ 代码总行数）
   - 检查目标行内容是否匹配以下模式之一：
     - `def` / `async def` 函数定义
     - `class` 类定义
     - 大写常量赋值（如 `PERM_EDIT = 2`）
     - 模块级常量（如 `KEY_NEXT_NODE_OPERATOR = "..."`）
     - dataclass 字段定义（小写 + 类型注解 + `=`）
     - 任意缩进行（非纯注释，函数体内调用 / 赋值 / 字符串）
   - 若不匹配，查找附近 ±tolerance 行内的匹配（`NEAR_MATCH` 警告）
3. 输出 drift 报告（OK / NEAR_MATCH / NO_DEF / FILE_NOT_FOUND / LINE_OUT_OF_RANGE）
4. exit 0 = 无 DRIFT；exit 1 = 有 DRIFT；exit 2 = 脚本错误

## 设计要点

- **不依赖第三方包**（仅 Python 3.10+ 标准库 `re` / `json` / `pathlib`）
- **从 §3.1 / §3.2 / §3 差异审计中提炼**：95+ 项 doc 行号漂移，多数为「调用站点」或「函数体内语句」而非「定义行」，所以脚本接受所有缩进行为有效上下文
- **支持 CI 集成**：`--json` 输出标准结构，可接入 bdd-regression 流水线（~~GitHub Actions 已取消 2026-09-25~~）
- **支持单文件扫**：`--md-file` 参数，方便 PR 时只扫变动 doc

## 已知限制

1. **多行复合引用**（如 `engine.py:170-183`）：只校验起始行 `:170`，不校验 `:183` 范围
2. **跨文件引用**（如 `docs/flow.md §3.3`）：未提取跨文件路径（仅校验 `vendor/jeeflow/` 引用）
3. **doc 内嵌代码块**（```python ... ```）：未区分。脚本把代码块内的 `vendor/jeeflow/<file>.py:<line>` 也视为引用（设计如此，便于扫「伪代码示例」）

## 与 diffs.md 的关系

`diffs.md` 是**单次手工审计结果**（2026-09-24，95+ 项已修至 0）。
`doc-link-checker.py` 是**持续自动化工具**，未来 code 演进时一行 `python3 ToT/sop/doc-link-checker.py` 即可发现新 drift。

建议接入 **Phase 4 CI 流水线**：每次 PR 跑 `doc-link-checker.py`，失败即拦截。

## 后续

- [ ] 支持多行范围校验（`engine.py:170-183` 同时校验两端）
- [ ] 加入 `docs/flow.md` / `docs/api.md` 等仓库级文档
- [ ] 集成 `doc-archive-snapshot.py`（每发版打 snapshot，比对两版本 drift）
- ~~[ ] JSON 输出加入 GitHub Actions annotation 格式（`::error file=...,col=...`）~~ **取消 2026-09-25**（无需远程 CI）