# 前端WebSocket连接问题修复指南

## 问题描述
聊天页面显示"连接中"状态，WebSocket无法成功连接到后端。

## 问题原因
前端存储的token可能已过期或无效，导致WebSocket认证失败。

## 解决方案

### 方案1：通过浏览器开发者工具更新token（推荐）

1. 打开浏览器开发者工具（F12）
2. 切换到Console标签页
3. 执行以下代码更新token：

```javascript
// 清除旧的认证数据
localStorage.clear();

// 设置新的token
localStorage.setItem('flutter.auth_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5IiwiZXhwIjoxNzY4NjYwOTc2LCJpYXQiOjE3Njc5Njk3NzYsInR5cGUiOiJhY2Nlc3MiLCJqdGkiOiIxNzY3OTQwOTc2LjgwMTU0NyJ9.jyu-3c5lBzt6NyEoHFnEvw5Z7NrSed2Ga2oR3zb2pJ0');

// 设置用户信息
localStorage.setItem('flutter.auth_user', '{"id":9,"phone":"18602552212","device_id":null,"created_at":"2026-01-09T02:11:48.932158"}');

console.log('Token已更新，请刷新页面');
```

4. 刷新页面（Ctrl+R 或 Cmd+R）

### 方案2：重新登录

1. 点击退出登录
2. 重新使用手机号 `18602552212` 登录
3. 输入验证码（开发环境下任意6位数字都可以）

### 方案3：检查后端服务

如果上述方案都不行，检查后端服务是否正常运行：

```bash
# 检查后端健康状态
curl http://localhost:8000/api/v1/health/

# 应该返回：{"status":"healthy","service":"AssetFlow API"}
```

## 验证修复

修复后，聊天页面应该：
1. 显示"已连接到AI助手"的提示
2. 收到AI的欢迎消息
3. 能够正常发送和接收消息

## 技术细节

- 新token有效期：7天
- 用户ID：9
- 手机号：18602552212
- WebSocket端点：ws://localhost:8000/api/v1/chat/ws/chat/9

## 如果问题仍然存在

请检查：
1. 后端服务是否在端口8000运行
2. 浏览器控制台是否有其他错误信息
3. 网络连接是否正常