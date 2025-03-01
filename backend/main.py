from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.v1 import api_router
from core.database import Base, engine
from core.logging import LoggingMiddleware, logger
from models.house_transaction import HouseTransaction  # 导入HouseTransaction模型
from models.geojson import GeoJsonData  # 添加新的模型

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加日志中间件
app.add_middleware(LoggingMiddleware)

# 注册API路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "欢迎使用HouseHelper API服务"}

if __name__ == "__main__":
    # 添加启动日志
    logger.info("正在启动HouseHelper API服务...")
    logger.info(f"服务器将运行在 http://0.0.0.0:8000")
    
    # 配置uvicorn使用自定义日志系统
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=False,
        log_level="info",
        log_config=None,
        use_colors=True
    )