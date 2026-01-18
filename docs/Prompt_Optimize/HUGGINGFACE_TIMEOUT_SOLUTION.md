# HuggingFace 模型下载超时问题解决方案

## 问题描述

后端服务启动时卡在下载 BGE 向量模型，导致：
1. 服务无法正常启动
2. 无法通过 Ctrl+C 停止服务
3. 必须使用 `kill -9` 强制终止

**错误日志**：
```
MaxRetryError("HTTPSConnectionPool(host='huggingface.co', port=443): 
Max retries exceeded with url: /BAAI/bge-large-zh-v1.5/resolve/main/modules.json 
(Caused by ConnectTimeoutError(<HTTPSConnection(host='huggingface.co', port=443) at 0x154a41b90>, 
'Connection to huggingface.co timed out. (connect timeout=10)'))
```

## 根本原因

1. **网络问题**：HuggingFace 在中国大陆访问不稳定
2. **启动阻塞**：模型下载在服务启动时同步执行，阻塞了整个启动流程
3. **信号处理**：下载过程中无法响应 SIGINT (Ctrl+C) 信号

## 解决方案

### 方案 1：使用本地缓存的模型（推荐）✅

如果模型已经下载过，使用本地缓存：

```bash
# 检查模型缓存位置
ls -la ~/.cache/huggingface/hub/models--BAAI--bge-large-zh-v1.5/

# 如果存在，设置环境变量使用离线模式
export HF_HUB_OFFLINE=1
```

**修改 `.env` 文件**：
```bash
# 添加到 backend/.env
HF_HUB_OFFLINE=1
```

### 方案 2：使用 HuggingFace 镜像站（推荐）✅

使用国内镜像加速下载：

```bash
# 方法 1：使用环境变量
export HF_ENDPOINT=https://hf-mirror.com

# 方法 2：修改 .env 文件
echo "HF_ENDPOINT=https://hf-mirror.com" >> backend/.env
```

### 方案 3：延迟加载模型（最佳方案）✅

修改代码，让模型在首次使用时才加载，而不是启动时加载。

**修改 `backend/app/services/memory_service.py`**：

```python
class MemoryService:
    def __init__(self):
        self._embedding_model = None  # 延迟初始化
        self.model_name = "BAAI/bge-large-zh-v1.5"
    
    @property
    def embedding_model(self):
        """Lazy loading of embedding model"""
        if self._embedding_model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(self.model_name)
                logger.info("✅ Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load embedding model: {e}")
                logger.warning("⚠️  Vector memory features will be disabled")
                # Return a mock model that returns zero vectors
                self._embedding_model = None
        return self._embedding_model
    
    async def add_memory(self, user_id: int, text: str, metadata: dict = None):
        """Add memory with lazy model loading"""
        if self.embedding_model is None:
            logger.warning("Embedding model not available, skipping vector storage")
            return
        
        # ... rest of the code
```

### 方案 4：添加超时和重试控制

修改模型加载代码，添加超时控制：

```python
import os
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '30'  # 30 秒超时

from sentence_transformers import SentenceTransformer

try:
    model = SentenceTransformer(
        "BAAI/bge-large-zh-v1.5",
        cache_folder="~/.cache/huggingface",
        device="cpu"  # 强制使用 CPU，避免 GPU 相关问题
    )
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    # 使用备用方案或禁用向量功能
    model = None
```

### 方案 5：预下载模型（一次性操作）

手动预下载模型到本地：

```bash
# 创建下载脚本
cat > backend/scripts/download_model.py << 'EOF'
"""
Pre-download BGE model to local cache
Run this once before starting the service
"""
import os
from sentence_transformers import SentenceTransformer

# 使用镜像站
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

print("Downloading BGE model...")
model = SentenceTransformer("BAAI/bge-large-zh-v1.5")
print("✅ Model downloaded successfully!")
print(f"Cache location: {model.cache_folder}")
EOF

# 运行下载脚本
cd backend
python scripts/download_model.py
```

## 快速修复步骤

### 立即修复（5 分钟）

1. **强制停止服务**：
```bash
# 查找进程
ps aux | grep uvicorn

# 强制终止（替换 PID）
kill -9 <PID>
```

2. **使用镜像站**：
```bash
# 添加到 backend/.env
echo "HF_ENDPOINT=https://hf-mirror.com" >> backend/.env
```

3. **重启服务**：
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 长期方案（推荐）

实施**方案 3：延迟加载模型**，修改 `memory_service.py`。

## 代码修改

### 修改 `backend/app/services/memory_service.py`

<function_calls>
<invoke name="readFile">
<parameter name="explanation">Reading memory_service.py to see the current model loading implementation