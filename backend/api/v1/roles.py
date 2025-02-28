from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from models.base import Role, Menu, API
from schemas.role import RoleCreate, RoleUpdate, RoleResponse, RoleDetailResponse, RolePermissionUpdate

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("/", response_model=List[RoleResponse])
async def get_roles(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """获取所有角色列表"""
    roles = db.query(Role).offset(skip).limit(limit).all()
    return roles

@router.get("/{role_id}", response_model=RoleDetailResponse)
async def get_role(role_id: int, db: Session = Depends(get_db)):
    """获取指定角色详情"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 获取角色关联的菜单和API权限
    menu_ids = [menu.id for menu in role.menus]
    api_ids = [api.id for api in role.apis]
    
    # 构建响应数据
    response_data = RoleDetailResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        created_at=role.created_at,
        updated_at=role.updated_at,
        menu_ids=menu_ids,
        api_ids=api_ids
    )
    
    return response_data

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    """创建新角色"""
    # 检查角色名是否已存在
    existing_role = db.query(Role).filter(Role.name == role.name).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="角色名已存在")
    
    # 创建新角色
    db_role = Role(**role.dict())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: int, role: RoleUpdate, db: Session = Depends(get_db)):
    """更新角色信息"""
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 如果更新角色名，检查是否与其他角色重名
    if role.name and role.name != db_role.name:
        existing_role = db.query(Role).filter(Role.name == role.name).first()
        if existing_role:
            raise HTTPException(status_code=400, detail="角色名已存在")
    
    # 更新角色信息
    update_data = role.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_role, key, value)
    
    db.commit()
    db.refresh(db_role)
    return db_role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: int, db: Session = Depends(get_db)):
    """删除角色"""
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 检查是否有用户关联此角色
    if db_role.users:
        raise HTTPException(status_code=400, detail="无法删除：该角色下有关联用户")
    
    db.delete(db_role)
    db.commit()
    return None

@router.put("/{role_id}/permissions", response_model=RoleDetailResponse)
async def update_role_permissions(role_id: int, permissions: RolePermissionUpdate, db: Session = Depends(get_db)):
    """更新角色权限（菜单和API）"""
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 更新菜单权限
    if permissions.menu_ids is not None:
        # 获取所有指定的菜单
        menus = db.query(Menu).filter(Menu.id.in_(permissions.menu_ids)).all()
        if len(menus) != len(permissions.menu_ids):
            raise HTTPException(status_code=400, detail="部分菜单ID不存在")
        db_role.menus = menus
    
    # 更新API权限
    if permissions.api_ids is not None:
        # 获取所有指定的API
        apis = db.query(API).filter(API.id.in_(permissions.api_ids)).all()
        if len(apis) != len(permissions.api_ids):
            raise HTTPException(status_code=400, detail="部分API ID不存在")
        db_role.apis = apis
    
    db.commit()
    db.refresh(db_role)
    
    # 构建响应数据
    menu_ids = [menu.id for menu in db_role.menus]
    api_ids = [api.id for api in db_role.apis]
    
    return RoleDetailResponse(
        id=db_role.id,
        name=db_role.name,
        description=db_role.description,
        created_at=db_role.created_at,
        updated_at=db_role.updated_at,
        menu_ids=menu_ids,
        api_ids=api_ids
    )