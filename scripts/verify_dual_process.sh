#!/bin/bash

# Verification script for Dual-Process Cognitive Architecture
# This script checks that all components are in place

echo "=========================================="
echo "Dual-Process Architecture Verification"
echo "=========================================="
echo ""

# Check if key files exist
echo "📁 Checking key files..."

files=(
    "backend/app/services/chat_agent.py"
    "backend/app/services/asset_extraction_service.py"
    "scripts/test_dual_process_architecture.py"
    "docs/Memory/DUAL_PROCESS_ARCHITECTURE_REFACTOR.md"
    "docs/Memory/DUAL_PROCESS_QUICK_REFERENCE.md"
    "DUAL_PROCESS_ARCHITECTURE_COMPLETE.md"
)

all_files_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
        all_files_exist=false
    fi
done

echo ""

# Check for key method in chat_agent.py
echo "🔍 Checking for _refresh_context_from_db method..."
if grep -q "_refresh_context_from_db" backend/app/services/chat_agent.py; then
    echo "  ✅ _refresh_context_from_db method found"
else
    echo "  ❌ _refresh_context_from_db method NOT FOUND"
    all_files_exist=false
fi

echo ""

# Check for context refresh calls
echo "🔍 Checking for context refresh integration..."
if grep -q "await self._refresh_context_from_db" backend/app/services/chat_agent.py; then
    count=$(grep -c "await self._refresh_context_from_db" backend/app/services/chat_agent.py)
    echo "  ✅ Context refresh called in $count places"
else
    echo "  ❌ Context refresh NOT integrated"
    all_files_exist=false
fi

echo ""

# Check Python syntax
echo "🐍 Checking Python syntax..."
cd backend
if python -m py_compile app/services/chat_agent.py 2>/dev/null; then
    echo "  ✅ chat_agent.py syntax OK"
else
    echo "  ❌ chat_agent.py has syntax errors"
    all_files_exist=false
fi

if python -m py_compile app/services/asset_extraction_service.py 2>/dev/null; then
    echo "  ✅ asset_extraction_service.py syntax OK"
else
    echo "  ❌ asset_extraction_service.py has syntax errors"
    all_files_exist=false
fi
cd ..

echo ""
echo "=========================================="

if [ "$all_files_exist" = true ]; then
    echo "✅ ALL CHECKS PASSED!"
    echo ""
    echo "Next steps:"
    echo "  1. Run tests: python scripts/test_dual_process_architecture.py"
    echo "  2. Review docs: docs/Memory/DUAL_PROCESS_ARCHITECTURE_REFACTOR.md"
    echo "  3. Deploy to production"
    exit 0
else
    echo "❌ SOME CHECKS FAILED"
    echo ""
    echo "Please review the errors above and fix them."
    exit 1
fi
