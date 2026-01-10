#!/bin/bash
# sync_api.sh - 同步后端 API 规范到前端
# Synchronize backend API specification to frontend

set -e

echo "🔄 正在同步 AssetFlow API 规范..."
echo "🔄 Synchronizing AssetFlow API specification..."

# Configuration
BACKEND_URL="http://localhost:8000"
OPENAPI_FILE="openapi.json"

# Check if backend is running
echo "📡 检查后端服务状态..."
echo "📡 Checking backend service status..."

if ! curl -s "${BACKEND_URL}/health" > /dev/null; then
    echo "⚠️  后端服务未运行，尝试从应用生成规范..."
    echo "⚠️  Backend service not running, trying to generate spec from app..."
    
    # Try to generate OpenAPI spec directly from the app
    if command -v uv &> /dev/null; then
        echo "🔧 使用应用直接生成 OpenAPI 规范..."
        echo "🔧 Generating OpenAPI spec directly from app..."
        
        uv run python -c "
from app.main import app
import json
with open('${OPENAPI_FILE}', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
print('OpenAPI specification generated successfully')
"
        
        if [ ! -f "${OPENAPI_FILE}" ]; then
            echo "❌ 无法生成 OpenAPI 规范"
            echo "❌ Failed to generate OpenAPI specification"
            echo "   请先启动后端服务："
            echo "   Please start the backend service first:"
            echo "   uv run uvicorn app.main:app --reload"
            exit 1
        fi
    else
        echo "❌ UV 未安装，无法生成规范"
        echo "❌ UV not installed, cannot generate specification"
        exit 1
    fi
else
    echo "✅ 后端服务运行正常"
    echo "✅ Backend service is running"
    
    # Fetch OpenAPI specification from running service
    echo "📥 获取最新的 API 规范..."
    echo "📥 Fetching latest API specification..."
    
    curl -s "${BACKEND_URL}/api/v1/openapi.json" > "${OPENAPI_FILE}"
    
    if [ ! -f "${OPENAPI_FILE}" ]; then
        echo "❌ 无法获取 OpenAPI 规范"
        echo "❌ Failed to fetch OpenAPI specification"
        exit 1
    fi
fi

echo "✅ API 规范获取成功"
echo "✅ API specification fetched successfully"

# Validate OpenAPI specification
echo "🔍 验证 API 规范格式..."
echo "🔍 Validating API specification format..."

if ! python3 -c "import json; json.load(open('${OPENAPI_FILE}'))" 2>/dev/null; then
    echo "❌ OpenAPI 规范格式无效"
    echo "❌ Invalid OpenAPI specification format"
    exit 1
fi

echo "✅ API 规范格式验证通过"
echo "✅ API specification format validated"

# Use our custom Python generator
echo "🔧 使用内置生成器创建客户端代码..."
echo "🔧 Using built-in generator to create client code..."

if command -v uv &> /dev/null; then
    uv run python scripts/generate_api_client.py
else
    python3 scripts/generate_api_client.py
fi

# Summary
echo ""
echo "🎉 API 同步完成！"
echo "🎉 API synchronization completed!"
echo ""
echo "📋 生成的文件 / Generated files:"
echo "   📄 ${OPENAPI_FILE} - OpenAPI 规范"
echo "   📄 api_types.ts - TypeScript 类型定义"
echo "   📄 api_client.dart - Dart 客户端"
echo ""
echo "📚 下一步 / Next steps:"
echo "   1. 将文件复制到前端项目 / Copy files to frontend project"
echo "   2. 安装必要依赖 / Install required dependencies"
echo "   3. 配置基础 URL 和认证 / Configure base URL and authentication"
echo ""
echo "🔧 如需外部代码生成工具，请安装："
echo "🔧 For external code generation tools, please install:"
echo "   npm install -g @openapitools/openapi-generator-cli"