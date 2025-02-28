from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# 角色基础模式
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

# 创建角色请求模式
class RoleCreate(RoleBase):
    pass

# 更新角色请求模式
class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

# 角色响应模式
class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 角色详细响应模式（包含关联的菜单和API权限）
class RoleDetailResponse(RoleResponse):
    menu_ids: List[int] = []
    api_ids: List[int] = []

# 角色权限分配请求模式
class RolePermissionUpdate(BaseModel):
    menu_ids: Optional[List[int]] = []
    api_ids: Optional[List[int]] = []