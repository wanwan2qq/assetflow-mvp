# 前端 Git 版本控制修复

## 问题发现

前端项目的 **所有源代码文件**（`lib/` 目录）都没有被 Git 跟踪！

### 问题原因

根目录的 `.gitignore` 文件中有以下规则：

```gitignore
# Python
lib/
lib64/
```

这个规则本意是忽略 Python 的 `lib/` 目录，但也误伤了 Flutter 的 `lib/` 目录。

### 影响范围

- **112 个 Dart 源文件**完全没有被 Git 跟踪
- 包括所有功能代码：
  - `lib/main.dart` - 应用入口
  - `lib/core/` - 核心功能
  - `lib/features/` - 功能模块
  - `lib/shared/` - 共享组件

## 修复方案

### 1. 修改根目录 `.gitignore`

**修改前**：
```gitignore
# Python
lib/
lib64/
```

**修改后**：
```gitignore
# Python lib directories (not Flutter lib/)
/backend/lib/
/backend/lib64/
/scripts/lib/
/scripts/lib64/
```

**说明**：
- 使用路径前缀 `/backend/` 和 `/scripts/` 限定范围
- 只忽略 Python 项目中的 `lib/` 目录
- 不影响 Flutter 项目的 `lib/` 目录

### 2. 添加前端源代码

```bash
cd frontend
./add_source_files.sh
```

或手动执行：

```bash
cd frontend
git add lib/
git status
```

### 3. 提交更改

```bash
# 提交 .gitignore 修改
git add ../.gitignore
git commit -m "Fix: Update .gitignore to not ignore Flutter lib directory"

# 提交前端源代码
git add lib/
git commit -m "Add frontend source files (lib directory)"

# 推送到远程
git push
```

## 验证修复

### 检查 lib/ 目录是否被忽略

```bash
cd frontend
git check-ignore -v lib/main.dart
```

**预期输出**：
```
(空输出，说明不被忽略)
```

### 检查有多少文件将被添加

```bash
cd frontend
git status --short | grep "^??" | grep "lib/" | wc -l
```

**预期输出**：
```
112 (或类似数量)
```

### 检查生成的文件是否被正确忽略

```bash
cd frontend
git check-ignore -v lib/generated/api/test/risk_level_test.dart
```

**预期输出**：
```
frontend/.gitignore:49:lib/generated/   lib/generated/api/test/risk_level_test.dart
```

说明 `lib/generated/` 目录被正确忽略。

## 文件结构

### 应该被跟踪的文件

```
frontend/lib/
├── main.dart                          # ✅ 应该跟踪
├── core/                              # ✅ 应该跟踪
│   ├── config/
│   ├── navigation/
│   ├── providers/
│   ├── router/
│   ├── services/
│   └── theme/
├── features/                          # ✅ 应该跟踪
│   ├── auth/
│   ├── chat/
│   ├── dashboard/
│   └── profile/
├── shared/                            # ✅ 应该跟踪
│   ├── models/
│   ├── utils/
│   └── widgets/
└── generated/                         # ❌ 不应该跟踪（已在 .gitignore）
    └── api/
```

### 应该被忽略的文件

```
frontend/lib/generated/                # ❌ OpenAPI 生成的代码
frontend/*.g.dart                      # ❌ build_runner 生成的代码
frontend/*.freezed.dart                # ❌ freezed 生成的代码
```

## 其他未跟踪的文件

除了 `lib/` 目录，还有以下文件未被跟踪（需要评估是否应该添加）：

### Backend 相关

```bash
# 新增的功能文件
backend/app/core/prompt_manager.py
backend/app/prompts/                   # 整个 prompts 目录

# 新增的脚本
backend/scripts/demo_*.py
backend/scripts/validate_*.py
backend/scripts/download_bge_model.py

# 新增的测试
backend/tests/test_portfolio_analyzer_refactor.py
backend/tests/test_prompt_manager.py

# 数据库迁移
backend/alembic/versions/2e0176ff710f_merge_heads.py
backend/alembic/versions/add_memory_extraction_tracking.py
```

### 文档相关

```bash
# 新增的文档
docs/Important/AI_*.md
docs/Memory/*.md
docs/PortfolioAnalyzer/*.md
docs/Prompt_Optimize/*.md
docs/OPTIMIZATION_*.md

# 修复总结
docs/fix_summary/utf8_websocket_crash_fix.md
docs/guides/DASHBOARD_*.md
```

### Scripts 相关

```bash
# 新增的测试脚本
scripts/test_*.py
scripts/debug_*.py
scripts/diagnose_*.py
scripts/verify_*.py
scripts/restart_service.sh
```

## 建议的 Git 操作

### 1. 立即添加（高优先级）

```bash
# 前端源代码（必须）
cd frontend
git add lib/

# 核心功能代码（必须）
cd ..
git add backend/app/core/prompt_manager.py
git add backend/app/prompts/

# 数据库迁移（必须）
git add backend/alembic/versions/
```

### 2. 选择性添加（中优先级）

```bash
# 新增的脚本和测试
git add backend/scripts/demo_*.py
git add backend/scripts/validate_*.py
git add backend/tests/test_portfolio_analyzer_refactor.py
git add backend/tests/test_prompt_manager.py

# 重要文档
git add docs/Important/
git add docs/Memory/
git add docs/PortfolioAnalyzer/
git add docs/Prompt_Optimize/
```

### 3. 可选添加（低优先级）

```bash
# 调试和测试脚本（可选）
git add scripts/test_*.py
git add scripts/debug_*.py
git add scripts/verify_*.py

# 临时脚本（可选）
git add scripts/restart_service.sh
```

## 完整的添加命令

```bash
# 1. 修复 .gitignore
git add .gitignore
git commit -m "Fix: Update .gitignore to not ignore Flutter lib directory"

# 2. 添加前端源代码
cd frontend
git add lib/
git commit -m "Add frontend source files (lib directory)"

# 3. 添加后端核心功能
cd ..
git add backend/app/core/prompt_manager.py
git add backend/app/prompts/
git add backend/alembic/versions/
git commit -m "Add backend prompt system and migrations"

# 4. 添加新增的脚本和测试
git add backend/scripts/demo_*.py
git add backend/scripts/validate_*.py
git add backend/scripts/download_bge_model.py
git add backend/tests/test_portfolio_analyzer_refactor.py
git add backend/tests/test_prompt_manager.py
git commit -m "Add new scripts and tests"

# 5. 添加文档
git add docs/Important/
git add docs/Memory/
git add docs/PortfolioAnalyzer/
git add docs/Prompt_Optimize/
git add docs/OPTIMIZATION_*.md
git add docs/fix_summary/
git add docs/guides/DASHBOARD_*.md
git commit -m "Add documentation for new features and fixes"

# 6. 添加调试脚本（可选）
git add scripts/
git commit -m "Add debug and test scripts"

# 7. 推送所有更改
git push
```

## 注意事项

### 1. 检查敏感信息

在添加文件前，确保没有敏感信息：

```bash
# 检查是否有 API keys
grep -r "sk-" backend/ frontend/ scripts/ --include="*.py" --include="*.dart"

# 检查是否有密码
grep -r "password" backend/ frontend/ scripts/ --include="*.py" --include="*.dart" | grep -v "# "
```

### 2. 检查大文件

```bash
# 查找大于 1MB 的文件
find . -type f -size +1M | grep -v ".git" | grep -v "node_modules" | grep -v ".dart_tool"
```

### 3. 验证 .gitignore

```bash
# 确保生成的文件被忽略
git check-ignore -v frontend/lib/generated/api/test/risk_level_test.dart
git check-ignore -v backend/__pycache__/
git check-ignore -v backend/.venv/
```

## 总结

### 问题
- 根目录 `.gitignore` 中的 `lib/` 规则误伤了 Flutter 项目
- 前端所有源代码（112 个文件）未被 Git 跟踪

### 解决
- 修改 `.gitignore`，使用路径前缀限定 Python lib 目录
- 添加前端 `lib/` 目录到 Git

### 影响
- ✅ Flutter 源代码现在可以被正确跟踪
- ✅ Python lib 目录仍然被正确忽略
- ✅ 生成的文件（`lib/generated/`）仍然被正确忽略

### 后续
- 提交所有未跟踪的重要文件
- 推送到远程仓库
- 确保团队成员同步更新
