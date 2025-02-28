from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# API基础模式
class APIBase(BaseModel):
    name: str
    path: str
    method: str
    description: Optional[str] = None

# 创建API请求模式
class APICreate(APIBase):
    pass

# 更新API请求模式
class APIUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    description: Optional[str] = None

# API响应模式
class APIResponse(APIBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# API列表响应模式
class APIListResponse(BaseModel):
    total: int
    items: List[APIResponse]

    class Config:
        from_attributes = True