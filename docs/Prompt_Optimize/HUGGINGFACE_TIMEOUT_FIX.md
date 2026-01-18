# HuggingFace 模型下载超时问题 - 完整解决方案

## 问题描述

后端服务启动时卡在下载 BGE 向量模型（`BAAI/bge-large-zh-v1.5`），导致：
- ✗ 服务无法正常启动
- ✗ 无法通过 Ctrl+C 停止服务
- ✗ 必须使用 `kill -9` 强制终止

**错误日志**：
```
MaxRetryError("HTTPSConnectionPool(host='huggingface.co', port=443): 
Max retries exceeded with url: /BAAI/bge-large-zh-v1.5/resolve/main/modules.json 
(Caused by ConnectTimeoutError)
```

## 根本原因

1. **网络问题**：HuggingFace 在中国大陆访问不稳定
2. **启动阻塞**：模型在 `__init__` 中同步加载，阻塞整个启动流程
3. **信号处理**：下载过程中无法响应 SIGINT (Ctrl+C) 信号

## 立即修复（5 分钟）

### Step 1: 强制停止服务

```bash
# 查找后端进程
ps aux | grep uvicorn

# 强制终止（替换 <PID> 为实际进程 ID）
kill -9 <PID>

# 或者一键停止
pkill -9 -f "uvicorn app.main:app"
```

### Step 2: 使用 HuggingFace 镜像站

```bash
# 添加到 backend/.env
echo "HF_ENDPOINT=https://hf-mirror.com" >> backend/.env
```

### Step 3: 重启服务

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 长期解决方案（推荐）

### 方案 1：延迟加载模型（最佳）✅

修改 `backend/app/services/memory_service.py`，让模型在首次使用时才加载：

```python
class MemoryService:
    """L3 Vector Memory Service with lazy loading"""
    
    def __init__(self):
        """Initialize without loading model"""
        self._embeddings = None  # Lazy initialization
        self._model_loading = False
        self._model_load_failed = False
        logger.info("MemoryService initialized (model will load on first use)")
    
    @property
    def embeddings(self):
        """Lazy loading of embedding model"""
        if self._embeddings is None and not self._model_load_failed and not self._model_loading:
            self._model_loading = True
            try:
                logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
                from langchain_huggingface import HuggingFaceEmbeddings
                
                self._embeddings = HuggingFaceEmbeddings(
                    model_name=settings.EMBEDDING_MODEL_NAME,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                logger.info("✅ Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load embedding model: {e}")
                logger.warning("⚠️  Vector memory features will be disabled")
                self._model_load_failed = True
            finally:
                self._model_loading = False
        
        return self._embeddings
    
    async def _generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding with lazy model loading"""
        try:
            if not self.embeddings:  # This will trigger lazy loading
                logger.warning("Embeddings not available")
                return None
            
            embedding = self.embeddings.embed_query(text)
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
```

### 方案 2：添加超时和重试控制

修改 `backend/app/core/config.py`，添加超时配置：

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # HuggingFace settings
    HF_ENDPOINT: str = "https://hf-mirror.com"  # 使用镜像站
    HF_HUB_DOWNLOAD_TIMEOUT: int = 30  # 30 秒超时
    HF_HUB_OFFLINE: bool = False  # 离线模式
    
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-large-zh-v1.5"
```

然后在 `memory_service.py` 中使用：

```python
import os

def __init__(self):
    # Set HuggingFace environment variables
    if settings.HF_ENDPOINT:
        os.environ['HF_ENDPOINT'] = settings.HF_ENDPOINT
    if settings.HF_HUB_DOWNLOAD_TIMEOUT:
        os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = str(settings.HF_HUB_DOWNLOAD_TIMEOUT)
    if settings.HF_HUB_OFFLINE:
        os.environ['HF_HUB_OFFLINE'] = '1'
    
    # ... rest of init
```

### 方案 3：预下载模型（一次性操作）

创建下载脚本 `backend/scripts/download_bge_model.py`：

```python
"""
Pre-download BGE model to local cache
Run this once before starting the service
"""
import os
from langchain_huggingface import HuggingFaceEmbeddings

# 使用镜像站
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

print("Downloading BGE model (BAAI/bge-large-zh-v1.5)...")
print("This may take a few minutes...")

try:
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-zh-v1.5",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Test embedding
    test_embedding = embeddings.embed_query("测试")
    print(f"✅ Model downloaded successfully!")
    print(f"✅ Embedding dimension: {len(test_embedding)}")
    print(f"✅ Cache location: ~/.cache/huggingface/")
    
except Exception as e:
    print(f"❌ Failed to download model: {e}")
    print("Please check your network connection and try again.")
```

运行下载：

```bash
cd backend
python scripts/download_bge_model.py
```

## 环境变量配置

在 `backend/.env` 中添加：

```bash
# HuggingFace 配置
HF_ENDPOINT=https://hf-mirror.com
HF_HUB_DOWNLOAD_TIMEOUT=30
# HF_HUB_OFFLINE=1  # 如果模型已下载，可以启用离线模式

# 向量模型配置
EMBEDDING_MODEL_NAME=BAAI/bge-large-zh-v1.5
```

## 验证修复

### 1. 检查模型缓存

```bash
# 检查模型是否已下载
ls -la ~/.cache/huggingface/hub/models--BAAI--bge-large-zh-v1.5/

# 如果存在，说明模型已缓存
```

### 2. 测试服务启动

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**预期结果**：
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     MemoryService initialized (model will load on first use)  # ✅ 不阻塞启动
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. 测试模型加载

```bash
# 发送一条消息触发模型加载
curl -X POST http://localhost:8000/api/v1/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "测试消息"}'
```

**预期日志**：
```
INFO:     Loading embedding model: BAAI/bge-large-zh-v1.5
INFO:     ✅ Embedding model loaded successfully
```

## 故障排除

### 问题 1：模型下载仍然超时

**解决方案**：
```bash
# 使用离线模式（需要先手动下载模型）
export HF_HUB_OFFLINE=1

# 或者禁用向量功能（临时方案）
# 在 memory_service.py 中直接返回 None
```

### 问题 2：服务启动后无法停止

**解决方案**：
```bash
# 方法 1：使用 pkill
pkill -9 -f "uvicorn app.main:app"

# 方法 2：查找并 kill
ps aux | grep uvicorn
kill -9 <PID>

# 方法 3：使用 killall
killall -9 uvicorn
```

### 问题 3：模型加载失败

**解决方案**：
```bash
# 清除缓存重新下载
rm -rf ~/.cache/huggingface/hub/models--BAAI--bge-large-zh-v1.5/

# 使用镜像站重新下载
export HF_ENDPOINT=https://hf-mirror.com
python scripts/download_bge_model.py
```

## 相关文件

- `backend/app/services/memory_service.py` - 需要修改
- `backend/app/core/config.py` - 添加配置
- `backend/.env` - 环境变量
- `backend/scripts/download_bge_model.py` - 预下载脚本（新建）

## 优先级

🔴 **高优先级** - 阻塞服务启动，影响开发和部署

## 总结

**推荐方案**：
1. ✅ 立即使用镜像站（`HF_ENDPOINT=https://hf-mirror.com`）
2. ✅ 实施延迟加载（修改 `memory_service.py`）
3. ✅ 预下载模型到本地缓存

**效果**：
- 服务启动不再阻塞（< 1 秒）
- 模型在首次使用时才加载（3-5 秒）
- 可以正常使用 Ctrl+C 停止服务
- 网络问题不影响服务启动
