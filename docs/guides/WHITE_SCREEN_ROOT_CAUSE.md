# 局域网访问白屏问题 - 根本原因分析 🎯

**诊断时间**: 2026年1月15日  
**状态**: ✅ 根本原因已找到

---

## 🔍 根本原因

通过深度诊断发现，白屏问题的根本原因是：

### **CORS配置未生效** ❌

后端服务返回：`Disallowed CORS origin`

**原因分析**:
1. ✅ `.env` 文件已正确配置（包含局域网IP）
2. ✅ `config.py` 代码正确读取配置
3. ❌ **后端服务在配置更新前就已启动**
4. ❌ 后端服务没有重启，仍使用旧配置

---

## 🧪 诊断证据

### 测试1: localhost CORS ✅
```bash
curl -H "Origin: http://localhost:8080" http://localhost:8000/api/v1/health/
# 结果: HTTP 200 OK
# Access-Control-Allow-Origin: http://localhost:8080
```

### 测试2: 局域网IP CORS ❌
```bash
curl -H "Origin: http://10.36.234.5:8080" http://10.36.234.5:8000/api/v1/health/
# 结果: HTTP 400 Bad Request
# Disallowed CORS origin
```

### 配置文件检查 ✅
```bash
$ grep BACKEND_CORS_ORIGINS backend/.env
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:8081,http://10.36.234.5:8080,http://10.36.234.5:3000
```

**结论**: 配置文件正确，但后端服务未重启，仍使用旧配置。

---

## 🔧 完整修复方案

### 已完成的修复 ✅

1. **前端动态API配置**
   - ✅ `frontend/lib/core/api/api_client.dart` - 添加 `_getApiBaseUrl()`
   - ✅ `frontend/lib/core/services/api_service.dart` - 已有动态配置
   - ✅ `frontend/lib/core/services/websocket_service.dart` - 添加 `_getWebSocketUrl()`

2. **后端CORS配置**
   - ✅ `backend/.env` - 添加局域网IP到CORS白名单
   - ✅ `backend/app/core/config.py` - 配置读取逻辑正确

3. **Flutter代码生成**
   - ✅ 重新运行 `build_runner` 生成最新代码

### 待执行的关键步骤 ⚠️

**必须重启后端服务以加载新的CORS配置！**

---

## 📋 用户操作步骤

### 步骤1: 停止所有服务

后端服务已停止。如果前端还在运行，请停止它。

### 步骤2: 启动后端（终端1）

```bash
cd backend
bash ../scripts/start_backend_lan.sh
```

**验证**: 看到以下输出表示成功
```
🚀 启动 AssetFlow 后端服务（局域网模式）
📍 本机IP: 10.36.234.5
🌐 后端将监听: 0.0.0.0:8000
```

### 步骤3: 启动前端（终端2）

```bash
cd frontend
bash ../scripts/start_frontend_lan.sh
```

**验证**: 看到以下输出表示成功
```
🚀 启动 AssetFlow 前端服务（局域网模式）
📍 本机IP: 10.36.234.5
🌐 前端将监听: 0.0.0.0:8080
```

### 步骤4: 访问应用

在浏览器中访问：
```
http://10.36.234.5:8080/#/login
```

**重要**: 首次访问按 `Cmd+Shift+R` 强制刷新！

### 步骤5: 验证修复

打开浏览器开发者工具 (F12)，检查：

1. **Console标签**: 应该没有CORS错误
2. **Network标签**: 
   - API请求地址应该是 `http://10.36.234.5:8000`
   - 请求状态应该是 200 OK
   - 响应头应该包含 `Access-Control-Allow-Origin: http://10.36.234.5:8080`

---

## 🎯 问题时间线

| 时间 | 事件 | 状态 |
|------|------|------|
| 初始 | 用户报告局域网访问白屏 | ❌ |
| 第1轮修复 | 添加动态API配置 | ⚠️ 不完整 |
| 第2轮修复 | 更新CORS配置 | ⚠️ 未重启 |
| 第3轮修复 | 重新生成Flutter代码 | ⚠️ 未重启 |
| **诊断** | **发现CORS配置未生效** | **🔍 根因** |
| **第4轮修复** | **重启后端服务** | **✅ 应该解决** |

---

## 🧪 验证清单

启动服务后，运行以下测试：

### 自动测试
```bash
bash scripts/test_cors.sh
```

**预期结果**:
```
1️⃣ 测试 localhost origin
HTTP/1.1 200 OK
access-control-allow-origin: http://localhost:8080

2️⃣ 测试局域网IP origin
HTTP/1.1 200 OK  ← 应该是200，不是400
access-control-allow-origin: http://10.36.234.5:8080  ← 应该有这个
```

### 手动测试
- [ ] 后端服务启动成功
- [ ] 前端服务启动成功
- [ ] 浏览器访问不再白屏
- [ ] 登录页面正常显示
- [ ] Console无CORS错误
- [ ] Network请求成功

---

## 📊 技术细节

### CORS工作原理

1. **浏览器发送预检请求** (OPTIONS)
   ```
   Origin: http://10.36.234.5:8080
   Access-Control-Request-Method: GET
   ```

2. **后端检查CORS配置**
   ```python
   allow_origins=settings.get_cors_origins()
   # 从 .env 读取: BACKEND_CORS_ORIGINS
   ```

3. **后端返回CORS头**
   ```
   Access-Control-Allow-Origin: http://10.36.234.5:8080
   Access-Control-Allow-Methods: *
   Access-Control-Allow-Headers: *
   ```

4. **浏览器允许实际请求**

### 问题所在

后端服务启动时读取`.env`文件并缓存配置。修改`.env`后，如果不重启服务，新配置不会生效。

---

## 🎓 经验教训

### 1. 配置更新必须重启服务
- ❌ 修改`.env`文件
- ❌ 期望自动生效
- ✅ 必须重启服务

### 2. 诊断要全面
- ✅ 检查配置文件
- ✅ 检查代码逻辑
- ✅ **检查运行时状态** ← 关键

### 3. CORS错误的表现
- 浏览器白屏
- Console可能没有明显错误
- Network标签显示请求失败
- 需要检查OPTIONS预检请求

---

## 🚀 快速命令参考

### 一键重启服务
```bash
bash scripts/restart_services_lan.sh
```

### 测试CORS
```bash
bash scripts/test_cors.sh
```

### 深度诊断
```bash
bash scripts/deep_diagnose_white_screen.sh
```

### 最终验证
```bash
bash scripts/final_check.sh
```

---

## 📞 如果问题仍然存在

### 检查1: CORS测试
```bash
bash scripts/test_cors.sh
```
如果仍然返回 `Disallowed CORS origin`，说明后端配置有问题。

### 检查2: 后端日志
查看后端终端输出，确认：
- 服务启动时间（应该是最近）
- 没有配置读取错误
- 监听地址是 `0.0.0.0:8000`

### 检查3: 环境变量
```bash
cd backend
source .venv/bin/activate
python -c "from app.core.config import settings; print(settings.get_cors_origins())"
```
应该输出包含局域网IP的列表。

### 检查4: 浏览器
- 清除所有缓存
- 使用隐私/无痕模式
- 尝试不同浏览器

---

**根本原因**: CORS配置未生效（服务未重启）  
**解决方案**: 重启后端服务  
**预期结果**: 白屏问题解决

---

**文档创建时间**: 2026-01-15  
**最后更新**: 2026-01-15  
**状态**: 待用户验证
