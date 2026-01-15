#!/bin/bash
# 测试CORS配置

LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo "🔍 测试CORS配置"
echo "=========================================="
echo "本机IP: $LOCAL_IP"
echo ""

echo "1️⃣ 测试 localhost origin"
echo "----------------------------------------"
curl -s -H "Origin: http://localhost:8080" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     http://localhost:8000/api/v1/health/ \
     -i | grep -E "(HTTP|Access-Control|origin)"

echo ""
echo "2️⃣ 测试局域网IP origin"
echo "----------------------------------------"
curl -s -H "Origin: http://$LOCAL_IP:8080" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     http://$LOCAL_IP:8000/api/v1/health/ \
     -i | grep -E "(HTTP|Access-Control|origin)"

echo ""
echo "3️⃣ 检查后端配置"
echo "----------------------------------------"
echo "backend/.env 中的 CORS 配置:"
grep "BACKEND_CORS_ORIGINS" backend/.env

echo ""
echo "=========================================="
