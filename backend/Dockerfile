# 后端 Dockerfile
# 基于 Python 3.11 slim 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 先复制依赖文件并安装（利用 Docker 缓存层）
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -i https://pypi.mirrors.ustc.edu.cn/simple/ -r requirements.txt

# 复制应用代码
COPY . .

# 暴露 8000 端口
EXPOSE 8000

# 生产环境启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
