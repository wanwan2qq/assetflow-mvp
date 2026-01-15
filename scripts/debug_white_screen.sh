#!/bin/bash
# 调试局域网访问白屏问题

echo "🔍 AssetFlow 白屏问题调试工具"
echo "=========================================="

# 获取本机IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "📍 本机IP: $LOCAL_IP"
echo ""

echo "1️⃣ 检查后端服务..."
echo "----------------------------------------"

# 检查后端健康状态
echo "测试 localhost:8000..."
curl -s http://localhost:8000/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ localhost:8000 - 正常"
else
    echo "❌ localhost:8000 - 失败"
fi

echo "测试 $LOCAL_IP:8000..."
curl -s http://$LOCAL_IP:8000/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ $LOCAL_IP:8000 - 正常"
else
    echo "❌ $LOCAL_IP:8000 - 失败"
fi

echo ""
echo "2️⃣ 检查前端服务..."
echo "----------------------------------------"

# 检查前端是否可访问
echo "测试 localhost:8080..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ localhost:8080 - 正常 (HTTP $HTTP_CODE)"
else
    echo "❌ localhost:8080 - 异常 (HTTP $HTTP_CODE)"
fi

echo "测试 $LOCAL_IP:8080..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$LOCAL_IP:8080 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ $LOCAL_IP:8080 - 正常 (HTTP $HTTP_CODE)"
else
    echo "❌ $LOCAL_IP:8080 - 异常 (HTTP $HTTP_CODE)"
fi

echo ""
echo "3️⃣ 检查前端API配置..."
echo "----------------------------------------"

# 检查api_service.dart中的配置
if [ -f "frontend/lib/core/services/api_service.dart" ]; then
    echo "检查 api_service.dart..."
    if grep -q "_getApiBaseUrl" frontend/lib/core/services/api_service.dart; then
        echo "✅ 动态API配置已启用"
    else
        echo "❌ 动态API配置未启用（仍使用硬编码localhost）"
    fi
else
    echo "❌ api_service.dart 文件不存在"
fi

echo ""
echo "4️⃣ 检查前端构建文件..."
echo "----------------------------------------"

# 检查是否需要重新生成代码
if [ -f "frontend/lib/core/services/api_service.g.dart" ]; then
    echo "✅ api_service.g.dart 存在"
    
    # 检查文件修改时间
    API_SERVICE_TIME=$(stat -f %m frontend/lib/core/services/api_service.dart 2>/dev/null || stat -c %Y frontend/lib/core/services/api_service.dart 2>/dev/null)
    GENERATED_TIME=$(stat -f %m frontend/lib/core/services/api_service.g.dart 2>/dev/null || stat -c %Y frontend/lib/core/services/api_service.g.dart 2>/dev/null)
    
    if [ "$API_SERVICE_TIME" -gt "$GENERATED_TIME" ]; then
        echo "⚠️  api_service.dart 比生成文件新，需要重新生成"
        echo "   运行: cd frontend && flutter pub run build_runner build --delete-conflicting-outputs"
    else
        echo "✅ 生成文件是最新的"
    fi
else
    echo "❌ api_service.g.dart 不存在，需要生成"
    echo "   运行: cd frontend && flutter pub run build_runner build --delete-conflicting-outputs"
fi

echo ""
echo "5️⃣ 检查CORS配置..."
echo "----------------------------------------"

# 检查后端CORS配置
if [ -f "backend/app/core/config.py" ]; then
    echo "检查 config.py..."
    if grep -q "$LOCAL_IP" backend/app/core/config.py; then
        echo "✅ CORS配置包含当前IP ($LOCAL_IP)"
    else
        echo "⚠️  CORS配置可能不包含当前IP"
        echo "   当前配置:"
        grep "BACKEND_CORS_ORIGINS" backend/app/core/config.py | head -1
    fi
fi

# 检查.env文件
if [ -f "backend/.env" ]; then
    echo "检查 .env..."
    if grep -q "BACKEND_CORS_ORIGINS" backend/.env; then
        echo "✅ .env 中有CORS配置"
        grep "BACKEND_CORS_ORIGINS" backend/.env
    else
        echo "⚠️  .env 中没有CORS配置（使用默认值）"
    fi
fi

echo ""
echo "6️⃣ 建议的修复步骤..."
echo "=========================================="

echo ""
echo "步骤1: 重新生成前端代码"
echo "cd frontend"
echo "flutter pub run build_runner build --delete-conflicting-outputs"
echo ""

echo "步骤2: 更新CORS配置"
echo "编辑 backend/.env，添加:"
echo "BACKEND_CORS_ORIGINS=http://localhost:8080,http://$LOCAL_IP:8080"
echo ""

echo "步骤3: 重启服务"
echo "# 重启后端"
echo "cd backend && bash ../scripts/start_backend_lan.sh"
echo ""
echo "# 重启前端（新终端）"
echo "cd frontend && bash ../scripts/start_frontend_lan.sh"
echo ""

echo "步骤4: 清除浏览器缓存"
echo "在浏览器中按 Cmd+Shift+R (Mac) 或 Ctrl+Shift+R (Windows) 强制刷新"
echo ""

echo "=========================================="
echo "调试完成！"
echo ""
echo "如果问题仍然存在，请:"
echo "1. 检查浏览器控制台的 Network 标签"
echo "2. 查看是否有失败的请求"
echo "3. 检查请求的URL是否正确"