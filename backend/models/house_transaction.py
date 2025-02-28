from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.base import Base

class HouseTransaction(Base):
    __tablename__ = 'house_transactions'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    city = Column(String(50), index=True, nullable=False)
    transaction_date = Column(Date, index=True, nullable=False)
    new_house_count = Column(Integer, default=0)
    new_house_area = Column(Float, default=0.0)
    second_hand_count = Column(Integer, default=0)
    second_hand_area = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    class Config:
        orm_mode = True