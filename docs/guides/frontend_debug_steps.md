# 前端连接调试步骤

## 问题现象
登录成功后，聊天页面显示"未连接"状态。

## 调试步骤

### 1. 检查浏览器控制台
1. 打开 http://localhost:8080
2. 按 F12 打开开发者工具
3. 点击 Console 标签页
4. 登录（手机号：13800138000，验证码：123456）
5. 导航到聊天页面
6. 查看控制台输出，应该看到：

**期望的调试信息：**
```
🔐 开始登录: 13800138000
🗑️ 已清除旧的认证信息
📡 登录响应状态码: 200
📡 登录响应数据: {access_token: "...", user_id: 28, phone: "13800138000"}
👤 创建用户对象: ...
🔑 新Token已存储
✅ 登录状态已更新
🔍 验证: 当前token前缀: eyJhbGciOiJIUzI1NiIsInR5...

🔍 Chat page loaded - Auth check:
   Auth state: 13800138000
   Token: eyJhbGciOiJIUzI1NiIsInR5...
🔌 Initial WebSocket connection needed
🔌 Connecting WebSocket for user 28 with token eyJhbGciOiJIUzI1NiIsInR5...
🚀 Attempting WebSocket connection...
🔌 连接WebSocket: ws://localhost:8000/api/v1/chat/ws/chat/28?token=...
🔗 WebSocket state changed to: connected
✅ WebSocket connection initiated
```

### 2. 检查网络连接
1. 在开发者工具中点击 Network 标签页
2. 过滤器选择 "WS" (WebSocket)
3. 导航到聊天页面
4. 应该看到 WebSocket 连接请求

### 3. 常见问题排查

#### 问题1：没有看到任何调试信息
**可能原因：** 前端代码没有更新
**解决方案：** 
- 刷新页面 (Ctrl+F5 或 Cmd+Shift+R)
- 或重启 Flutter 应用

#### 问题2：看到 "Auth state: null" 或 "Token: null"
**可能原因：** 登录状态没有正确保存
**解决方案：**
- 重新登录
- 检查登录过程中是否有错误信息

#### 问题3：看到 WebSocket 连接错误
**可能原因：** 后端连接问题
**解决方案：**
- 确认后端运行在 http://localhost:8000
- 检查后端日志是否有错误

#### 问题4：WebSocket 连接成功但显示"未连接"
**可能原因：** 前端状态更新问题
**解决方案：**
- 查看是否有 "🔗 WebSocket state changed to: connected" 消息
- 检查是否有 JavaScript 错误

### 4. 手动测试 WebSocket 连接
如果前端连接失败，可以使用以下 Python 脚本测试：

```bash
python3 debug_frontend_connection.py
```

这会显示：
- 后端状态
- 新的登录token
- WebSocket URL
- 预期的用户信息

### 5. 强制重新连接
如果连接仍然失败，在浏览器控制台中运行：

```javascript
// 强制刷新页面状态
location.reload();
```

## 预期结果
修复后应该看到：
1. 登录成功后立即显示连接调试信息
2. WebSocket 连接成功
3. 聊天页面显示"已连接"状态
4. 可以发送消息并收到 AI 回复

## 如果问题仍然存在
请提供：
1. 浏览器控制台的完整输出
2. Network 标签页中的 WebSocket 连接状态
3. 任何错误信息的截图