# ⚠️ 重启服务说明

## 当前状态

✅ **代码已修复** - `memory_service.py` 已更新，强制设置离线模式
❌ **服务未重启** - 旧进程还在运行旧代码，仍然尝试访问网络

## 你看到的日志

```
Connection to huggingface.co timed out
Retrying in 1s [Retry 1/5]
```

这些日志来自**正在运行的旧服务进程**，不是新代码产生的。

## 立即解决

### 方法 1: 使用重启脚本（推荐）

```bash
cd backend
./restart_service.sh
```

这个脚本会：
1. 停止旧进程
2. 清除 Python 缓存
3. 验证代码修复
4. 重启服务

### 方法 2: 手动重启

```bash
# 1. 停止旧进程
pkill -f "uvicorn app.main:app"

# 2. 等待进程停止
sleep 2

# 3. 重启服务
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 方法 3: 在终端中按 Ctrl+C

如果服务在终端中运行：
1. 按 `Ctrl+C` 停止
2. 重新运行启动命令

## 验证修复成功

### 启动日志应该显示

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     MemoryService initialized in OFFLINE mode (using cached BGE model)
INFO:     Application startup complete.
```

### 模型加载日志应该显示

```
INFO:     Loading BGE model in OFFLINE mode (using local cache)
INFO:     ✅ Embedding model loaded successfully: BAAI/bge-large-zh-v1.5
```

### 不应该看到

```
❌ Connection to huggingface.co timed out
❌ Retrying in 1s [Retry 1/5]
```

## 为什么需要重启

### Python 模块加载机制

1. **首次导入**：模块被加载到内存
2. **后续导入**：直接使用内存中的模块
3. **文件修改**：不会自动重新加载

### 环境变量设置时机

```python
# memory_service.py 模块级别
os.environ['HF_HUB_OFFLINE'] = '1'  # 只在模块首次导入时执行
```

如果模块已经被导入（旧代码），这行代码不会再次执行。

### --reload 的限制

`uvicorn --reload` 监控文件变化，但：
- 只在文件保存后触发
- 有时候不会重新加载所有模块
- 环境变量的变化不会触发重载

**最可靠的方法**：完全重启服务

## 快速检查

```bash
# 检查是否有旧进程
ps aux | grep uvicorn

# 检查代码是否已更新
grep "HF_HUB_OFFLINE" backend/app/services/memory_service.py

# 检查模型缓存
ls ~/.cache/huggingface/hub/models--BAAI--bge-large-zh-v1.5/
```

## 常见问题

### Q: 我已经重启了，还是有网络访问？

A: 检查是否有多个进程在运行：
```bash
ps aux | grep python | grep -v grep
pkill -9 -f uvicorn  # 强制杀死所有
```

### Q: --reload 应该自动重启啊？

A: `--reload` 有时候不可靠，特别是：
- 模块级别的代码变化
- 环境变量的变化
- 导入顺序的变化

### Q: 我用的是 Docker，怎么重启？

A: 
```bash
docker-compose restart backend
# 或
docker-compose down && docker-compose up -d
```

## 文件清单

### 修复相关
- ✅ `backend/app/services/memory_service.py` - 已修复
- ✅ `backend/.env` - 已简化
- ✅ `docs/Important/MEMORY_SERVICE_FIX_SUMMARY.md` - 修复文档
- ✅ `docs/Important/OFFLINE_MODE_FINAL_FIX.md` - 详细说明

### 重启相关
- ✅ `backend/restart_service.sh` - 重启脚本
- ✅ `backend/RESTART_SERVICE_REQUIRED.md` - 重启说明
- ✅ `docs/Important/RESTART_REQUIRED_SUMMARY.md` - 本文档

### 测试相关
- ✅ `backend/verify_offline_mode.py` - 离线模式验证
- ✅ `backend/test_no_network_access.py` - 网络访问检查
- ✅ `backend/test_memory_service_fix.py` - 完整功能测试

## 总结

**问题**：代码已修复，但服务未重启，旧进程还在运行

**解决**：
```bash
cd backend
./restart_service.sh
```

**验证**：启动日志显示 "OFFLINE mode"，没有网络访问错误

**预计时间**：< 1 分钟
