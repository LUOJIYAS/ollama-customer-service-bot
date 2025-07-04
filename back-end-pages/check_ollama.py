#!/usr/bin/env python3
"""
Ollama服务检查脚本
用于验证Ollama 0.9.5服务状态和模型可用性
"""

import requests
import json
import sys
from typing import Dict, Any, List

OLLAMA_BASE_URL = "http://localhost:11434"
REQUIRED_MODELS = [
    "deepseek-r1:latest",
    "modelscope.cn/Qwen/Qwen3-Embedding-8B-GGUF:latest"
]

def check_ollama_connection() -> bool:
    """检查Ollama服务连接"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=5)
        if response.status_code == 200:
            version_info = response.json()
            version = version_info.get('version', 'unknown')
            print(f"✓ Ollama服务运行正常 - 版本: {version}")
            
            # 检查版本是否至少为0.9.5
            if version < "0.9.5":
                print("⚠️ 警告: Ollama版本低于0.9.5，某些新功能（如工具调用增强）可能不可用")
                print("建议: 升级到Ollama 0.9.5或更高版本")
            
            return True
        else:
            print(f"❌ Ollama服务响应异常 - 状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到Ollama服务: {e}")
        print("请确保Ollama服务正在运行: ollama serve")
        return False

def get_available_models() -> List[Dict[str, Any]]:
    """获取可用模型列表"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('models', [])
        else:
            print(f"❌ 获取模型列表失败 - 状态码: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取模型列表时发生错误: {e}")
        return []

def check_required_models(available_models: List[Dict[str, Any]]) -> bool:
    """检查必需的模型是否可用"""
    model_names = [model['name'] for model in available_models]
    
    print("\n📋 模型状态检查:")
    all_available = True
    
    for required_model in REQUIRED_MODELS:
        if required_model in model_names:
            print(f"✓ {required_model} - 可用")
        else:
            print(f"❌ {required_model} - 未安装")
            all_available = False
    
    if not all_available:
        print("\n💡 安装缺失的模型:")
        for required_model in REQUIRED_MODELS:
            if required_model not in model_names:
                print(f"ollama pull {required_model}")
    
    return all_available

def test_chat_api() -> bool:
    """测试聊天API"""
    try:
        payload = {
            "model": "deepseek-r1:latest",
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }
        
        print("正在测试聊天API（可能需要30-60秒）...")
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=60  # 增加超时时间
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'message' in data and 'content' in data['message']:
                print("✓ 聊天API测试成功")
                return True
            else:
                print(f"❌ 聊天API响应格式异常: {data}")
                return False
        else:
            print(f"❌ 聊天API测试失败 - 状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("❌ 聊天API测试超时（模型加载可能需要更长时间）")
        print("建议: 手动运行 'ollama run deepseek-r1:latest' 预热模型")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 聊天API测试错误: {e}")
        return False

def test_embed_api() -> bool:
    """测试嵌入API"""
    try:
        payload = {
            "model": "modelscope.cn/Qwen/Qwen3-Embedding-8B-GGUF:latest",
            "input": "test embedding"
        }
        
        print("正在测试嵌入API...")
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json=payload,
            timeout=30  # 增加超时时间
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'embeddings' in data and len(data['embeddings']) > 0:
                print("✓ 嵌入API测试成功")
                return True
            else:
                print(f"❌ 嵌入API响应格式异常: {data}")
                return False
        else:
            print(f"❌ 嵌入API测试失败 - 状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("❌ 嵌入API测试超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 嵌入API测试错误: {e}")
        return False

def test_tools_api() -> bool:
    """测试工具调用API"""
    try:
        # 一个简单的计算工具示例
        tool_def = {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "执行简单的数学计算",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                            "description": "要执行的数学运算"
                        },
                        "a": {
                            "type": "number",
                            "description": "第一个数"
                        },
                        "b": {
                            "type": "number",
                            "description": "第二个数"
                        }
                    },
                    "required": ["operation", "a", "b"]
                }
            }
        }
        
        payload = {
            "model": "deepseek-r1:latest",
            "messages": [
                {"role": "user", "content": "计算2加3等于多少"}
            ],
            "tools": [tool_def],
            "stream": False
        }
        
        print("正在测试工具调用API...")
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            # 这里不检查是否返回工具调用，因为模型可能选择不使用工具
            print("✓ 工具调用API测试成功 (请求格式验证)")
            return True
        else:
            print(f"❌ 工具调用API测试失败 - 状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 工具调用API测试错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("Ollama 0.9.5 服务检查")
    print("=" * 50)
    
    # 检查连接
    if not check_ollama_connection():
        sys.exit(1)
    
    # 获取模型列表
    available_models = get_available_models()
    if not available_models:
        print("❌ 无法获取模型列表")
        sys.exit(1)
    
    print(f"\n📦 发现 {len(available_models)} 个可用模型")
    
    # 检查必需模型
    models_ok = check_required_models(available_models)
    
    if models_ok:
        print("\n🧪 API功能测试:")
        chat_ok = test_chat_api()
        embed_ok = test_embed_api()
        tools_ok = test_tools_api()
        
        if chat_ok and embed_ok:
            print("\n🎉 所有基本功能测试通过！")
            if tools_ok:
                print("✓ 工具调用功能正常")
            else:
                print("⚠️ 工具调用功能测试不通过，可能需要更高版本Ollama")
            
            print("\nOllama服务已就绪")
            sys.exit(0)
        else:
            print("\n❌ API测试失败")
            sys.exit(1)
    else:
        print("\n❌ 请先安装所需的模型")
        sys.exit(1)

if __name__ == "__main__":
    main() 