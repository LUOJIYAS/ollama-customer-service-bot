"""
配置管理模块
统一管理应用配置参数
"""

import os
from typing import Optional


class Config:
    """应用配置类"""
    
    # Ollama配置
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "deepseek-r1:latest")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "modelscope.cn/Qwen/Qwen3-Embedding-8B-GGUF:latest")
    
    # ChromaDB配置
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")
    
    # 服务配置
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS配置
    ALLOWED_ORIGINS: list = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    
    @classmethod
    def get_ollama_config(cls) -> dict:
        """获取Ollama配置"""
        return {
            "base_url": cls.OLLAMA_BASE_URL,
            "chat_model": cls.CHAT_MODEL,
            "embedding_model": cls.EMBEDDING_MODEL
        }
    
    @classmethod
    def get_server_config(cls) -> dict:
        """获取服务器配置"""
        return {
            "host": cls.SERVER_HOST,
            "port": cls.SERVER_PORT,
            "log_level": cls.LOG_LEVEL.lower()
        }
    
    @classmethod
    def get_database_config(cls) -> dict:
        """获取数据库配置"""
        return {
            "persist_directory": cls.CHROMA_PERSIST_DIRECTORY
        }

# 全局配置实例
config = Config() 