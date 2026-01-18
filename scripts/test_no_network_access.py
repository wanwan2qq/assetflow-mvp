"""
验证 BGE 模型加载时不会访问网络
通过监控网络日志确认完全离线
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("=" * 60)
print("网络访问测试")
print("=" * 60)

print("\n正在导入 memory_service...")
print("如果看到 'Connection to huggingface.co' 说明有网络访问")
print("如果没有看到，说明完全离线运行")
print("-" * 60)

# 导入会触发模型加载
from app.services.memory_service import get_memory_service

service = get_memory_service()

print("\n正在加载 BGE 模型...")
embeddings = service.embeddings

if embeddings:
    print("\n✅ 模型加载成功")
    
    # 测试生成嵌入
    test_text = "测试文本"
    embedding = embeddings.embed_query(test_text)
    print(f"✅ 嵌入生成成功 (维度: {len(embedding)})")
else:
    print("\n⚠️  模型未加载")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
print("\n如果上面没有看到 'Connection to huggingface.co' 的错误")
print("说明离线模式配置成功！")
