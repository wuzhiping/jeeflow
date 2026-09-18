FROM ghcr.io/astral-sh/uv:debian

WORKDIR /app

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# 复制本地项目源码
COPY . .

# 安装 Python 依赖
RUN uv sync --frozen
# RUN uv pip install jeeflow[postgres]

# RUN mv ./.venv/lib/python3.12/site-packages/jeeflow ./.venv/lib/python3.12/site-packages/jeeflow-X

ENV SPI_FOLDER=demo
ENV JEEFLOW_PG_DSN=postgresql://uid:pwd@127.0.0.1:5432/jeeflow
ENV PORT=8101
# 启动行为开关（main.py / main_pg.py 共用）
# FLOWS: 启动时是否加载 flows/*.json；默认 true
# SEEDS: 启动时是否跑业务种子；默认 false（避免冷启动时阻塞请求）
ENV FLOWS=true
ENV SEEDS=false

# 服务端口
EXPOSE 8101

# 启动服务
CMD ["uv", "run", "main.py"]
