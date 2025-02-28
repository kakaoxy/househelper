from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import date, datetime

# 房产成交量基础模式
class HouseTransactionBase(BaseModel):
    city: str
    transaction_date: date
    new_house_count: int = 0
    new_house_area: float = 0.0
    second_hand_count: int = 0
    second_hand_area: float = 0.0

# 创建房产成交量请求模式
class HouseTransactionCreate(HouseTransactionBase):
    @validator('transaction_date', pre=True)
    def validate_transaction_date(cls, v):
        if isinstance(v, str):
            try:
                d = date.fromisoformat(v)
                if d > date.today():
                    raise ValueError('不能使用未来日期')
                return d
            except ValueError as e:
                raise ValueError('无效的日期格式')
        return v

    @validator('new_house_count', 'second_hand_count')
    def validate_count(cls, v):
        if v < 0:
            raise ValueError('成交量不能为负数')
        return v

    @validator('new_house_area', 'second_hand_area')
    def validate_area(cls, v):
        if v < 0:
            raise ValueError('成交面积不能为负数')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "city": "北京",
                "transaction_date": "2024-01-15",
                "new_house_count": 100,
                "new_house_area": 10000.0,
                "second_hand_count": 50,
                "second_hand_area": 5000.0
            }
        }

# 更新房产成交量请求模式
class HouseTransactionUpdate(BaseModel):
    city: Optional[str] = None
    transaction_date: Optional[date] = None
    new_house_count: Optional[int] = None
    new_house_area: Optional[float] = None
    second_hand_count: Optional[int] = None
    second_hand_area: Optional[float] = None

    @validator('transaction_date', pre=True)
    def validate_transaction_date(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                d = date.fromisoformat(v)
                if d > date.today():
                    raise ValueError('不能使用未来日期')
                return d
            except ValueError as e:
                raise ValueError('无效的日期格式')
        return v

    @validator('new_house_count', 'second_hand_count')
    def validate_count(cls, v):
        if v is not None and v < 0:
            raise ValueError('成交量不能为负数')
        return v

    @validator('new_house_area', 'second_hand_area')
    def validate_area(cls, v):
        if v is not None and v < 0:
            raise ValueError('成交面积不能为负数')
        return v

# 房产成交量响应模式
class HouseTransactionResponse(HouseTransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 房产成交量列表响应模式
class HouseTransactionListResponse(BaseModel):
    total: int
    items: List[HouseTransactionResponse]

    class Config:
        from_attributes = True