#!/bin/bash
# 启动前端服务支持局域网访问

echo "🚀 启动 AssetFlow 前端服务 (局域网访问)"
echo "=========================================="

# 检查是否在 frontend 目录
if [ ! -f "pubspec.yaml" ]; then
    echo "❌ 错误: 请在 frontend 目录下运行此脚本"
    echo "使用方法: cd frontend && bash ../scripts/start_frontend_lan.sh"
    exit 1
fi

# 获取本机IP地址
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "📍 本机IP地址: $LOCAL_IP"

# 检查Flutter版本
echo "� 检查Flutter版本..."
FLUTTER_VERSION=$(flutter --version | head -1)
echo "   $FLUTTER_VERSION"

# 启动 Flutter Web 服务
echo ""
echo "🔧 启动参数:"
echo "  - 端口: 8080"
echo "  - 主机: 0.0.0.0 (允许局域网访问)"
echo "  - 平台: Chrome Web"
echo ""

echo "🌐 访问地址:"
echo "  - 本地: http://localhost:8080/#/login"
echo "  - 局域网: http://$LOCAL_IP:8080/#/login"
echo ""

echo "⚠️  注意事项:"
echo "  1. 确保后端服务运行在 http://localhost:8000 或 http://$LOCAL_IP:8000"
echo "  2. 确保防火墙允许 8080 端口"
echo "  3. 如果仍然白屏，请检查浏览器控制台错误"
echo "  4. 首次启动可能需要下载依赖，请耐心等待"
echo ""

# 启动服务（移除不支持的 --web-renderer 参数）
echo "🚀 正在启动服务..."
echo "按 q 停止服务"
echo ""

flutter run -d chrome --web-port=8080 --web-hostname=0.0.0.0