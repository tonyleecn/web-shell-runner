#!/bin/bash

# 定义变量
APP_DIR="/root/tony/ai-51.3-deploy"
VENV_DIR="$APP_DIR/venv"
PORT=4446
LOG_FILE="$APP_DIR/app.log"

# 切换到应用目录
cd $APP_DIR

# 检查是否已经在运行
if lsof -t -i :$PORT > /dev/null; then
    echo "端口 $PORT 已被占用，应用可能已在运行"
    exit 1
fi

# 激活虚拟环境并启动应用
echo "正在启动应用..."
source $VENV_DIR/bin/activate
nohup python app.py > $LOG_FILE 2>&1 &

# 等待应用启动
sleep 3

# 检查是否成功启动
if lsof -t -i :$PORT > /dev/null; then
    PID=$(lsof -t -i :$PORT)
    echo "应用已成功启动，PID: $PID，端口: $PORT"
    echo "日志文件: $LOG_FILE"
else
    echo "应用启动失败，请检查日志文件: $LOG_FILE"
    exit 1
fi 