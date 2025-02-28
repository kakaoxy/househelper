from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from core.crud import CRUDBase
from models.house_transaction import HouseTransaction
from schemas.house_transaction import HouseTransactionCreate, HouseTransactionUpdate

# 房产成交量数据CRUD操作类
class CRUDHouseTransaction(CRUDBase[HouseTransaction, HouseTransactionCreate, HouseTransactionUpdate]):
    def get_by_city(self, db: Session, *, city: str, skip: int = 0, limit: int = 100) -> List[HouseTransaction]:
        """
        根据城市获取房产成交量数据
        """
        return db.query(self.model).filter(self.model.city == city).offset(skip).limit(limit).all()
    
    def get_by_date_range(self, db: Session, *, city: Optional[str] = None, start_date: Any = None, end_date: Any = None, skip: int = 0, limit: int = 100) -> List[HouseTransaction]:
        """
        根据日期范围获取房产成交量数据
        """
        query = db.query(self.model)
        if city:
            query = query.filter(self.model.city == city)
        if start_date:
            query = query.filter(self.model.transaction_date >= start_date)
        if end_date:
            query = query.filter(self.model.transaction_date <= end_date)
        return query.offset(skip).limit(limit).all()
    
    def count_by_city(self, db: Session, *, city: str) -> int:
        """
        统计指定城市的房产成交量数据数量
        """
        return db.query(self.model).filter(self.model.city == city).count()

# 创建房产成交量数据CRUD实例
house_transaction = CRUDHouseTransaction(HouseTransaction)