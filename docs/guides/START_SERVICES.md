# AssetFlow 服务启动指南

**快速启动后端和前端服务**

---

## 🚀 方法1: 使用启动脚本（推荐）

### 后端服务

```bash
cd backend
bash ../scripts/start_backend_lan.sh
```

脚本会自动：
- ✅ 检测并激活虚拟环境
- ✅ 安装缺失的依赖
- ✅ 显示访问地址
- ✅ 启动服务

### 前端服务

**新开一个终端窗口**:

```bash
cd frontend
bash ../scripts/start_frontend_lan.sh
```

---

## 🔧 方法2: 手动启动

### 后端服务

```bash
# 1. 进入backend目录
cd backend

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 安装依赖（首次运行）
pip install -e .

# 4. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端服务

```bash
# 1. 进入frontend目录
cd frontend

# 2. 安装依赖（首次运行）
flutter pub get

# 3. 启动服务
flutter run -d chrome --web-port=8080 --web-hostname=0.0.0.0
```

---

## 🌐 访问地址

启动成功后，你会看到类似的输出：

```
📍 本机IP地址: 10.36.234.5

🌐 访问地址:
  - 本地: http://localhost:8080/#/login
  - 局域网: http://10.36.234.5:8080/#/login
```

---

## ❌ 常见错误

### 错误1: ModuleNotFoundError: No module named 'sqlmodel'

**原因**: 未激活虚拟环境或依赖未安装

**解决**:
```bash
cd backend
source .venv/bin/activate  # 激活虚拟环境
pip install -e .            # 安装依赖
```

### 错误2: command not found: uvicorn

**原因**: uvicorn未安装或虚拟环境未激活

**解决**:
```bash
cd backend
source .venv/bin/activate
pip install uvicorn
```

### 错误3: Port 8000 already in use

**原因**: 端口被占用

**解决**:
```bash
# 查找占用进程
lsof -i :8000

# 杀死进程
kill -9 [PID]

# 或使用其他端口
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 错误4: Flutter not found

**原因**: Flutter未安装或未添加到PATH

**解决**:
```bash
# 检查Flutter
flutter --version

# 如果未安装，访问: https://flutter.dev/docs/get-started/install
```

---

## 🔍 验证服务

### 检查后端

```bash
# 方法1: 使用curl
curl http://localhost:8000/health

# 方法2: 浏览器访问
open http://localhost:8000/docs
```

### 检查前端

```bash
# 浏览器访问
open http://localhost:8080/#/login
```

---

## 🛠️ 诊断工具

如果遇到问题，运行诊断脚本：

```bash
python scripts/diagnose_lan_access.py
```

---

## 📝 环境要求

### 后端
- Python 3.9+
- pip
- 虚拟环境 (.venv)

### 前端
- Flutter 3.10+
- Dart 3.0+
- Chrome浏览器

---

## 💡 提示

1. **首次启动**: 需要安装依赖，可能需要几分钟
2. **虚拟环境**: 始终在虚拟环境中运行后端
3. **端口冲突**: 确保8000和8080端口未被占用
4. **网络**: 局域网访问需要在同一WiFi下

---

## 🆘 需要帮助？

查看详细文档：
- [局域网访问修复](docs/LAN_ACCESS_FIX.md)
- [快速启动指南](QUICK_START_LAN.md)
- [后端README](backend/README.md)
- [前端README](frontend/README.md)
