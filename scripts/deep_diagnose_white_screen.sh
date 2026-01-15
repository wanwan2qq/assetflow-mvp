#!/bin/bash
# 深度诊断白屏问题

echo "🔍 深度诊断白屏问题"
echo "=========================================="

LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "📍 本机IP: $LOCAL_IP"
echo ""

echo "1️⃣ 检查所有硬编码的localhost引用"
echo "----------------------------------------"
echo "在 Dart 文件中搜索 localhost..."
grep -r "localhost" frontend/lib --include="*.dart" | grep -v "test" | grep -v ".g.dart" | grep -v "generated/api"
echo ""

echo "2️⃣ 检查生成的文件"
echo "----------------------------------------"
echo "api_client.g.dart:"
if [ -f "frontend/lib/core/api/api_client.g.dart" ]; then
    grep "baseUrl" frontend/lib/core/api/api_client.g.dart || echo "  未找到 baseUrl"
else
    echo "  文件不存在"
fi

echo ""
echo "api_service.g.dart:"
if [ -f "frontend/lib/core/services/api_service.g.dart" ]; then
    grep "baseUrl" frontend/lib/core/services/api_service.g.dart || echo "  未找到 baseUrl"
else
    echo "  文件不存在"
fi

echo ""
echo "websocket_service.g.dart:"
if [ -f "frontend/lib/core/services/websocket_service.g.dart" ]; then
    grep "ws://" frontend/lib/core/services/websocket_service.g.dart || echo "  未找到 ws://"
else
    echo "  文件不存在"
fi

echo ""
echo "3️⃣ 检查前端构建配置"
echo "----------------------------------------"
if [ -d "frontend/build/web" ]; then
    echo "✅ build/web 目录存在"
    echo "检查 main.dart.js..."
    if [ -f "frontend/build/web/main.dart.js" ]; then
        echo "✅ main.dart.js 存在"
        # 检查是否包含硬编码的localhost
        if grep -q "localhost:8000" frontend/build/web/main.dart.js 2>/dev/null; then
            echo "⚠️  main.dart.js 包含硬编码的 localhost:8000"
            echo "   需要重新构建前端"
        else
            echo "✅ main.dart.js 不包含硬编码的 localhost"
        fi
    else
        echo "❌ main.dart.js 不存在"
    fi
else
    echo "⚠️  build/web 目录不存在（开发模式正常）"
fi

echo ""
echo "4️⃣ 检查后端服务"
echo "----------------------------------------"
echo "测试后端健康检查..."
HEALTH_RESPONSE=$(curl -s http://$LOCAL_IP:8000/api/v1/health/ 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ 后端服务正常"
    echo "   响应: $HEALTH_RESPONSE"
else
    echo "❌ 后端服务无法访问"
    echo "   错误: $HEALTH_RESPONSE"
fi

echo ""
echo "测试CORS..."
CORS_RESPONSE=$(curl -s -H "Origin: http://$LOCAL_IP:8080" -H "Access-Control-Request-Method: GET" -X OPTIONS http://$LOCAL_IP:8000/api/v1/health/ -i 2>&1)
if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo "✅ CORS配置正常"
else
    echo "❌ CORS配置可能有问题"
    echo "$CORS_RESPONSE"
fi

echo ""
echo "5️⃣ 检查前端服务"
echo "----------------------------------------"
echo "测试前端服务..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://$LOCAL_IP:8080 2>&1)
if [ "$FRONTEND_RESPONSE" = "200" ]; then
    echo "✅ 前端服务正常 (HTTP $FRONTEND_RESPONSE)"
else
    echo "❌ 前端服务异常 (HTTP $FRONTEND_RESPONSE)"
fi

echo ""
echo "6️⃣ 检查Flutter进程"
echo "----------------------------------------"
FLUTTER_PROCESS=$(ps aux | grep "flutter run" | grep -v grep)
if [ -n "$FLUTTER_PROCESS" ]; then
    echo "✅ Flutter进程运行中"
    echo "$FLUTTER_PROCESS"
else
    echo "❌ Flutter进程未运行"
fi

echo ""
echo "7️⃣ 检查端口占用"
echo "----------------------------------------"
echo "检查 8080 端口..."
PORT_8080=$(lsof -i :8080 2>/dev/null)
if [ -n "$PORT_8080" ]; then
    echo "✅ 8080端口被占用（正常）"
    echo "$PORT_8080" | head -2
else
    echo "❌ 8080端口未被占用"
fi

echo ""
echo "检查 8000 端口..."
PORT_8000=$(lsof -i :8000 2>/dev/null)
if [ -n "$PORT_8000" ]; then
    echo "✅ 8000端口被占用（正常）"
    echo "$PORT_8000" | head -2
else
    echo "❌ 8000端口未被占用"
fi

echo ""
echo "=========================================="
echo "📋 建议的修复步骤"
echo "=========================================="
echo ""

# 检查是否需要重新生成代码
NEEDS_REBUILD=false

if grep -q "localhost:8000" frontend/lib/core/api/api_client.dart 2>/dev/null; then
    echo "⚠️  api_client.dart 仍包含硬编码的 localhost"
    NEEDS_REBUILD=true
fi

if grep -q "ws://localhost:8000" frontend/lib/core/services/websocket_service.dart 2>/dev/null; then
    echo "⚠️  websocket_service.dart 仍包含硬编码的 localhost"
    NEEDS_REBUILD=true
fi

if [ "$NEEDS_REBUILD" = true ]; then
    echo ""
    echo "1. 重新生成Flutter代码:"
    echo "   cd frontend"
    echo "   flutter pub run build_runner build --delete-conflicting-outputs"
    echo ""
fi

echo "2. 停止所有服务"
echo ""
echo "3. 重新启动后端（终端1）:"
echo "   cd backend"
echo "   bash ../scripts/start_backend_lan.sh"
echo ""
echo "4. 重新启动前端（终端2）:"
echo "   cd frontend"
echo "   bash ../scripts/start_frontend_lan.sh"
echo ""
echo "5. 清除浏览器缓存并强制刷新:"
echo "   Cmd+Shift+R (Mac) 或 Ctrl+Shift+R (Windows)"
echo ""
echo "6. 如果仍然白屏，检查浏览器控制台:"
echo "   - 打开开发者工具 (F12)"
echo "   - 查看 Console 标签的错误信息"
echo "   - 查看 Network 标签的请求"
echo "   - 截图并提供错误信息"
echo ""
