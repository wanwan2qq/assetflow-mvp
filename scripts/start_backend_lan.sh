#!/bin/bash
# 启动后端服务支持局域网访问

echo "🚀 启动 AssetFlow 后端服务 (局域网访问)"
echo "=========================================="

# 检查是否在 backend 目录
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 错误: 请在 backend 目录下运行此脚本"
    echo "使用方法: cd backend && bash ../scripts/start_backend_lan.sh"
    exit 1
fi

# 获取本机IP地址
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "📍 本机IP地址: $LOCAL_IP"

# 检查并激活虚拟环境
echo "🔍 检查虚拟环境..."
if [ -d ".venv" ]; then
    echo "✅ 找到虚拟环境，正在激活..."
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活: $(which python)"
elif [ -d "venv" ]; then
    echo "✅ 找到虚拟环境，正在激活..."
    source venv/bin/activate
    echo "✅ 虚拟环境已激活: $(which python)"
else
    echo "⚠️  警告: 未找到虚拟环境 (.venv 或 venv)"
    echo "正在创建虚拟环境..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "✅ 虚拟环境已创建并激活"
    
    echo "📦 安装依赖..."
    pip install -e .
fi

# 检查关键依赖
echo "🔍 检查关键依赖..."
python -c "import sqlmodel" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ sqlmodel 未安装，正在安装依赖..."
    pip install -e .
fi

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到 .env 文件，将使用默认配置"
    echo "建议创建 .env 文件并配置 BACKEND_CORS_ORIGINS"
fi

# 启动参数说明
echo ""
echo "🔧 启动参数:"
echo "  - Python: $(which python)"
echo "  - 主机: 0.0.0.0 (允许局域网访问)"
echo "  - 端口: 8000"
echo "  - 模式: 开发模式 (自动重载)"
echo ""

echo "🌐 访问地址:"
echo "  - 本地: http://localhost:8000"
echo "  - 局域网: http://$LOCAL_IP:8000"
echo "  - API文档: http://$LOCAL_IP:8000/docs"
echo ""

echo "⚠️  注意事项:"
echo "  1. 确保防火墙允许 8000 端口"
echo "  2. 确保 CORS 配置包含前端地址"
echo "  3. 数据库文件将在当前目录创建"
echo ""

# 启动服务
echo "🚀 正在启动服务..."
echo "按 Ctrl+C 停止服务"
echo ""

# 使用 --host 0.0.0.0 允许局域网访问
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload