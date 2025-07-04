#!/usr/bin/env python3
"""
智能客服机器人后端启动脚本
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_directories():
    """创建必要的目录"""
    directories = [
        "data/chroma_db",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

def check_ollama_service():
    """检查Ollama服务状态"""
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        if response.status_code == 200:
            print("✓ Ollama服务运行正常")
            return True
        else:
            print("✗ Ollama服务响应异常")
            return False
    except Exception as e:
        print(f"✗ 无法连接到Ollama服务: {e}")
        print("请确保Ollama已安装并运行: ollama serve")
        return False

def check_models():
    """检查必要的模型是否已下载"""
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=10.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            required_models = [
                "deepseek-r1:latest",
                "modelscope.cn/Qwen/Qwen3-Embedding-8B-GGUF:latest"
            ]
            
            missing_models = []
            for model in required_models:
                if not any(model in name for name in model_names):
                    missing_models.append(model)
            
            if missing_models:
                print("✗ 缺少以下模型:")
                for model in missing_models:
                    print(f"  - {model}")
                print("\n请运行以下命令下载模型:")
                for model in missing_models:
                    print(f"  ollama pull {model}")
                return False
            else:
                print("✓ 所有必需模型已下载")
                return True
    except Exception as e:
        print(f"✗ 检查模型失败: {e}")
        return False

async def main():
    """主函数"""
    print("🤖 启动智能客服机器人后端服务")
    print("=" * 50)
    
    # 创建必要目录
    create_directories()
    
    # 检查Ollama服务
    if not check_ollama_service():
        sys.exit(1)
    
    # 检查模型
    if not check_models():
        sys.exit(1)
    
    # 启动FastAPI服务
    print("\n🚀 启动FastAPI服务...")
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"✗ 启动服务失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 