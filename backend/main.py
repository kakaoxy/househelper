from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.v1.base import router as base_router
from api.v1.users import router as users_router
from api.v1.roles import router as roles_router
from api.v1.menus import router as menus_router
from api.v1.apis import router as apis_router
from api.v1.house_transactions import router as house_transactions_router
from core.database import Base, engine
from core.logging import LoggingMiddleware, logger

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

# 注册路由
app.include_router(base_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")
app.include_router(menus_router, prefix="/api/v1")
app.include_router(apis_router, prefix="/api/v1")
app.include_router(house_transactions_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "欢迎使用HouseHelper API服务"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=True,
        log_level="info",
        log_config=None  # 使用默认日志配置
    )