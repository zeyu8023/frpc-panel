#!/bin/bash

# 自动生成 .env（如果不存在）
if [ ! -f /app/.env ]; then
  echo "⚙️ 生成默认 .env 文件"
  cat <<EOF > /app/.env
USERNAME=admin
PASSWORD=admin123
FRPC_INI=/data/frpc.ini
FRPC_CONTAINER=frpc
SECRET_KEY=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)
EOF
fi

# 自动生成 frpc.ini（如果不存在）
if [ ! -f /data/frpc.ini ]; then
  echo "⚙️ 生成默认 frpc.ini 文件"
  mkdir -p /data
  cat <<EOF > /data/frpc.ini
[example]
type = tcp
local_ip = 127.0.0.1
local_port = 8080
remote_port = 18080
EOF
fi

# 启动 Flask 应用
exec python app.py
