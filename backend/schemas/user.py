from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# 用户基础模式
class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

# 创建用户请求模式
class UserCreate(UserBase):
    password: str
    role_id: Optional[int] = None

# 更新用户请求模式
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    password: Optional[str] = None
    role_id: Optional[int] = None

# 用户登录请求模式
class UserLogin(BaseModel):
    username: str
    password: str

# 用户响应模式
class UserResponse(UserBase):
    id: int
    role_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# 令牌响应模式
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# 令牌数据模式
class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    permissions: Optional[List[str]] = None