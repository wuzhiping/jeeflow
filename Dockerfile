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
RUN uv pip install jeeflow[postgres]
# 服务端口
EXPOSE 8101

# 启动服务
CMD ["uv", "run", "main.py"]
