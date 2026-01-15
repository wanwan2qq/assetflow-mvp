#!/bin/bash
# 检查前端资源加载

LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo "🔍 检查前端资源加载"
echo "=========================================="
echo "本机IP: $LOCAL_IP"
echo ""

echo "1️⃣ 测试前端首页"
echo "----------------------------------------"
echo "localhost访问:"
curl -s http://localhost:8080/ | head -20
echo ""

echo "局域网IP访问:"
curl -s http://$LOCAL_IP:8080/ | head -20
echo ""

echo "2️⃣ 检查关键资源"
echo "----------------------------------------"

# 检查flutter_bootstrap.js
echo "检查 flutter_bootstrap.js..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$LOCAL_IP:8080/flutter_bootstrap.js)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ flutter_bootstrap.js 可访问 (HTTP $HTTP_CODE)"
else
    echo "❌ flutter_bootstrap.js 不可访问 (HTTP $HTTP_CODE)"
fi

# 检查main.dart.js
echo "检查 main.dart.js..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$LOCAL_IP:8080/main.dart.js)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ main.dart.js 可访问 (HTTP $HTTP_CODE)"
else
    echo "⚠️  main.dart.js 不可访问 (HTTP $HTTP_CODE) - 开发模式正常"
fi

echo ""
echo "3️⃣ 检查Flutter进程"
echo "----------------------------------------"
FLUTTER_PID=$(ps aux | grep "dartvm" | grep "8080" | grep -v grep | awk '{print $2}')
if [ -n "$FLUTTER_PID" ]; then
    echo "✅ Flutter进程运行中 (PID: $FLUTTER_PID)"
    ps aux | grep "$FLUTTER_PID" | grep -v grep
else
    echo "❌ Flutter进程未运行"
fi

echo ""
echo "=========================================="
