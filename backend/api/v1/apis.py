from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from models.base import API
from schemas.api import APICreate, APIUpdate, APIResponse, APIListResponse

router = APIRouter(prefix="/apis", tags=["apis"])

@router.get("/", response_model=APIListResponse)
async def get_apis(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """获取所有API列表"""
    apis = db.query(API).offset(skip).limit(limit).all()
    total = db.query(API).count()
    return {"total": total, "items": apis}

@router.get("/{api_id}", response_model=APIResponse)
async def get_api(api_id: int, db: Session = Depends(get_db)):
    """获取指定API详情"""
    api = db.query(API).filter(API.id == api_id).first()
    if not api:
        raise HTTPException(status_code=404, detail="API不存在")
    return api

@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_api(api: APICreate, db: Session = Depends(get_db)):
    """创建新API"""
    # 检查API路径和方法组合是否已存在
    existing_api = db.query(API).filter(API.path == api.path, API.method == api.method).first()
    if existing_api:
        raise HTTPException(status_code=400, detail="相同路径和方法的API已存在")
    
    # 创建新API
    db_api = API(**api.dict())
    db.add(db_api)
    db.commit()
    db.refresh(db_api)
    return db_api

@router.put("/{api_id}", response_model=APIResponse)
async def update_api(api_id: int, api: APIUpdate, db: Session = Depends(get_db)):
    """更新API信息"""
    db_api = db.query(API).filter(API.id == api_id).first()
    if not db_api:
        raise HTTPException(status_code=404, detail="API不存在")
    
    # 如果更新路径或方法，检查是否与其他API重复
    if (api.path is not None or api.method is not None) and (api.path != db_api.path or api.method != db_api.method):
        check_path = api.path if api.path is not None else db_api.path
        check_method = api.method if api.method is not None else db_api.method
        existing_api = db.query(API).filter(API.path == check_path, API.method == check_method).first()
        if existing_api and existing_api.id != api_id:
            raise HTTPException(status_code=400, detail="相同路径和方法的API已存在")
    
    # 更新API信息
    update_data = api.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_api, key, value)
    
    db.commit()
    db.refresh(db_api)
    return db_api

@router.delete("/{api_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api(api_id: int, db: Session = Depends(get_db)):
    """删除API"""
    db_api = db.query(API).filter(API.id == api_id).first()
    if not db_api:
        raise HTTPException(status_code=404, detail="API不存在")
    
    db.delete(db_api)
    db.commit()
    return None