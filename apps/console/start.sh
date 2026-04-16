#!/bin/bash

echo "================================"
echo "  VCE Console 启动脚本"
echo "================================"
echo ""

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "[1/2] 正在安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "依赖安装失败！"
        exit 1
    fi
    echo ""
fi

# 启动开发服务器
echo "[2/2] 启动开发服务器 (端口 3000)..."
echo "API 代理目标: http://localhost:8000"
echo ""
npm run dev
