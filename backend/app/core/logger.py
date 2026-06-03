"""日志配置，使用 Loguru。"""
import sys
from loguru import logger

# 移除默认 handler，避免重复
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO",
)
# 可选：写入文件
# logger.add("logs/app_{time:YYYY-MM-DD}.log", rotation="1 day", retention="7 days", level="INFO")
