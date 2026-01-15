#!/bin/bash
# 重启所有服务以应用新配置

echo "🔄 重启服务以应用局域网配置"
echo "=========================================="

LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "📍 本机IP: $LOCAL_IP"
echo ""

echo "1️⃣ 停止现有服务..."
echo "----------------------------------------"

# 停止后端
echo "停止后端服务..."
BACKEND_PID=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')
if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID
    echo "✅ 后端服务已停止 (PID: $BACKEND_PID)"
    sleep 2
else
    echo "⚠️  后端服务未运行"
fi

# 停止前端
echo "停止前端服务..."
FRONTEND_PID=$(ps aux | grep "flutter run" | grep -v grep | awk '{print $2}')
if [ -n "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID
    echo "✅ 前端服务已停止 (PID: $FRONTEND_PID)"
    sleep 2
else
    echo "⚠️  前端服务未运行"
fi

echo ""
echo "2️⃣ 验证配置..."
echo "----------------------------------------"
echo "CORS配置:"
grep "BACKEND_CORS_ORIGINS" backend/.env
echo ""

echo "3️⃣ 启动服务..."
echo "----------------------------------------"
echo ""
echo "⚠️  请在两个不同的终端窗口中运行以下命令："
echo ""
echo "终端1 - 启动后端:"
echo "  cd backend"
echo "  bash ../scripts/start_backend_lan.sh"
echo ""
echo "终端2 - 启动前端:"
echo "  cd frontend"
echo "  bash ../scripts/start_frontend_lan.sh"
echo ""
echo "=========================================="
echo "📱 启动后访问:"
echo "  http://$LOCAL_IP:8080/#/login"
echo ""
echo "💡 提示: 首次访问请按 Cmd+Shift+R 强制刷新"
echo "=========================================="
