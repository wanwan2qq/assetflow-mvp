# AssetFlow 启动指南 - 解决依赖问题

**问题**: 使用系统Python导致 `ModuleNotFoundError: No module named 'sqlmodel'`  
**解决**: 必须在虚拟环境中运行

---

## ✅ 正确的启动方式

### 步骤1: 检查环境

```bash
cd backend
bash ../scripts/check_backend_env.sh
```

**预期输出**:
```
✅ 虚拟环境存在: .venv/
✅ sqlmodel: 0.0.31
✅ fastapi: 0.128.0
✅ uvicorn: 0.40.0
✅ 所有关键依赖已安装，可以启动服务
```

### 步骤2: 启动后端（使用脚本）

```bash
cd backend
bash ../scripts/start_backend_lan.sh
```

脚本会自动：
1. 检测虚拟环境
2. 激活虚拟环境
3. 检查依赖
4. 启动服务

### 步骤3: 启动前端

**新开终端**:
```bash
cd frontend
flutter run -d chrome --web-port=8080 --web-hostname=0.0.0.0
```

---

## 🔧 手动启动（如果脚本失败）

### 后端

```bash
# 1. 进入backend目录
cd backend

# 2. 激活虚拟环境（重要！）
source .venv/bin/activate

# 3. 验证Python路径
which python
# 应该显示: /path/to/backend/.venv/bin/python

# 4. 验证依赖
python -c "import sqlmodel; print('OK')"

# 5. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```bash
cd frontend
flutter run -d chrome --web-port=8080 --web-hostname=0.0.0.0
```

---

## ❌ 错误原因分析

### 你遇到的错误

```
ModuleNotFoundError: No module named 'sqlmodel'
```

**原因**: 
- 使用了系统Python (`/Applications/Xcode.app/.../Python3.framework/...`)
- 而不是项目虚拟环境 (`backend/.venv/bin/python`)

**Python路径对比**:
```
❌ 错误: /Applications/Xcode.app/.../python3.9
✅ 正确: /path/to/backend/.venv/bin/python (3.11.14)
```

---

## 🔍 诊断步骤

### 1. 检查当前Python

```bash
which python
python --version
```

### 2. 检查是否在虚拟环境中

```bash
echo $VIRTUAL_ENV
# 应该显示: /path/to/backend/.venv
```

### 3. 检查依赖是否安装

```bash
python -c "import sqlmodel"
# 如果报错，说明不在虚拟环境或依赖未安装
```

---

## 🛠️ 修复方案

### 方案1: 使用修复后的启动脚本

```bash
cd backend
bash ../scripts/start_backend_lan.sh
```

脚本已更新，会自动激活虚拟环境。

### 方案2: 手动激活虚拟环境

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 方案3: 重新创建虚拟环境（如果损坏）

```bash
cd backend

# 删除旧虚拟环境
rm -rf .venv

# 创建新虚拟环境
python3 -m venv .venv

# 激活
source .venv/bin/activate

# 安装依赖
pip install -e .

# 启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📋 完整启动检查清单

- [ ] 在 `backend` 目录下
- [ ] 虚拟环境存在 (`.venv/`)
- [ ] 虚拟环境已激活 (`source .venv/bin/activate`)
- [ ] Python路径正确 (`which python` 显示 `.venv/bin/python`)
- [ ] 依赖已安装 (`python -c "import sqlmodel"` 不报错)
- [ ] 配置文件存在 (`.env` 或使用默认配置)
- [ ] 端口未被占用 (`lsof -i :8000` 无输出)

---

## 🌐 验证服务

### 后端验证

```bash
# 方法1: curl
curl http://localhost:8000/health

# 方法2: 浏览器
open http://localhost:8000/docs
```

**预期响应**:
```json
{"status": "healthy"}
```

### 前端验证

```bash
open http://localhost:8080/#/login
```

**预期**: 看到登录页面

---

## 💡 最佳实践

### 1. 始终使用虚拟环境

```bash
# 每次启动前
cd backend
source .venv/bin/activate
```

### 2. 使用启动脚本

```bash
# 脚本会自动处理虚拟环境
bash ../scripts/start_backend_lan.sh
```

### 3. 定期更新依赖

```bash
cd backend
source .venv/bin/activate
pip install --upgrade -e .
```

---

## 🆘 仍然有问题？

### 运行完整诊断

```bash
# 检查后端环境
cd backend && bash ../scripts/check_backend_env.sh

# 检查局域网访问
python scripts/diagnose_lan_access.py
```

### 查看日志

```bash
# 启动时添加详细日志
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### 联系支持

查看详细文档：
- [START_SERVICES.md](START_SERVICES.md) - 服务启动指南
- [LAN_ACCESS_FIX.md](docs/LAN_ACCESS_FIX.md) - 局域网访问修复
- [backend/README.md](backend/README.md) - 后端文档

---

## ✅ 成功标志

启动成功后，你会看到：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

然后可以访问：
- 本地: http://localhost:8000
- 局域网: http://10.36.234.5:8000
- API文档: http://localhost:8000/docs

---

**问题已解决！** 🎉

记住：**始终在虚拟环境中运行后端服务**
