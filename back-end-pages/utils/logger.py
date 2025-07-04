"""
日志配置工具
使用loguru提供结构化日志记录
"""

import sys
from loguru import logger
from typing import Optional


def setup_logger(name: Optional[str] = None, level: str = "INFO"):
    """
    设置应用日志配置
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        logger: 配置好的日志记录器
    """
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True
    )
    
    # 添加文件输出
    logger.add(
        "logs/app.log",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    # 添加错误日志文件
    logger.add(
        "logs/error.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="50 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    return logger 