FROM ghcr.io/astral-sh/uv:debian

WORKDIR /app

# 安装 git
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# 拉取项目
RUN git clone https://github.com/wuzhiping/jeeflow.git .

# 安装 Python 依赖
RUN uv sync --frozen

# 服务端口
EXPOSE 8101

# 启动
CMD ["uv", "run", "main.py"]
