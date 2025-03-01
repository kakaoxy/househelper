from pydantic import BaseModel
from typing import Optional, Dict, Any

class GeoJsonBase(BaseModel):
    name: str
    data: Dict[str, Any]

class GeoJsonCreate(GeoJsonBase):
    pass

class GeoJson(GeoJsonBase):
    id: int
    
    class Config:
        from_attributes = True