from fastapi import APIRouter

from .base import router as base_router
from .users import router as users_router
from .roles import router as roles_router
from .menus import router as menus_router
from .apis import router as apis_router
from .house_transactions import router as house_transactions_router
from .geojson import router as geojson_router

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(base_router)
api_router.include_router(users_router)
api_router.include_router(roles_router)
api_router.include_router(menus_router)
api_router.include_router(apis_router)
api_router.include_router(house_transactions_router)
api_router.include_router(geojson_router)