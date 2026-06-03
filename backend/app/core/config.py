"""应用配置，从环境变量读取，兼容 .env。"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    app_name: str = "数据查询系统"
    debug: bool = False

    # 数据库 (MySQL 8 / 瀚高兼容)
    database_url: str = "mysql+pymysql://root:password@localhost:3306/data_query?charset=utf8mb4"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h

    # 导出文件存储
    export_storage_path: str = "./storage/exports"

    # 查询日志大报文存储策略
    # 小于该阈值的 payload 可直接入库；超过阈值则仅保存 preview + size，并落盘完整内容
    query_log_inline_max_bytes: int = 65535
    query_log_file_dir: str = "./storage/query_payloads"

    # 演示模式：mock 远程接口与加密
    use_mock_remote: bool = True
    use_mock_crypto: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
