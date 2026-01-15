# AssetFlow 局域网访问快速启动指南

**目标**: 在局域网内访问 AssetFlow 应用

---

## 🚀 快速启动 (3步)

### 步骤1: 启动后端服务

```bash
cd backend
bash ../scripts/start_backend_lan.sh
```

**预期输出**:
```
🚀 启动 AssetFlow 后端服务 (局域网访问)
==========================================
📍 本机IP地址: 10.36.234.5
🌐 访问地址:
  - 本地: http://localhost:8000
  - 局域网: http://10.36.234.5:8000
  - API文档: http://10.36.234.5:8000/docs
```

### 步骤2: 启动前端服务

**新开一个终端窗口**:

```bash
cd frontend
bash ../scripts/start_frontend_lan.sh
```

**预期输出**:
```
🚀 启动 AssetFlow 前端服务 (局域网访问)
==========================================
📍 本机IP地址: 10.36.234.5
🌐 访问地址:
  - 本地: http://localhost:8080/#/login
  - 局域网: http://10.36.234.5:8080/#/login
```

### 步骤3: 访问应用

**在同一局域网的任何设备上**:

- 打开浏览器
- 访问: `http://10.36.234.5:8080/#/login`
- 应该能看到登录页面（不再白屏）

---

## 🔍 问题排查

### 如果仍然白屏

运行诊断脚本:

```bash
python scripts/diagnose_lan_access.py
```

查看输出，根据提示修复问题。

### 常见问题

**1. 后端无法访问**
```bash
# 测试后端
curl http://10.36.234.5:8000/health

# 如果失败，检查防火墙设置
```

**2. CORS错误**
```bash
# 编辑 backend/.env
# 添加你的局域网IP
BACKEND_CORS_ORIGINS=http://localhost:8080,http://10.36.234.5:8080

# 重启后端服务
```

**3. 前端无法启动**
```bash
# 检查端口占用
lsof -i :8080

# 杀死占用进程
kill -9 [PID]
```

---

## 📱 移动设备访问

### iOS/Android

1. 确保移动设备连接到同一WiFi
2. 在移动浏览器中访问: `http://10.36.234.5:8080/#/login`
3. 如果是iOS，可能需要添加到主屏幕以获得更好的体验

### 添加到主屏幕 (iOS)

1. 在Safari中打开应用
2. 点击分享按钮
3. 选择"添加到主屏幕"
4. 应用将像原生App一样运行

---

## 🛠️ 高级配置

### 自定义端口

**后端**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

**前端**:
```bash
flutter run -d chrome --web-port=9080 --web-hostname=0.0.0.0
```

**注意**: 修改端口后需要更新CORS配置

### 使用环境变量

创建 `backend/.env`:
```env
# 你的局域网IP
LOCAL_IP=10.36.234.5

# CORS配置
BACKEND_CORS_ORIGINS=http://localhost:8080,http://${LOCAL_IP}:8080

# 数据库
DATABASE_URL=sqlite:///./assetflow.db

# OpenAI (可选)
OPENAI_API_KEY=your-key-here
```

---

## 📊 性能优化

### 生产模式构建

**前端**:
```bash
cd frontend
flutter build web --release
```

构建后的文件在 `frontend/build/web/`，可以使用任何Web服务器托管。

**后端**:
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🔒 安全建议

1. **仅在可信网络使用**: 局域网访问适合开发和内部使用
2. **生产环境**: 使用HTTPS和适当的认证
3. **防火墙**: 限制端口访问范围
4. **CORS**: 只允许必要的源

---

## 📚 更多信息

- [完整修复文档](docs/LAN_ACCESS_FIX.md)
- [前端README](frontend/README.md)
- [后端README](backend/README.md)

---

**快速启动完成！** 🎉

如有问题，请查看 [LAN_ACCESS_FIX.md](docs/LAN_ACCESS_FIX.md) 获取详细排查步骤。
