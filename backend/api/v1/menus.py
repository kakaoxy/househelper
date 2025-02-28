from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from models.base import Menu
from schemas.menu import MenuCreate, MenuUpdate, MenuResponse, MenuTreeResponse

router = APIRouter(prefix="/menus", tags=["menus"])

@router.get("/", response_model=List[MenuResponse])
async def get_menus(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """获取所有菜单列表"""
    menus = db.query(Menu).offset(skip).limit(limit).all()
    return menus

@router.get("/tree", response_model=List[MenuTreeResponse])
async def get_menu_tree(db: Session = Depends(get_db)):
    """获取菜单树形结构"""
    # 获取所有顶级菜单（parent_id为空的菜单）
    root_menus = db.query(Menu).filter(Menu.parent_id == None).all()
    
    # 递归构建菜单树
    def build_menu_tree(menu_item):
        menu_dict = MenuTreeResponse(
            id=menu_item.id,
            name=menu_item.name,
            path=menu_item.path,
            component=menu_item.component,
            icon=menu_item.icon,
            sort_order=menu_item.sort_order,
            parent_id=menu_item.parent_id,
            is_hidden=menu_item.is_hidden,
            created_at=menu_item.created_at,
            updated_at=menu_item.updated_at,
            children=[]
        )
        
        # 获取子菜单
        children = db.query(Menu).filter(Menu.parent_id == menu_item.id).order_by(Menu.sort_order).all()
        if children:
            menu_dict.children = [build_menu_tree(child) for child in children]
        
        return menu_dict
    
    # 构建完整的菜单树
    menu_tree = [build_menu_tree(menu) for menu in root_menus]
    return menu_tree

@router.get("/{menu_id}", response_model=MenuResponse)
async def get_menu(menu_id: int, db: Session = Depends(get_db)):
    """获取指定菜单详情"""
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    return menu

@router.post("/", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
async def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    """创建新菜单"""
    # 如果指定了父菜单，检查父菜单是否存在
    if menu.parent_id:
        parent_menu = db.query(Menu).filter(Menu.id == menu.parent_id).first()
        if not parent_menu:
            raise HTTPException(status_code=400, detail="父菜单不存在")
    
    # 创建新菜单
    db_menu = Menu(**menu.dict())
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu

@router.put("/{menu_id}", response_model=MenuResponse)
async def update_menu(menu_id: int, menu: MenuUpdate, db: Session = Depends(get_db)):
    """更新菜单信息"""
    db_menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not db_menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    
    # 如果更新父菜单ID，检查父菜单是否存在
    if menu.parent_id is not None and menu.parent_id != db_menu.parent_id:
        # 不能将菜单的父级设置为自己或其子菜单
        if menu.parent_id == menu_id:
            raise HTTPException(status_code=400, detail="不能将菜单的父级设置为自己")
        
        # 检查父菜单是否存在
        if menu.parent_id > 0:
            parent_menu = db.query(Menu).filter(Menu.id == menu.parent_id).first()
            if not parent_menu:
                raise HTTPException(status_code=400, detail="父菜单不存在")
    
    # 更新菜单信息
    update_data = menu.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_menu, key, value)
    
    db.commit()
    db.refresh(db_menu)
    return db_menu

@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    """删除菜单"""
    db_menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not db_menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    
    # 检查是否有子菜单
    children = db.query(Menu).filter(Menu.parent_id == menu_id).all()
    if children:
        raise HTTPException(status_code=400, detail="无法删除：该菜单下有子菜单")
    
    db.delete(db_menu)
    db.commit()
    return None