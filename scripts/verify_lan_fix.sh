#!/bin/bash
# 验证局域网访问修复

echo "🔍 验证局域网访问修复"
echo "=========================================="

# 获取本机IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "📍 本机IP: $LOCAL_IP"
echo ""

echo "✅ 修复内容:"
echo "1. 更新了 backend/.env 的CORS配置，包含 $LOCAL_IP"
echo "2. 重新生成了 frontend/lib/core/services/api_service.g.dart"
echo ""

echo "📋 下一步操作:"
echo "=========================================="
echo ""
echo "1️⃣ 启动后端服务（终端1）:"
echo "   cd backend"
echo "   bash ../scripts/start_backend_lan.sh"
echo ""
echo "2️⃣ 启动前端服务（终端2）:"
echo "   cd frontend"
echo "   bash ../scripts/start_frontend_lan.sh"
echo ""
echo "3️⃣ 访问应用:"
echo "   局域网地址: http://$LOCAL_IP:8080/#/login"
echo ""
echo "4️⃣ 如果仍然白屏:"
echo "   - 在浏览器中按 Cmd+Shift+R 强制刷新"
echo "   - 打开浏览器开发者工具 (F12)"
echo "   - 查看 Console 标签是否有错误"
echo "   - 查看 Network 标签，确认API请求地址是 http://$LOCAL_IP:8000"
echo ""
echo "=========================================="
