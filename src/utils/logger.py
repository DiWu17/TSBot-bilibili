"""日志配置工具"""

import logging
import sys
from typing import Optional


def setup_logger(
    log_file: Optional[str] = None,
    level: str = 'INFO',
    console: bool = True
) -> logging.Logger:
    """
    配置并返回一个根日志记录器
    
    Args:
        log_file: 日志文件路径（可选）
        level: 日志级别
        console: 是否输出到控制台
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 清理已存在的 handler，避免重复输出
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)

