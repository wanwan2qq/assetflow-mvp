# ⚠️ 需要重启服务

## 问题

你看到的网络访问日志来自**正在运行的旧服务进程**：

```
Connection to huggingface.co timed out
Retrying in 1s [Retry 1/5]
```

## 原因

代码已经修复，但**服务还在运行旧代码**。Python 进程不会自动重新加载已导入的模块。

## 解决方案

### 1. 停止当前服务

找到并停止正在运行的 uvicorn 进程：

```bash
# 方法 1: 如果在终端中运行，按 Ctrl+C

# 方法 2: 查找并杀死进程
ps aux | grep uvicorn
kill <PID>

# 方法 3: 杀死所有 uvicorn 进程
pkill -f uvicorn
```

### 2. 重启服务

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 验证修复

启动后应该看到：

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     MemoryService initialized in OFFLINE mode (using cached BGE model)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**不应该看到**：
```
❌ Connection to huggingface.co timed out
```

### 4. 测试功能

发送一条消息，触发模型加载：

```bash
curl -X POST http://localhost:8000/api/v1/chat/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{"message": "测试消息"}'
```

**预期日志**：
```
INFO:     Loading BGE model in OFFLINE mode (using local cache)
INFO:     ✅ Embedding model loaded successfully: BAAI/bge-large-zh-v1.5
```

## 为什么 --reload 没有自动重启？

`--reload` 只监控文件变化，但有时候：
1. 文件变化发生在启动之前
2. 模块已经被导入，不会重新加载
3. 环境变量的变化不会触发重载

**最可靠的方法**：手动重启服务

## 快速检查清单

- [ ] 停止旧服务进程
- [ ] 确认没有 uvicorn 进程在运行：`ps aux | grep uvicorn`
- [ ] 重新启动服务
- [ ] 检查启动日志，确认 "OFFLINE mode"
- [ ] 发送测试消息
- [ ] 确认没有 "huggingface.co" 的网络访问日志

## 如果还是有网络访问

### 检查 1: 确认代码已更新

```bash
cd backend
head -20 app/services/memory_service.py
```

应该看到：
```python
# CRITICAL: Force offline mode for HuggingFace
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

from langchain_huggingface import HuggingFaceEmbeddings
```

### 检查 2: 确认没有其他进程

```bash
# 查找所有 Python 进程
ps aux | grep python

# 查找所有 uvicorn 进程
ps aux | grep uvicorn

# 杀死所有相关进程
pkill -f "uvicorn app.main:app"
pkill -f "python.*app.main"
```

### 检查 3: 清除 Python 缓存

```bash
cd backend
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

### 检查 4: 重新安装依赖（如果需要）

```bash
cd backend
uv sync --reinstall
```

## 生产环境部署

如果使用 Docker 或其他部署方式：

### Docker
```bash
# 重新构建镜像
docker-compose build backend

# 重启容器
docker-compose restart backend

# 或者完全重新创建
docker-compose down
docker-compose up -d
```

### Systemd
```bash
sudo systemctl restart assetflow-backend
```

### PM2
```bash
pm2 restart assetflow-backend
```

## 总结

**问题**：旧服务进程还在运行旧代码

**解决**：
1. 停止旧进程
2. 重启服务
3. 验证日志

**验证成功标志**：
- ✅ 启动日志显示 "OFFLINE mode"
- ✅ 模型加载日志显示 "✅ Embedding model loaded successfully"
- ✅ 没有 "Connection to huggingface.co" 的错误
