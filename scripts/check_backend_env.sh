#!/bin/bash
# 检查后端环境配置

echo "🔍 AssetFlow 后端环境检查"
echo "=========================================="

# 检查是否在 backend 目录
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 错误: 请在 backend 目录下运行"
    echo "使用方法: cd backend && bash ../scripts/check_backend_env.sh"
    exit 1
fi

echo ""
echo "1️⃣ 检查Python版本..."
python3 --version

echo ""
echo "2️⃣ 检查虚拟环境..."
if [ -d ".venv" ]; then
    echo "✅ 虚拟环境存在: .venv/"
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    echo "✅ 虚拟环境已激活"
    echo "   Python路径: $(which python)"
    echo "   Python版本: $(python --version)"
else
    echo "❌ 虚拟环境不存在"
    echo "   请运行: python3 -m venv .venv"
    exit 1
fi

echo ""
echo "3️⃣ 检查关键依赖..."

# 检查 sqlmodel
python -c "import sqlmodel; print('✅ sqlmodel:', sqlmodel.__version__)" 2>/dev/null || echo "❌ sqlmodel 未安装"

# 检查 fastapi
python -c "import fastapi; print('✅ fastapi:', fastapi.__version__)" 2>/dev/null || echo "❌ fastapi 未安装"

# 检查 uvicorn
python -c "import uvicorn; print('✅ uvicorn:', uvicorn.__version__)" 2>/dev/null || echo "❌ uvicorn 未安装"

# 检查 pydantic
python -c "import pydantic; print('✅ pydantic:', pydantic.__version__)" 2>/dev/null || echo "❌ pydantic 未安装"

echo ""
echo "4️⃣ 检查配置文件..."
if [ -f ".env" ]; then
    echo "✅ .env 文件存在"
else
    echo "⚠️  .env 文件不存在（将使用默认配置）"
fi

if [ -f "pyproject.toml" ]; then
    echo "✅ pyproject.toml 存在"
else
    echo "❌ pyproject.toml 不存在"
fi

echo ""
echo "5️⃣ 检查数据库..."
if [ -f "assetflow.db" ]; then
    echo "✅ 数据库文件存在: assetflow.db"
    echo "   大小: $(du -h assetflow.db | cut -f1)"
else
    echo "⚠️  数据库文件不存在（首次运行时会自动创建）"
fi

echo ""
echo "=========================================="
echo "环境检查完成！"
echo ""

# 检查是否所有依赖都已安装
python -c "import sqlmodel, fastapi, uvicorn" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 所有关键依赖已安装，可以启动服务"
    echo ""
    echo "启动命令:"
    echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
else
    echo "❌ 部分依赖缺失，请先安装:"
    echo "  pip install -e ."
fi