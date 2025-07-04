"""
Ollama API 客户端
支持聊天对话和嵌入向量生成
基于Ollama 0.9.5 API规范
"""

import httpx
import json
from typing import AsyncGenerator, List, Dict, Any, Optional, Union
from loguru import logger


class OllamaClient:
    """Ollama API 客户端，支持最新的Ollama 0.9.5 API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        初始化Ollama客户端
        
        Args:
            base_url: Ollama服务地址
        """
        self.base_url = base_url
        self.chat_model = "deepseek-r1:latest"
        self.embedding_model = "modelscope.cn/Qwen/Qwen3-Embedding-8B-GGUF:latest"
        
    async def chat_stream(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        keep_alive: str = "5m"
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天对话（使用新的/api/chat端点）
        
        Args:
            messages: 消息列表，格式为[{"role": "user/assistant", "content": "..."}]
            model: 模型名称，默认使用配置的聊天模型
            system: 系统提示
            tools: 工具列表
            keep_alive: 模型保持时间
            
        Yields:
            str: 模型响应的文本块
        """
        model = model or self.chat_model
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                request_data = {
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "keep_alive": keep_alive
                }
                
                if system:
                    # 在消息前添加系统消息
                    full_messages = [{"role": "system", "content": system}] + messages
                    request_data["messages"] = full_messages
                
                if tools:
                    request_data["tools"] = tools
                
                logger.info(f"开始流式聊天请求，模型: {model}, 消息数: {len(messages)}")
                
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=request_data
                ) as response:
                    if response.status_code != 200:
                        error_msg = f"Ollama Chat API 错误: {response.status_code}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                    
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                # 处理文本内容
                                if "message" in data and "content" in data["message"]:
                                    content = data["message"]["content"]
                                    if content:
                                        yield content
                                
                                # 处理工具调用 (Ollama 0.9.5+ 新增功能)
                                if "message" in data and "tool_calls" in data["message"] and data["message"]["tool_calls"]:
                                    tool_calls = data["message"]["tool_calls"]
                                    for tool_call in tool_calls:
                                        # 将工具调用转换为特殊格式文本，便于后续处理
                                        tool_info = json.dumps(tool_call, ensure_ascii=False)
                                        yield f"<tool_call>{tool_info}</tool_call>"
                                
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"流式聊天请求失败: {e}")
            raise
    
    async def chat_stream_legacy(self, prompt: str, model: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        流式聊天对话（使用旧的/api/generate端点）
        
        Args:
            prompt: 用户输入
            model: 模型名称，默认使用配置的聊天模型
            
        Yields:
            str: 模型响应的文本块
        """
        model = model or self.chat_model
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                request_data = {
                    "model": model,
                    "prompt": prompt,
                    "stream": True
                }
                
                logger.info(f"开始流式聊天请求（Legacy），模型: {model}")
                
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=request_data
                ) as response:
                    if response.status_code != 200:
                        error_msg = f"Ollama API 错误: {response.status_code}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                    
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"流式聊天请求失败: {e}")
            raise
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        keep_alive: str = "5m"
    ) -> Dict[str, Any]:
        """
        非流式聊天对话（使用新的/api/chat端点）
        
        Args:
            messages: 消息列表
            model: 模型名称
            system: 系统提示
            tools: 工具列表
            keep_alive: 模型保持时间
            
        Returns:
            Dict[str, Any]: 完整的API响应
        """
        model = model or self.chat_model
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                request_data = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "keep_alive": keep_alive
                }
                
                if system:
                    # 在消息前添加系统消息
                    full_messages = [{"role": "system", "content": system}] + messages
                    request_data["messages"] = full_messages
                
                if tools:
                    request_data["tools"] = tools
                
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=request_data
                )
                
                if response.status_code != 200:
                    error_msg = f"Ollama Chat API 错误: {response.status_code}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                response_data = response.json()
                
                # 记录工具调用信息 (Ollama 0.9.5+ 新增功能)
                if "message" in response_data and "tool_calls" in response_data["message"] and response_data["message"]["tool_calls"]:
                    tool_calls = response_data["message"]["tool_calls"]
                    logger.info(f"模型返回工具调用: {len(tool_calls)} 个工具被调用")
                    
                return response_data
                
        except Exception as e:
            logger.error(f"聊天请求失败: {e}")
            raise
    
    async def get_embeddings(
        self, 
        texts: Union[str, List[str]], 
        model: Optional[str] = None,
        truncate: bool = True,
        keep_alive: str = "5m"
    ) -> List[List[float]]:
        """
        获取文本嵌入向量（使用新的/api/embed端点）
        
        Args:
            texts: 单个文本或文本列表
            model: 嵌入模型名称
            truncate: 是否截断超长文本
            keep_alive: 模型保持时间
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        model = model or self.embedding_model
        
        # 确保texts是列表格式
        if isinstance(texts, str):
            input_texts = [texts]
        else:
            input_texts = texts
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                request_data = {
                    "model": model,
                    "input": input_texts,
                    "truncate": truncate,
                    "keep_alive": keep_alive
                }
                
                logger.info(f"开始嵌入请求，模型: {model}, 文本数: {len(input_texts)}")
                
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json=request_data
                )
                
                if response.status_code != 200:
                    error_msg = f"Ollama Embed API 错误: {response.status_code}, 响应: {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                data = response.json()
                embeddings = data.get("embeddings", [])
                
                if not embeddings:
                    logger.warning("未获取到任何嵌入向量")
                    # 创建零向量作为占位符
                    return [[0.0] * 768] * len(input_texts)
                
                logger.info(f"成功获取 {len(embeddings)} 个文本嵌入")
                return embeddings
                
        except Exception as e:
            logger.error(f"获取嵌入向量失败: {e}")
            # 尝试回退到旧的API
            return await self._get_embeddings_legacy(input_texts, model)
    
    async def _get_embeddings_legacy(self, texts: List[str], model: str) -> List[List[float]]:
        """
        获取文本嵌入向量（使用旧的/api/embeddings端点作为回退）
        
        Args:
            texts: 文本列表
            model: 嵌入模型名称
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                embeddings = []
                
                for text in texts:
                    request_data = {
                        "model": model,
                        "prompt": text
                    }
                    
                    response = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json=request_data
                    )
                    
                    if response.status_code != 200:
                        logger.warning(f"Legacy嵌入API请求失败: {response.status_code}")
                        embeddings.append([0.0] * 768)
                        continue
                    
                    data = response.json()
                    if "embedding" in data:
                        embeddings.append(data["embedding"])
                    else:
                        logger.warning(f"未获取到文本嵌入: {text[:50]}...")
                        embeddings.append([0.0] * 768)
                
                logger.info(f"Legacy API成功获取 {len(embeddings)} 个文本嵌入")
                return embeddings
                
        except Exception as e:
            logger.error(f"Legacy嵌入API也失败: {e}")
            # 返回零向量作为最后的回退
            return [[0.0] * 768] * len(texts)
    
    async def check_health(self) -> bool:
        """
        检查Ollama服务健康状态
        
        Returns:
            bool: 服务是否可用
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama健康检查失败: {e}")
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        获取可用模型列表
        
        Returns:
            List[Dict[str, Any]]: 模型列表
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])
                else:
                    logger.error(f"获取模型列表失败: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []
    
    async def list_running_models(self) -> List[Dict[str, Any]]:
        """
        获取正在运行的模型列表
        
        Returns:
            List[Dict[str, Any]]: 运行中的模型列表
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/ps")
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])
                else:
                    logger.error(f"获取运行模型列表失败: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"获取运行模型列表失败: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        拉取模型（流式）
        
        Args:
            model_name: 模型名称
            
        Yields:
            Dict[str, Any]: 拉取进度信息
        """
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                request_data = {"model": model_name}
                
                logger.info(f"开始拉取模型: {model_name}")
                
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/pull",
                    json=request_data
                ) as response:
                    if response.status_code != 200:
                        error_msg = f"拉取模型失败: {response.status_code}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                    
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                yield data
                                if data.get("status") == "success":
                                    break
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"拉取模型失败: {e}")
            raise 