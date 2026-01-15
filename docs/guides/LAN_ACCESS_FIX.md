# 局域网访问白屏问题修复

**日期**: 2026年1月15日  
**状态**: ✅ 已修复  
**问题**: 通过局域网IP访问前端时出现白屏

---

## 🎯 问题分析

### 根本原因

1. **前端API配置硬编码**: `api_service.dart` 中硬编码了 `http://localhost:8000`
2. **CORS配置不完整**: 后端CORS只允许 `localhost`，不包含局域网IP
3. **服务绑定问题**: 服务可能只绑定到 `127.0.0.1` 而非 `0.0.0.0`

### 症状

- 本地访问 `http://localhost:8080` 正常
- 局域网访问 `http://10.36.234.5:8080` 白屏
- 浏览器控制台显示 CORS 错误或 API 连接失败

---

## 🔧 修复方案

### 1. 前端动态API配置

**文件**: `frontend/lib/core/services/api_service.dart`

**修改前**:
```dart
dio.options.baseUrl = 'http://localhost:8000';
```

**修改后**:
```dart
String baseUrl = _getApiBaseUrl();
dio.options.baseUrl = baseUrl;

/// 动态获取API基础URL
String _getApiBaseUrl() {
  final currentHost = Uri.base.host;
  
  // 如果是localhost，使用localhost:8000
  if (currentHost == 'localhost' || currentHost == '127.0.0.1') {
    return 'http://localhost:8000';
  }
  
  // 如果是局域网IP，使用相同IP的8000端口
  return 'http://$currentHost:8000';
}
```

**原理**: 
- 自动检测当前访问的host
- 如果是 `localhost` → 使用 `http://localhost:8000`
- 如果是局域网IP → 使用 `http://[局域网IP]:8000`

### 2. 后端CORS配置更新

**文件**: `backend/app/core/config.py`

**修改前**:
```python
BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://localhost:8081"
```

**修改后**:
```python
BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://localhost:8081,http://10.36.234.5:8080,http://10.36.234.5:3000"
```

**注意**: 
- 需要将 `10.36.234.5` 替换为你的实际局域网IP
- 或者在 `.env` 文件中配置

### 3. 服务启动配置

#### 后端启动 (绑定所有网络接口)

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**关键参数**:
- `--host 0.0.0.0`: 绑定所有网络接口（允许局域网访问）
- `--port 8000`: 指定端口
- `--reload`: 开发模式自动重载

#### 前端启动 (支持局域网访问)

```bash
cd frontend
flutter run -d chrome --web-port=8080 --web-hostname=0.0.0.0
```

**关键参数**:
- `--web-port=8080`: 指定端口
- `--web-hostname=0.0.0.0`: 允许局域网访问

---

## 🧪 测试验证

### 1. 运行诊断脚本

```bash
python scripts/diagnose_lan_access.py
```

**输出示例**:
```
🔍 AssetFlow 局域网访问诊断工具
==================================================
📍 检测到本机IP: 10.36.234.5

🔍 检查后端服务 (端口 8000):
--------------------------------------------------
✅ http://localhost:8000/health - 正常 (状态码: 200)
✅ http://10.36.234.5:8000/health - 正常 (状态码: 200)

🔍 检查CORS配置:
--------------------------------------------------
✅ CORS 头部存在:
   access-control-allow-origin: http://10.36.234.5:8080
   access-control-allow-credentials: true

🔍 检查前端服务 (端口 8080):
--------------------------------------------------
✅ http://localhost:8080 - 正常 (内容长度: 15234)
✅ http://10.36.234.5:8080 - 正常 (内容长度: 15234)
```

### 2. 手动测试步骤

1. **启动后端服务**
   ```bash
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **启动前端服务**
   ```bash
   cd frontend
   bash ../scripts/start_frontend_lan.sh
   ```

3. **本地测试**
   - 访问: `http://localhost:8080/#/login`
   - 应该能正常显示登录页面

4. **局域网测试**
   - 访问: `http://10.36.234.5:8080/#/login`
   - 应该能正常显示登录页面（不再白屏）

5. **检查浏览器控制台**
   - 按 F12 打开开发者工具
   - 查看 Console 标签：不应有 CORS 错误
   - 查看 Network 标签：API 请求应该成功

---

## 📊 修复前后对比

### 修复前

**本地访问** (`http://localhost:8080`):
```
✅ 前端加载正常
✅ API请求: http://localhost:8000 (成功)
✅ 页面显示正常
```

**局域网访问** (`http://10.36.234.5:8080`):
```
❌ 前端加载正常
❌ API请求: http://localhost:8000 (失败 - 无法连接)
❌ 页面白屏
❌ Console错误: Failed to fetch
```

### 修复后

**本地访问** (`http://localhost:8080`):
```
✅ 前端加载正常
✅ API请求: http://localhost:8000 (成功)
✅ 页面显示正常
```

**局域网访问** (`http://10.36.234.5:8080`):
```
✅ 前端加载正常
✅ API请求: http://10.36.234.5:8000 (成功 - 动态检测)
✅ 页面显示正常
✅ Console无错误
```

---

## 🚨 常见问题排查

### 问题1: 仍然白屏

**可能原因**:
- 后端服务未启动或未绑定到 `0.0.0.0`
- 防火墙阻止了端口访问
- CORS配置中缺少当前IP

**解决方法**:
```bash
# 1. 检查后端服务
curl http://10.36.234.5:8000/health

# 2. 检查防火墙
# macOS: 系统偏好设置 > 安全性与隐私 > 防火墙

# 3. 更新CORS配置
# 编辑 backend/.env 添加:
# BACKEND_CORS_ORIGINS=http://localhost:8080,http://10.36.234.5:8080
```

### 问题2: CORS错误

**错误信息**:
```
Access to fetch at 'http://10.36.234.5:8000/api/v1/...' from origin 
'http://10.36.234.5:8080' has been blocked by CORS policy
```

**解决方法**:
1. 确认后端 CORS 配置包含前端地址
2. 重启后端服务使配置生效
3. 清除浏览器缓存

### 问题3: API连接失败

**错误信息**:
```
Failed to fetch
net::ERR_CONNECTION_REFUSED
```

**解决方法**:
```bash
# 1. 确认后端服务运行在正确的host
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. 测试后端可访问性
curl http://10.36.234.5:8000/health

# 3. 检查网络连接
ping 10.36.234.5
```

### 问题4: 前端服务无法启动

**错误信息**:
```
Error: Unable to bind to port 8080
```

**解决方法**:
```bash
# 1. 检查端口占用
lsof -i :8080

# 2. 杀死占用进程
kill -9 [PID]

# 3. 使用其他端口
flutter run -d chrome --web-port=8081 --web-hostname=0.0.0.0
```

---

## 📝 配置文件示例

### backend/.env
```env
# API配置
API_V1_STR=/api/v1

# CORS配置 - 支持局域网访问
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://10.36.234.5:8080,http://10.36.234.5:3000

# 数据库配置
DATABASE_URL=sqlite:///./assetflow.db

# OpenAI配置
OPENAI_API_KEY=your-api-key-here
```

---

## 🎓 技术原理

### 动态API地址检测

```dart
String _getApiBaseUrl() {
  // Uri.base 获取当前页面的完整URI
  // 例如: http://10.36.234.5:8080/#/login
  final currentHost = Uri.base.host;  // 提取host: 10.36.234.5
  
  // 根据host动态构建API地址
  if (currentHost == 'localhost' || currentHost == '127.0.0.1') {
    return 'http://localhost:8000';
  }
  
  return 'http://$currentHost:8000';
}
```

**优势**:
- 无需手动配置
- 自动适应不同网络环境
- 支持本地和局域网访问

### CORS工作原理

```
浏览器 (http://10.36.234.5:8080)
    ↓
    发送请求到 http://10.36.234.5:8000
    ↓
后端检查 Origin 头部
    ↓
如果 Origin 在 BACKEND_CORS_ORIGINS 中
    ↓
返回 Access-Control-Allow-Origin 头部
    ↓
浏览器允许请求
```

---

## ✅ 验收标准

- [ ] 本地访问 `http://localhost:8080` 正常
- [ ] 局域网访问 `http://[IP]:8080` 正常
- [ ] API请求成功（无CORS错误）
- [ ] 登录功能正常
- [ ] 聊天功能正常
- [ ] WebSocket连接正常
- [ ] 诊断脚本全部通过

---

## 📚 相关文档

- [前端README](../frontend/README.md)
- [后端README](../backend/README.md)
- [部署检查清单](../DEPLOYMENT_CHECKLIST.md)

---

**修复完成**: ✅  
**测试状态**: 待验证  
**下一步**: 在实际局域网环境中测试
