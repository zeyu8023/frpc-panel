FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 拷贝项目文件
COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 确保 entrypoint 可执行
RUN chmod +x entrypoint.sh

# 暴露端口
EXPOSE 5002

# 设置默认入口
ENTRYPOINT ["./entrypoint.sh"]
