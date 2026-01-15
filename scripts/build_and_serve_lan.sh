#!/bin/bash
# 构建并服务前端（生产模式）

echo "🏗️  构建并服务 AssetFlow 前端（生产模式）"
echo "=========================================="

# 检查是否在 frontend 目录
if [ ! -f "pubspec.yaml" ]; then
    echo "❌ 错误: 请在 frontend 目录下运行此脚本"
    echo "使用方法: cd frontend && bash ../scripts/build_and_serve_lan.sh"
    exit 1
fi

# 获取本机IP地址
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "📍 本机IP地址: $LOCAL_IP"
echo ""

echo "1️⃣ 构建前端..."
echo "----------------------------------------"
flutter build web --release

if [ $? -ne 0 ]; then
    echo "❌ 构建失败"
    exit 1
fi

echo ""
echo "✅ 构建完成"
echo ""

echo "2️⃣ 启动HTTP服务器..."
echo "----------------------------------------"

# 检查是否安装了Python
if command -v python3 &> /dev/null; then
    echo "使用 Python HTTP 服务器"
    echo ""
    echo "🌐 访问地址:"
    echo "  - 本地: http://localhost:8080/#/login"
    echo "  - 局域网: http://$LOCAL_IP:8080/#/login"
    echo ""
    echo "按 Ctrl+C 停止服务"
    echo ""
    
    cd build/web
    python3 -m http.server 8080 --bind 0.0.0.0
else
    echo "❌ 未找到 Python3"
    echo "请安装 Python3 或使用其他HTTP服务器"
    exit 1
fi
