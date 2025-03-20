#!/bin/bash
echo "开始执行测试脚本..."
echo "这是一行标准输出"
sleep 1
echo "这是第二行标准输出"
sleep 1
echo "这是标准错误输出" >&2
sleep 1
echo "测试脚本执行完成"
exit 0 