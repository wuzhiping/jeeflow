# jeeflow-original

**目的**：保留 jeeflow 上游原版（v1.8.28）用于与 `./vendor/jeeflow/` diff 对比。

**来源**：复制自 `.venv/lib/python3.12/site-packages/jeeflow/` 在 2026-09-19 uv 重构前的最后版本。

**用法**：
```bash
# 查看具体文件改动
diff vendor/jeeflow/engine.py vendor/jeeflow-original/engine.py

# 统计改动量
diff -r vendor/jeeflow vendor/jeeflow-original | wc -l
```

**关键改动文件**（FIX-T1 ~ FIX-T36 累计）：
- `engine.py` — 144 行 diff
- `facade.py` — 229 行 diff
- `repository/base.py` — 159 行 diff（FIX-T35 悲观锁）
- `memory.py` — 78 行 diff
- `spi.py` — 10 行 diff（lock_instance_for_update）
- `model.py` — FIX-T30 taskType + FIX-T32 taskActorIdList

**禁止修改**：本目录是只读参考。改动应放 `./vendor/jeeflow/`。
