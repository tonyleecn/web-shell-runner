#!/bin/bash

# 定义变量
PORT=4446

# 查找并终止进程
PID=$(lsof -t -i :$PORT)

if [ -z "$PID" ]; then
    echo "没有找到运行在端口 $PORT 的应用"
    exit 0
fi

echo "正在停止应用，PID: $PID，端口: $PORT"
kill -15 $PID

# 等待进程终止
sleep 2

# 检查进程是否已终止
if lsof -t -i :$PORT > /dev/null; then
    echo "应用未能正常终止，正在强制终止..."
    kill -9 $(lsof -t -i :$PORT)
    sleep 1
fi

# 最终检查
if lsof -t -i :$PORT > /dev/null; then
    echo "无法终止应用，请手动检查"
    exit 1
else
    echo "应用已成功停止"
fi 