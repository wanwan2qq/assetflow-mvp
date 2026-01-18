"""
Pre-download BGE model to local cache
Run this once before starting the service to avoid startup delays

Usage:
    cd backend
    python scripts/download_bge_model.py
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_huggingface import HuggingFaceEmbeddings

# 使用 HuggingFace 镜像站（中国大陆访问更快）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

print("=" * 80)
print("BGE Model Downloader")
print("=" * 80)
print("\nDownloading BGE model (BAAI/bge-large-zh-v1.5)...")
print("This may take a few minutes depending on your network speed...")
print("\nModel size: ~1.3 GB")
print("Cache location: ~/.cache/huggingface/hub/")
print("\n" + "=" * 80)

try:
    # Download and initialize the model
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-zh-v1.5",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Test embedding to verify model works
    print("\nTesting model...")
    test_embedding = embeddings.embed_query("测试文本")
    
    print("\n" + "=" * 80)
    print("✅ SUCCESS!")
    print("=" * 80)
    print(f"✅ Model downloaded successfully!")
    print(f"✅ Embedding dimension: {len(test_embedding)}")
    print(f"✅ Cache location: ~/.cache/huggingface/hub/models--BAAI--bge-large-zh-v1.5/")
    print("\nYou can now start the backend service without download delays.")
    print("\nOptional: Set HF_HUB_OFFLINE=1 in .env to use offline mode.")
    print("=" * 80)
    
except Exception as e:
    print("\n" + "=" * 80)
    print("❌ FAILED!")
    print("=" * 80)
    print(f"❌ Failed to download model: {e}")
    print("\nTroubleshooting:")
    print("1. Check your network connection")
    print("2. Try using a VPN if you're in China")
    print("3. Verify you have enough disk space (~2 GB)")
    print("4. Check if ~/.cache/huggingface/ is writable")
    print("\nFor more help, see: docs/Important/HUGGINGFACE_TIMEOUT_FIX.md")
    print("=" * 80)
    sys.exit(1)
