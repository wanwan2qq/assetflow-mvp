#!/bin/bash

echo "=========================================="
echo "添加前端源代码到 Git"
echo "=========================================="

# 添加 lib 目录（排除 generated）
echo ""
echo "1. 添加 lib/ 目录（排除 generated/）..."
git add lib/

# 检查添加的文件
echo ""
echo "2. 检查将要添加的文件..."
git status --short | grep "^A" | grep "lib/" | wc -l
echo "个文件将被添加"

# 显示前 20 个文件
echo ""
echo "前 20 个文件："
git status --short | grep "^A" | grep "lib/" | head -20

echo ""
echo "=========================================="
echo "✅ 完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 检查添加的文件: git status"
echo "2. 提交更改: git commit -m 'Add frontend source files'"
echo "3. 推送到远程: git push"
