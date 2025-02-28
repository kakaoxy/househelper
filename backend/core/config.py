from pydantic import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # 项目基本信息
    PROJECT_NAME: str = "HouseHelper API"
    PROJECT_DESCRIPTION: str = "房产助手后端API服务"
    PROJECT_VERSION: str = "0.1.0"
    
    # API版本前缀
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/househelper.db"
    
    # JWT配置
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["*"]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = f"{BASE_DIR}/log/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 创建全局设置实例
settings = Settings()