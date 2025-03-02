from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any, Callable
import jwt
from jwt.exceptions import PyJWTError
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models.base import User

# 安全策略实例
security = HTTPBearer()

# 不需要验证的API路径列表
AUTH_WHITELIST = [
    f"{settings.API_V1_STR}/users/login",
    f"{settings.API_V1_STR}/users/register",
    f"{settings.API_V1_STR}/users/wxlogin",  # 微信登录接口
    "/",  # 根路径欢迎页
    "/docs",  # Swagger文档
    "/redoc",  # ReDoc文档
    "/openapi.json",  # OpenAPI规范
]

# 验证路径是否在白名单中
def is_path_in_whitelist(path: str) -> bool:
    # 精确匹配
    if path in AUTH_WHITELIST:
        return True
    
    # 检查是否是静态文件或文档相关路径
    if path.startswith("/static/") or path.startswith("/docs/") or path.startswith("/redoc/"):
        return True
    
    # 检查是否是白名单路径的子路径
    for whitelist_path in AUTH_WHITELIST:
        if path.startswith(f"{whitelist_path}/"):
            return True
    
    return False

# 解析JWT令牌
def decode_jwt_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的身份验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 获取用户信息
def get_user_from_token(payload: Dict[str, Any], db: Session) -> User:
    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的身份验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 尝试通过username查找用户（普通登录）
    user = db.query(User).filter(User.username == subject).first()
    
    # 如果未找到，尝试通过openid查找用户（微信登录）
    if user is None:
        user = db.query(User).filter(User.openid == subject).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被删除",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
    
    return user

# JWT验证中间件
class JWTAuthMiddleware:
    def __init__(self, app: Any):
        self.app = app
    
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            # 非HTTP请求直接放行（如WebSocket）
            await self.app(scope, receive, send)
            return
        
        # 创建请求对象
        request = Request(scope=scope, receive=receive, send=send)
        path = request.url.path
        
        # 检查路径是否在白名单中
        if is_path_in_whitelist(path):
            await self.app(scope, receive, send)
            return
        
        # 获取授权头
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未提供身份验证凭据",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token = auth_header.split(" ")[1]
            payload = decode_jwt_token(token)
            
            # 获取数据库会话
            db = next(get_db())
            user = get_user_from_token(payload, db)
            
            # 将用户信息添加到请求状态
            scope["user"] = user
            
            # 继续处理请求
            await self.app(scope, receive, send)
        except HTTPException as e:
            # 构建错误响应
            from starlette.responses import JSONResponse
            response = JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=e.headers or {},
            )
            await response(scope, receive, send)
        except Exception as e:
            # 处理其他异常
            from starlette.responses import JSONResponse
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "服务器内部错误"},
            )
            await response(scope, receive, send)

# 获取当前用户的依赖函数
async def get_current_user(request: Request) -> User:
    user = getattr(request.scope, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供有效的身份验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user