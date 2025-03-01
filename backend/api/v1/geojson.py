from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import json

from core.database import get_db
from models.geojson import GeoJsonData
from schemas.geojson import GeoJson, GeoJsonCreate

router = APIRouter()

# 定义GeoJSON文件的基础路径
GEOJSON_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "geojson")

@router.get("/geojson/{name}")
async def get_geojson(name: str):
    """获取指定名称的GeoJSON数据"""
    # 检查文件名是否已包含扩展名
    if name.endswith('.geojson') or name.endswith('.json'):
        file_path = os.path.join(GEOJSON_BASE_PATH, name)
    else:
        # 尝试两种扩展名
        json_path = os.path.join(GEOJSON_BASE_PATH, f"{name}.json")
        geojson_path = os.path.join(GEOJSON_BASE_PATH, f"{name}.geojson")
        
        if os.path.exists(json_path):
            file_path = json_path
        elif os.path.exists(geojson_path):
            file_path = geojson_path
        else:
            raise HTTPException(status_code=404, detail=f"GeoJSON文件 {name} 不存在")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取GeoJSON文件失败: {str(e)}")

@router.get("/geojson", response_model=List[GeoJson])
async def list_geojson(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """获取GeoJSON数据列表"""
    geojson_list = db.query(GeoJsonData).offset(skip).limit(limit).all()
    return geojson_list

@router.post("/geojson", response_model=GeoJson)
async def create_geojson(geojson: GeoJsonCreate, db: Session = Depends(get_db)):
    """创建新的GeoJSON数据"""
    db_geojson = GeoJsonData(**geojson.dict())
    db.add(db_geojson)
    db.commit()
    db.refresh(db_geojson)
    return db_geojson