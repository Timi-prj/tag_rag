# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
# 防止 Python 生成 .pyc 文件
ENV PYTHONDONTWRITEBYTECODE=1
# 确保日志即时输出
ENV PYTHONUNBUFFERED=1

# 复制依赖文件并安装
# 注意：我们先只复制 requirements.txt，利用 Docker 缓存层
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 这里不需要 COPY src . 
# 因为我们会通过 docker-compose 的 volume 挂载代码
