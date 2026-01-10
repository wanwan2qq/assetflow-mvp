#!/bin/bash

# sync_api.sh - 同步后端 API 规范到前端
set -e

echo "🔄 正在获取最新的 API 规范..."

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ 后端服务未运行，请先启动后端服务"
    echo "   cd backend && uvicorn app.main:app --reload"
    exit 1
fi

# Download OpenAPI spec
curl -s http://localhost:8000/api/v1/openapi.json > openapi.json

if [ ! -s openapi.json ]; then
    echo "❌ 无法获取 API 规范，请检查后端服务"
    exit 1
fi

echo "✅ API 规范下载完成"

# Generate Dart client code using npx
echo "🔧 生成 Dart 客户端代码..."

# Create generated directory if it doesn't exist
mkdir -p lib/generated/api/

# Generate Dart client code
npx @openapitools/openapi-generator-cli generate \
    -i openapi.json \
    -g dart-dio \
    -o lib/generated/api/ \
    --additional-properties=pubName=assetflow_api,pubVersion=1.0.0 \
    --skip-validate-spec

echo "✅ Dart 客户端代码生成完成"

# Run code generation for Riverpod and other annotations
echo "🔧 运行代码生成..."
if command -v flutter &> /dev/null; then
    flutter packages pub get
    flutter packages pub run build_runner build --delete-conflicting-outputs
    echo "✅ 代码生成完成"
else
    echo "⚠️  Flutter 未安装，请手动运行:"
    echo "   flutter packages pub get"
    echo "   flutter packages pub run build_runner build --delete-conflicting-outputs"
fi

# Clean up
rm -f openapi.json

echo "🎉 API 同步完成！"
echo ""
echo "📝 生成的文件:"
echo "   - lib/generated/api/ (API 客户端)"
echo "   - lib/**/*.g.dart (Riverpod 生成文件)"
echo ""
echo "💡 提示: 如果遇到编译错误，请检查生成的代码并手动调整"