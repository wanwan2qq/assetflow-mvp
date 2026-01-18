#!/bin/bash

echo "=========================================="
echo "修复 Git 版本控制"
echo "=========================================="

# 1. 修复 .gitignore
echo ""
echo "1. 检查 .gitignore 修复..."
if grep -q "/backend/lib/" .gitignore; then
    echo "✅ .gitignore 已修复"
else
    echo "❌ .gitignore 需要手动修复"
    echo "   请查看 docs/Important/FRONTEND_GIT_FIX.md"
    exit 1
fi

# 2. 添加前端源代码
echo ""
echo "2. 添加前端源代码..."
cd frontend
git add lib/
added_count=$(git status --short | grep "^A" | grep "lib/" | wc -l | tr -d ' ')
echo "✅ 添加了 $added_count 个文件"

# 3. 添加后端核心功能
echo ""
echo "3. 添加后端核心功能..."
cd ..
git add backend/app/core/prompt_manager.py 2>/dev/null
git add backend/app/prompts/ 2>/dev/null
git add backend/alembic/versions/ 2>/dev/null
echo "✅ 后端核心功能已添加"

# 4. 添加新增的脚本
echo ""
echo "4. 添加新增的脚本..."
git add backend/scripts/demo_*.py 2>/dev/null
git add backend/scripts/validate_*.py 2>/dev/null
git add backend/scripts/download_bge_model.py 2>/dev/null
git add backend/tests/test_portfolio_analyzer_refactor.py 2>/dev/null
git add backend/tests/test_prompt_manager.py 2>/dev/null
echo "✅ 新增脚本已添加"

# 5. 添加文档
echo ""
echo "5. 添加文档..."
git add docs/Important/ 2>/dev/null
git add docs/Memory/ 2>/dev/null
git add docs/PortfolioAnalyzer/ 2>/dev/null
git add docs/Prompt_Optimize/ 2>/dev/null
git add docs/OPTIMIZATION_*.md 2>/dev/null
git add docs/fix_summary/ 2>/dev/null
git add docs/guides/DASHBOARD_*.md 2>/dev/null
echo "✅ 文档已添加"

# 6. 显示状态
echo ""
echo "=========================================="
echo "Git 状态"
echo "=========================================="
git status --short | head -30

echo ""
echo "=========================================="
echo "✅ 完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 检查添加的文件: git status"
echo "2. 提交更改: git commit -m 'Fix Git tracking and add missing files'"
echo "3. 推送到远程: git push"
echo ""
echo "详细说明请查看: docs/Important/FRONTEND_GIT_FIX.md"
