# 🚨 局域网白屏 - 立即修复指南

## ✅ 根本原因已找到

**问题**: 后端CORS配置未生效（服务未重启）  
**解决**: 重启后端服务

---

## 🎯 立即执行（3步）

### 1️⃣ 启动后端（终端1）

```bash
cd backend
bash ../scripts/start_backend_lan.sh
```

等待看到：
```
✅ 后端服务启动成功
📱 局域网访问: http://10.36.234.5:8000
```

### 2️⃣ 启动前端（终端2）

```bash
cd frontend
bash ../scripts/start_frontend_lan.sh
```

等待看到：
```
✅ 前端服务启动成功
📱 局域网访问: http://10.36.234.5:8080/#/login
```

### 3️⃣ 访问并刷新

1. 打开浏览器访问: `http://10.36.234.5:8080/#/login`
2. 按 `Cmd+Shift+R` (Mac) 或 `Ctrl+Shift+R` (Windows) 强制刷新
3. 应该看到登录页面（不再白屏）

---

## 🧪 验证修复

```bash
bash scripts/test_cors.sh
```

**预期结果**:
```
1️⃣ 测试 localhost origin
HTTP/1.1 200 OK ✅

2️⃣ 测试局域网IP origin
HTTP/1.1 200 OK ✅  ← 应该是200，不是400
```

---

## 📚 详细文档

- [WHITE_SCREEN_ROOT_CAUSE.md](WHITE_SCREEN_ROOT_CAUSE.md) - 根本原因分析
- [WHITE_SCREEN_FIX_FINAL.md](WHITE_SCREEN_FIX_FINAL.md) - 完整修复方案
- [QUICK_FIX_REFERENCE.md](QUICK_FIX_REFERENCE.md) - 快速参考

---

**修复状态**: ✅ 所有代码已修复  
**待执行**: 重启服务  
**预计时间**: 2分钟
