from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from datetime import date

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.base import Base

# 定义模型类型变量
ModelType = TypeVar("ModelType", bound=Base)
# 定义创建架构类型变量
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
# 定义更新架构类型变量
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# 通用CRUD操作基类
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD对象初始化，传入SQLAlchemy模型类
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        根据ID获取单个对象
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        获取多个对象，支持分页
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def get_count(self, db: Session) -> int:
        """
        获取对象总数
        """
        return db.query(func.count(self.model.id)).scalar()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        创建对象
        """
        obj_in_data = jsonable_encoder(obj_in)
        # 处理日期字段
        if 'transaction_date' in obj_in_data and isinstance(obj_in_data['transaction_date'], str):
            obj_in_data['transaction_date'] = date.fromisoformat(obj_in_data['transaction_date'])
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        更新对象
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        # 处理日期字段
        if 'transaction_date' in update_data and isinstance(update_data['transaction_date'], str):
            update_data['transaction_date'] = date.fromisoformat(update_data['transaction_date'])
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        删除对象
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
    
    def filter_by(self, db: Session, *, conditions: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        根据条件筛选对象
        """
        query = db.query(self.model)
        for field, value in conditions.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        return query.offset(skip).limit(limit).all()
    
    def count_by(self, db: Session, *, conditions: Dict[str, Any]) -> int:
        """
        根据条件统计对象数量
        """
        query = db.query(func.count(self.model.id))
        for field, value in conditions.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        return query.scalar()