# Git 操作指南

本文档提供了在 AssetFlow 项目中使用 Git 的完整指南，包括日常开发工作流程和最佳实践。

## 目录

1. [基础配置](#基础配置)
2. [日常工作流程](#日常工作流程)
3. [分支管理](#分支管理)
4. [提交规范](#提交规范)
5. [常用命令](#常用命令)
6. [问题解决](#问题解决)
7. [团队协作](#团队协作)

## 基础配置

### 初始设置

```bash
# 设置用户信息
git config --global user.name "你的姓名"
git config --global user.email "your.email@example.com"

# 设置默认编辑器
git config --global core.editor "code --wait"

# 设置默认分支名
git config --global init.defaultBranch main

# 启用颜色输出
git config --global color.ui auto
```

### 项目克隆

```bash
# 克隆项目
git clone <repository-url>
cd assetflow

# 查看远程仓库
git remote -v
```

## 日常工作流程

### 1. 开始新功能开发

```bash
# 切换到主分支并更新
git checkout main
git pull origin main

# 创建新的功能分支
git checkout -b feature/your-feature-name

# 或者创建修复分支
git checkout -b fix/bug-description
```

### 2. 开发过程中的提交

```bash
# 查看文件状态
git status

# 添加文件到暂存区
git add .                    # 添加所有文件
git add backend/app/         # 添加特定目录
git add specific-file.py     # 添加特定文件

# 提交更改
git commit -m "feat: UI卡片功能实现，MVP基本功能实现。下一步进行大规模的系统重构，实现完整的家庭资产配置助手能力"

# 推送到远程分支
git push origin feature/your-feature-name
git push origin main
```


### 3. 完成功能开发

```bash
# 确保代码是最新的
git checkout main
git pull origin main
git checkout feature/your-feature-name
git rebase main

# 推送更新后的分支
git push origin feature/your-feature-name --force-with-lease

# 创建 Pull Request (在 GitHub/GitLab 等平台)
```

## 分支管理

### 分支命名规范

```bash
# 功能分支
feature/user-authentication
feature/asset-dashboard
feature/sms-integration

# 修复分支
fix/login-error
fix/websocket-connection
fix/null-safety-issues

# 热修复分支
hotfix/critical-security-patch

# 发布分支
release/v1.0.0
```

### 分支操作

```bash
# 查看所有分支
git branch -a

# 创建并切换分支
git checkout -b new-branch-name

# 切换分支
git checkout branch-name

# 删除本地分支
git branch -d branch-name

# 删除远程分支
git push origin --delete branch-name

# 重命名当前分支
git branch -m new-branch-name
```

## 提交规范

### 提交消息格式

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### 提交类型

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化（不影响功能）
- `refactor`: 代码重构
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动

### 示例

```bash
# 功能提交
git commit -m "feat(auth): 添加JWT令牌验证"

# 修复提交
git commit -m "fix(sms): 修复短信发送失败问题"

# 文档提交
git commit -m "docs: 更新API文档"

# 测试提交
git commit -m "test(frontend): 添加登录页面集成测试"
```

## 常用命令

### 查看历史

```bash
# 查看提交历史
git log --oneline --graph --decorate

# 查看特定文件的历史
git log --follow -- backend/app/services/sms_service.py

# 查看两个分支的差异
git diff main..feature/branch-name

# 查看工作区和暂存区的差异
git diff
git diff --staged
```

### 撤销操作

```bash
# 撤销工作区的更改
git checkout -- file-name
git restore file-name

# 撤销暂存区的更改
git reset HEAD file-name
git restore --staged file-name

# 撤销最后一次提交（保留更改）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃更改）
git reset --hard HEAD~1

# 修改最后一次提交消息
git commit --amend -m "新的提交消息"
```

### 合并和变基

```bash
# 合并分支
git checkout main
git merge feature/branch-name

# 变基操作
git checkout feature/branch-name
git rebase main

# 交互式变基（整理提交历史）
git rebase -i HEAD~3
```

## 问题解决

### 合并冲突

```bash
# 当出现合并冲突时
git status                   # 查看冲突文件
# 手动编辑冲突文件，解决冲突
git add .                    # 标记冲突已解决
git commit                   # 完成合并

# 或者中止合并
git merge --abort
```

### 找回丢失的提交

```bash
# 查看引用日志
git reflog

# 恢复到特定提交
git checkout <commit-hash>
git checkout -b recovery-branch
```

### 清理工作区

```bash
# 清理未跟踪的文件
git clean -f

# 清理未跟踪的文件和目录
git clean -fd

# 预览将要删除的文件
git clean -n
```

## 团队协作

### 同步远程更改

```bash
# 获取远程更新
git fetch origin

# 拉取并合并
git pull origin main

# 推送本地更改
git push origin branch-name
```

### 代码审查流程

1. 创建功能分支
2. 开发并提交代码
3. 推送到远程仓库
4. 创建 Pull Request
5. 代码审查和讨论
6. 修改并更新 PR
7. 合并到主分支

### 标签管理

```bash
# 创建标签
git tag v1.0.0
git tag -a v1.0.0 -m "版本 1.0.0 发布"

# 推送标签
git push origin v1.0.0
git push origin --tags

# 查看标签
git tag -l

# 删除标签
git tag -d v1.0.0
git push origin --delete v1.0.0
```

## 项目特定的 Git 配置

### .gitignore 文件

项目已配置了 `.gitignore` 文件，包含以下忽略规则：

- 环境变量文件 (`.env`)
- 依赖目录 (`node_modules/`, `.venv/`)
- 构建输出 (`build/`, `dist/`)
- IDE 配置文件
- 临时文件和缓存

### 预提交钩子建议

```bash
# 安装 pre-commit (可选)
pip install pre-commit

# 在项目根目录创建 .pre-commit-config.yaml
# 配置代码格式化和检查工具
```

## 最佳实践

1. **频繁提交**: 保持小而频繁的提交
2. **清晰的提交消息**: 使用规范的提交消息格式
3. **分支策略**: 为每个功能或修复创建独立分支
4. **代码审查**: 所有代码都应通过 Pull Request 进行审查
5. **保持同步**: 定期从主分支拉取最新更改
6. **测试**: 提交前确保测试通过
7. **文档**: 及时更新相关文档

## 紧急情况处理

### 回滚生产部署

```bash
# 快速回滚到上一个稳定版本
git checkout main
git reset --hard <last-stable-commit>
git push origin main --force-with-lease

# 或使用 revert（推荐）
git revert <problematic-commit>
git push origin main
```

### 数据恢复

```bash
# 如果意外删除了重要文件
git checkout HEAD -- <deleted-file>

# 如果需要恢复整个目录
git checkout HEAD -- <directory>/
```

---

**注意**: 在执行任何可能影响历史记录的操作（如 `--force` 推送）之前，请确保与团队成员沟通，并备份重要数据。