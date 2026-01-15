# 局域网访问白屏 - 快速修复参考 🚀

## ✅ 已完成的修复

1. **更新CORS配置** - `backend/.env` 已包含局域网IP
2. **重新生成Flutter代码** - `api_service.g.dart` 已更新

---

## 🎯 启动服务（3步）

### 1️⃣ 启动后端（终端1）
```bash
cd backend
bash ../scripts/start_backend_lan.sh
```

### 2️⃣ 启动前端（终端2）
```bash
cd frontend
bash ../scripts/start_frontend_lan.sh
```

### 3️⃣ 访问应用
```
http://10.36.234.5:8080/#/login
```

**重要**: 首次访问按 `Cmd+Shift+R` 强制刷新！

---

## 🔍 快速诊断

```bash
bash scripts/debug_white_screen.sh
```

---

## 📱 访问地址

- **本地**: http://localhost:8080/#/login
- **局域网**: http://10.36.234.5:8080/#/login
- **后端API**: http://10.36.234.5:8000

---

## 🆘 问题排查

### 白屏 + 无错误
→ 按 `Cmd+Shift+R` 强制刷新

### CORS错误
→ 检查 `backend/.env` 是否包含局域网IP

### API请求失败
→ 检查后端服务是否启动在 `0.0.0.0:8000`

### 前端无法访问
→ 检查前端服务是否启动在 `0.0.0.0:8080`

---

## 📞 获取帮助

查看详细文档：
- [WHITE_SCREEN_FIX_FINAL.md](WHITE_SCREEN_FIX_FINAL.md) - 完整修复方案
- [LAN_ACCESS_FIX_COMPLETE.md](LAN_ACCESS_FIX_COMPLETE.md) - 技术文档

运行诊断工具：
```bash
bash scripts/debug_white_screen.sh
bash scripts/verify_lan_fix.sh
```

---

**修复状态**: ✅ 完成  
**当前IP**: 10.36.234.5  
**更新时间**: 2026-01-15
