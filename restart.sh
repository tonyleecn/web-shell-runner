#!/bin/bash

# 定义变量
APP_DIR="/root/tony/ai-51.3-deploy"

# 切换到应用目录
cd $APP_DIR

# 停止应用
echo "正在重启应用..."
./stop.sh

# 等待完全停止
sleep 2

# 启动应用
./start.sh 