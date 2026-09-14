# UI (可以略过)
* cd ui
* pnpm install
* pnpm dev
* pnpm build:demo

# API (aio)
* uv run main.py

# http://localhost:8101/jeeflow/ui/

# [SPI][(https://jeeflow-doc.mldong.com/languages/python/spi-guide)
```
# sqlite:Memory for DEV
from jeeflow import MemoryRepository
repo = MemoryRepository()

# PostgreSQL（pip install jeeflow[postgres]）
import asyncpg
from jeeflow import JdbcRepository, PostgresAdapter
pool = await asyncpg.create_pool("postgresql://root:pwd@127.0.0.1/jeeflow")
repo = JdbcRepository(PostgresAdapter(pool))
```
