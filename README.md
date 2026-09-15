<img width="1821" height="1073" alt="dc2e55f9-3d28-4fb8-ab35-19ca517870aa" src="https://github.com/user-attachments/assets/28b457fc-8761-4f7b-9341-8054542903b7" />

# UI (可以略过)
* cd ui
* pnpm install
* pnpm dev
* pnpm build:demo

# API (aio)
* uv run main.py

# http://localhost:8101/jeeflow/ui/

# [SPI](https://jeeflow-doc.mldong.com/languages/python/spi-guide)
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

```
docker build -t shawoo/jeeflow .
docker run --rm -p 8101:8101 shawoo/jeeflow
```
