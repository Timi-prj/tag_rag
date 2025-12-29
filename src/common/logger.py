"""
异步日志模块
提供简单、异步、支持大小和时间轮转的日志功能
"""
import os
import sys
import logging
import logging.handlers
import queue
import threading
from typing import Optional, Dict, Any
from datetime import datetime


class AsyncLoggingFactory:
    """异步日志工厂"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._loggers: Dict[str, logging.Logger] = {}
            self._queue = queue.Queue(-1)  # 无限队列
            self._listener = None
            self._handlers = {}
            self._initialized = True
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        配置日志系统
        
        Args:
            config: 日志配置字典，包含以下字段：
                - level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
                - format: 日志格式字符串
                - handlers: 处理器配置
        """
        if self._listener and self._listener._thread.is_alive():
            self._listener.stop()
        
        # 设置根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.get('level', 'INFO')))
        
        # 创建格式器
        log_format = config.get('format', 
                              '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter(log_format)
        
        # 清理现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        self._handlers.clear()
        
        # 配置处理器
        handlers_config = config.get('handlers', {})
        
        # 控制台处理器
        if handlers_config.get('console', {}).get('enabled', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, 
                                           handlers_config['console'].get('level', 'INFO')))
            console_handler.setFormatter(formatter)
            self._handlers['console'] = console_handler
        
        # 文件处理器（结合大小和时间轮转）
        file_config = handlers_config.get('file', {})
        if file_config.get('enabled', True):
            log_path = file_config.get('path', './logs/tag_rag.log')
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            max_bytes = file_config.get('max_bytes', 104857600)  # 100MB
            backup_count = file_config.get('backup_count', 7)     # 保留7天
            when = file_config.get('when', 'midnight')           # 每天轮转
            
            # 创建轮转文件处理器
            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=log_path,
                when=when,
                interval=1,
                backupCount=backup_count,
                encoding='utf-8'
            )
            
            # 添加大小检查（通过自定义类实现）
            class SizedTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
                def shouldRollover(self, record):
                    # 检查文件大小
                    if os.path.exists(self.baseFilename):
                        if os.stat(self.baseFilename).st_size >= max_bytes:
                            return 1
                    # 检查时间
                    return super().shouldRollover(record)
            
            file_handler = SizedTimedRotatingFileHandler(
                filename=log_path,
                when=when,
                interval=1,
                backupCount=backup_count,
                encoding='utf-8'
            )
            
            file_handler.setLevel(getattr(logging, file_config.get('level', 'INFO')))
            file_handler.setFormatter(formatter)
            self._handlers['file'] = file_handler
        
        # 创建队列处理器
        queue_handler = logging.handlers.QueueHandler(self._queue)
        root_logger.addHandler(queue_handler)
        
        # 启动监听器
        self._listener = logging.handlers.QueueListener(
            self._queue,
            *self._handlers.values(),
            respect_handler_level=True
        )
        self._listener.start()
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取或创建指定名称的logger
        
        Args:
            name: logger名称，通常使用模块名
            
        Returns:
            配置好的logger实例
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]
    
    def shutdown(self) -> None:
        """关闭日志系统"""
        if self._listener:
            self._listener.stop()
        logging.shutdown()


# 全局工厂实例
_factory = AsyncLoggingFactory()


def configure_logging(config: Dict[str, Any]) -> None:
    """
    配置日志系统（对外接口）
    
    Args:
        config: 日志配置字典
    """
    _factory.configure(config)


def get_logger(name: str) -> logging.Logger:
    """
    获取logger（对外接口）
    
    Args:
        name: logger名称
        
    Returns:
        logger实例
    """
    return _factory.get_logger(name)


def shutdown_logging() -> None:
    """关闭日志系统（对外接口）"""
    _factory.shutdown()


# 常用快捷函数
def debug(msg: str, *args, **kwargs) -> None:
    """DEBUG级别日志"""
    logger = get_logger('tag_rag')
    logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    """INFO级别日志"""
    logger = get_logger('tag_rag')
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """WARNING级别日志"""
    logger = get_logger('tag_rag')
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """ERROR级别日志"""
    logger = get_logger('tag_rag')
    logger.error(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs) -> None:
    """异常日志（自动包含堆栈）"""
    logger = get_logger('tag_rag')
    logger.exception(msg, *args, **kwargs)


# 上下文管理器，用于临时修改日志级别
class temporary_log_level:
    """临时修改日志级别的上下文管理器"""
    
    def __init__(self, logger_name: str, level: str):
        self.logger_name = logger_name
        self.level = getattr(logging, level.upper())
        self.original_level = None
    
    def __enter__(self):
        logger = logging.getLogger(self.logger_name)
        self.original_level = logger.level
        logger.setLevel(self.level)
        return logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(self.original_level)
