#!/bin/bash
# 终极白屏修复方案

echo "🔧 AssetFlow 局域网白屏 - 终极修复方案"
echo "=========================================="

LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "📍 本机IP: $LOCAL_IP"
echo ""

echo "📊 当前状态检查"
echo "----------------------------------------"

# 检查CORS
echo "1. CORS配置..."
CORS_TEST=$(curl -s -H "Origin: http://$LOCAL_IP:8080" -X OPTIONS http://$LOCAL_IP:8000/api/v1/health/ -i | grep "access-control-allow-origin")
if echo "$CORS_TEST" | grep -q "$LOCAL_IP"; then
    echo "   ✅ CORS配置正确"
else
    echo "   ❌ CORS配置错误"
    echo "   需要重启后端服务"
fi

# 检查前端服务
echo "2. 前端服务..."
FRONTEND_PID=$(ps aux | grep "dartvm" | grep "8080" | grep -v grep | awk '{print $2}')
if [ -n "$FRONTEND_PID" ]; then
    echo "   ✅ 前端服务运行中 (PID: $FRONTEND_PID)"
else
    echo "   ❌ 前端服务未运行"
fi

# 检查后端服务
echo "3. 后端服务..."
BACKEND_PID=$(ps aux | grep "uvicorn" | grep "8000" | grep -v grep | awk '{print $2}')
if [ -n "$BACKEND_PID" ]; then
    echo "   ✅ 后端服务运行中 (PID: $BACKEND_PID)"
else
    echo "   ❌ 后端服务未运行"
fi

echo ""
echo "🎯 问题分析"
echo "=========================================="
echo ""
echo "Flutter Web 在开发模式下通过局域网IP访问时，"
echo "可能会遇到以下问题："
echo ""
echo "1. 热重载状态不一致"
echo "2. 开发服务器的WebSocket连接问题"
echo "3. 浏览器缓存的旧代码"
echo ""

echo "💡 解决方案"
echo "=========================================="
echo ""
echo "方案A: 完全重启（推荐）"
echo "----------------------------------------"
echo "1. 停止所有服务"
echo "2. 清理Flutter缓存"
echo "3. 重新启动服务"
echo ""
echo "执行命令:"
echo "  bash scripts/ultimate_white_screen_fix.sh --restart"
echo ""

echo "方案B: 使用生产构建"
echo "----------------------------------------"
echo "1. 构建生产版本"
echo "2. 使用HTTP服务器提供服务"
echo ""
echo "执行命令:"
echo "  cd frontend"
echo "  bash ../scripts/build_and_serve_lan.sh"
echo ""

echo "方案C: 使用localhost + 端口转发"
echo "----------------------------------------"
echo "1. 在本机使用 localhost:8080 访问"
echo "2. 在其他设备上，配置hosts文件指向本机IP"
echo ""

# 如果传入 --restart 参数，执行完全重启
if [ "$1" = "--restart" ]; then
    echo ""
    echo "🔄 执行完全重启..."
    echo "=========================================="
    
    # 停止前端
    if [ -n "$FRONTEND_PID" ]; then
        echo "停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 2
    fi
    
    # 停止后端
    if [ -n "$BACKEND_PID" ]; then
        echo "停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 2
    fi
    
    # 清理Flutter缓存
    echo "清理Flutter缓存..."
    cd frontend
    flutter clean
    flutter pub get
    cd ..
    
    echo ""
    echo "✅ 清理完成"
    echo ""
    echo "📋 下一步操作:"
    echo "----------------------------------------"
    echo "1. 启动后端（终端1）:"
    echo "   cd backend"
    echo "   bash ../scripts/start_backend_lan.sh"
    echo ""
    echo "2. 启动前端（终端2）:"
    echo "   cd frontend"
    echo "   bash ../scripts/start_frontend_lan.sh"
    echo ""
    echo "3. 访问应用:"
    echo "   http://$LOCAL_IP:8080/#/login"
    echo ""
    echo "4. 强制刷新浏览器:"
    echo "   Cmd+Shift+R (Mac) 或 Ctrl+Shift+R (Windows)"
    echo ""
fi

echo "=========================================="
