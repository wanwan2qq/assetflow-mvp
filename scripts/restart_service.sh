#!/bin/bash

echo "=========================================="
echo "重启 AssetFlow Backend 服务"
echo "=========================================="

# 停止旧进程
echo ""
echo "1. 停止旧进程..."
pkill -f "uvicorn app.main:app" 2>/dev/null
sleep 2

# 确认进程已停止
if ps aux | grep -v grep | grep "uvicorn app.main:app" > /dev/null; then
    echo "⚠️  警告：仍有进程在运行，强制杀死..."
    pkill -9 -f "uvicorn app.main:app"
    sleep 1
fi

echo "✅ 旧进程已停止"

# 清除 Python 缓存
echo ""
echo "2. 清除 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "✅ 缓存已清除"

# 检查代码修复
echo ""
echo "3. 验证代码修复..."
if grep -q "os.environ\['HF_HUB_OFFLINE'\] = '1'" app/services/memory_service.py; then
    echo "✅ 离线模式代码已更新"
else
    echo "❌ 警告：离线模式代码未找到"
fi

# 启动服务
echo ""
echo "4. 启动服务..."
echo "=========================================="
echo ""

uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
