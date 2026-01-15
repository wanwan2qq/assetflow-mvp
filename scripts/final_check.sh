#!/bin/bash
# 最终验证脚本

echo "🎯 局域网访问白屏修复 - 最终验证"
echo "=========================================="
echo ""

# 获取本机IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo "✅ 修复完成检查:"
echo ""

# 检查1: CORS配置
echo "1️⃣ CORS配置检查..."
if grep -q "$LOCAL_IP" backend/.env; then
    echo "   ✅ backend/.env 包含局域网IP ($LOCAL_IP)"
else
    echo "   ❌ backend/.env 缺少局域网IP"
    exit 1
fi

# 检查2: 生成文件
echo ""
echo "2️⃣ Flutter生成文件检查..."
if [ -f "frontend/lib/core/services/api_service.g.dart" ]; then
    API_TIME=$(stat -f %m frontend/lib/core/services/api_service.dart 2>/dev/null)
    GEN_TIME=$(stat -f %m frontend/lib/core/services/api_service.g.dart 2>/dev/null)
    
    if [ "$GEN_TIME" -ge "$API_TIME" ]; then
        echo "   ✅ api_service.g.dart 是最新的"
    else
        echo "   ⚠️  api_service.g.dart 需要更新"
        echo "   运行: cd frontend && flutter pub run build_runner build --delete-conflicting-outputs"
        exit 1
    fi
else
    echo "   ❌ api_service.g.dart 不存在"
    exit 1
fi

# 检查3: 动态API配置
echo ""
echo "3️⃣ 动态API配置检查..."
if grep -q "_getApiBaseUrl" frontend/lib/core/services/api_service.dart; then
    echo "   ✅ 动态API配置已启用"
else
    echo "   ❌ 动态API配置未启用"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 所有检查通过！"
echo ""
echo "📋 下一步操作:"
echo ""
echo "1. 启动后端服务（终端1）:"
echo "   cd backend && bash ../scripts/start_backend_lan.sh"
echo ""
echo "2. 启动前端服务（终端2）:"
echo "   cd frontend && bash ../scripts/start_frontend_lan.sh"
echo ""
echo "3. 访问应用:"
echo "   http://$LOCAL_IP:8080/#/login"
echo ""
echo "4. 强制刷新浏览器:"
echo "   按 Cmd+Shift+R (Mac) 或 Ctrl+Shift+R (Windows)"
echo ""
echo "=========================================="
echo "📚 相关文档:"
echo "   - WHITE_SCREEN_FIX_FINAL.md (完整修复方案)"
echo "   - QUICK_FIX_REFERENCE.md (快速参考)"
echo "   - LAN_ACCESS_FIX_COMPLETE.md (技术文档)"
echo ""
