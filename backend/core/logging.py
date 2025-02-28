import sys
from pathlib import Path
from loguru import logger
from fastapi import Request, Response
from typing import Callable, Any
import time

from .config import settings

# 配置日志记录器
def setup_logger():
    # 移除默认的处理器
    logger.remove()
    
    # 添加控制台输出处理器
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=True
    )
    
    # 确保日志目录存在
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 添加文件输出处理器
    logger.add(
        settings.LOG_FILE,
        rotation="100 MB",  # 当日志文件达到100MB时轮转
        retention="30 days",  # 保留30天的日志
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        encoding="utf-8"
    )
    
    return logger

# 创建日志中间件
class LoggingMiddleware:
    def __init__(self, app: Any):
        self.app = app
    
    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        if scope["type"] == "http":
            logger.info(
                f"[REQUEST] {scope['method']} {scope['path']}"
            )

        # 处理请求
        async def wrapped_send(message: dict) -> None:
            if message["type"] == "http.response.start":
                # 计算处理时间
                process_time = (time.time() - start_time) * 1000
                
                # 记录响应信息
                if scope["type"] == "http":
                    logger.info(
                        f"[RESPONSE] {scope['method']} {scope['path']} | "
                        f"Status: {message['status']} | "
                        f"Time: {process_time:.2f}ms"
                    )
            
            await send(message)
        
        await self.app(scope, receive, wrapped_send)

# 初始化日志记录器
logger = setup_logger()