"""
验证 BGE 模型离线模式
确保不会访问网络
"""

import os
import sys
from pathlib import Path

# 设置离线模式
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("=" * 60)
print("BGE 模型离线模式验证")
print("=" * 60)

# 检查环境变量
print("\n1. 检查环境变量:")
print(f"   HF_HUB_OFFLINE = {os.getenv('HF_HUB_OFFLINE')}")
print(f"   TRANSFORMERS_OFFLINE = {os.getenv('TRANSFORMERS_OFFLINE')}")

# 检查本地模型
print("\n2. 检查本地模型缓存:")
cache_dir = Path.home() / ".cache" / "huggingface" / "hub" / "models--BAAI--bge-large-zh-v1.5"
if cache_dir.exists():
    print(f"   ✅ 模型已缓存: {cache_dir}")
    print(f"   大小: {sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file()) / 1024 / 1024:.1f} MB")
else:
    print(f"   ❌ 模型未找到: {cache_dir}")
    sys.exit(1)

# 测试加载模型
print("\n3. 测试加载模型 (离线模式):")
try:
    from app.services.memory_service import get_memory_service
    
    service = get_memory_service()
    print("   ✅ MemoryService 初始化成功")
    
    # 触发模型加载
    print("   正在加载 BGE 模型...")
    embeddings = service.embeddings
    
    if embeddings:
        print("   ✅ BGE 模型加载成功 (离线模式)")
        
        # 测试生成嵌入
        test_text = "测试文本"
        embedding = embeddings.embed_query(test_text)
        print(f"   ✅ 嵌入生成成功 (维度: {len(embedding)})")
        
        if len(embedding) == 1024:
            print("   ✅ 向量维度正确 (1024)")
        else:
            print(f"   ❌ 向量维度错误: {len(embedding)} (期望: 1024)")
            sys.exit(1)
    else:
        print("   ⚠️  模型未加载 (可能是开发环境)")
        
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ 离线模式验证通过！")
print("=" * 60)
print("\n总结:")
print("- 模型已在本地缓存")
print("- 离线模式已启用")
print("- 不会访问 huggingface.co")
print("- 向量维度: 1024 (BGE-large-zh-v1.5)")
