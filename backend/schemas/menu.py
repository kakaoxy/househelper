from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# 菜单基础模式
class MenuBase(BaseModel):
    name: str
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = 0
    parent_id: Optional[int] = None
    is_hidden: Optional[bool] = False

# 创建菜单请求模式
class MenuCreate(MenuBase):
    pass

# 更新菜单请求模式
class MenuUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    parent_id: Optional[int] = None
    is_hidden: Optional[bool] = None

# 菜单响应模式
class MenuResponse(MenuBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 菜单树形结构响应模式
class MenuTreeResponse(MenuResponse):
    children: List['MenuTreeResponse'] = []

# 解决循环引用问题
MenuTreeResponse.update_forward_refs()