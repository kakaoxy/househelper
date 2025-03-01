from sqlalchemy import Column, Integer, String, JSON
from core.database import Base

class GeoJsonData(Base):
    __tablename__ = "geojson_data"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)  # 数据集名称
    data = Column(JSON)  # GeoJSON 数据