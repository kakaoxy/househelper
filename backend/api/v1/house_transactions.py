from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from core.database import get_db
from crud.house_transaction import house_transaction
from schemas.house_transaction import (
    HouseTransactionCreate, 
    HouseTransactionUpdate, 
    HouseTransactionResponse,
    HouseTransactionListResponse
)

router = APIRouter(prefix="/house-transactions", tags=["house-transactions"])

@router.get("/", response_model=HouseTransactionListResponse)
async def get_house_transactions(
    db: Session = Depends(get_db),
    city: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
):
    """获取房产成交量数据列表，支持按城市和日期范围筛选"""
    if city or start_date or end_date:
        # 按条件筛选
        transactions = house_transaction.get_by_date_range(
            db, city=city, start_date=start_date, end_date=end_date, skip=skip, limit=limit
        )
        # 计算总数
        conditions = {}
        if city:
            conditions["city"] = city
        total = house_transaction.count_by(db, conditions=conditions)
    else:
        # 获取所有数据
        transactions = house_transaction.get_multi(db, skip=skip, limit=limit)
        total = house_transaction.get_count(db)
    
    return {"total": total, "items": transactions}

@router.get("/{transaction_id}", response_model=HouseTransactionResponse)
async def get_house_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """获取指定ID的房产成交量数据"""
    transaction = house_transaction.get(db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="房产成交量数据不存在")
    return transaction

@router.post("/", response_model=HouseTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_house_transaction(transaction_in: HouseTransactionCreate, db: Session = Depends(get_db)):
    """创建新的房产成交量数据"""
    return house_transaction.create(db, obj_in=transaction_in)

@router.put("/{transaction_id}", response_model=HouseTransactionResponse)
async def update_house_transaction(
    transaction_id: int, transaction_in: HouseTransactionUpdate, db: Session = Depends(get_db)
):
    """更新指定ID的房产成交量数据"""
    transaction = house_transaction.get(db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="房产成交量数据不存在")
    return house_transaction.update(db, db_obj=transaction, obj_in=transaction_in)

@router.delete("/{transaction_id}", response_model=HouseTransactionResponse)
async def delete_house_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """删除指定ID的房产成交量数据"""
    transaction = house_transaction.get(db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="房产成交量数据不存在")
    return house_transaction.remove(db, id=transaction_id)

@router.get("/by-city/{city}", response_model=HouseTransactionListResponse)
async def get_house_transactions_by_city(
    city: str, db: Session = Depends(get_db), skip: int = 0, limit: int = 100
):
    """获取指定城市的房产成交量数据"""
    transactions = house_transaction.get_by_city(db, city=city, skip=skip, limit=limit)
    total = house_transaction.count_by_city(db, city=city)
    return {"total": total, "items": transactions}