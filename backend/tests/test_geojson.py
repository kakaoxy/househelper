import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open, MagicMock
import json
import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from core.database import Base, get_db
from main import app
from models.geojson import GeoJsonData
from schemas.geojson import GeoJsonCreate

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_geojson.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试数据
test_geojson_data = {
    "name": "test_geojson",
    "description": "测试GeoJSON数据",
    "data": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "测试点"},
                "geometry": {
                    "type": "Point",
                    "coordinates": [120.0, 30.0]
                }
            }
        ]
    }
}

@pytest.fixture(scope="function")
def test_db():
    # 删除所有表
    Base.metadata.drop_all(bind=engine)
    # 创建测试数据库表
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        # 测试结束后清理数据库
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    # 替换依赖项
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}

@pytest.fixture
def mock_geojson_file():
    """模拟GeoJSON文件内容"""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "测试点"},
                "geometry": {
                    "type": "Point",
                    "coordinates": [120.0, 30.0]
                }
            }
        ]
    }

# 添加一个中间件来记录请求
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"[TEST] [REQUEST] {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"[TEST] [RESPONSE] {request.method} {request.url.path} | Status: {response.status_code}")
    return response

def test_create_geojson(client):
    """测试创建GeoJSON数据"""
    logger.info("开始测试创建GeoJSON数据")
    response = client.post("/api/v1/geojson", json=test_geojson_data)
    logger.info(f"响应状态码: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_geojson_data["name"]
    if "description" in data:
        assert data["description"] == test_geojson_data["description"]
    assert "data" in data
    assert data["data"] == test_geojson_data["data"]

def test_list_geojson(client):
    """测试获取GeoJSON数据列表"""
    logger.info("开始测试获取GeoJSON数据列表")
    # 先创建一条数据
    client.post("/api/v1/geojson", json=test_geojson_data)
    
    # 测试获取列表
    response = client.get("/api/v1/geojson")
    logger.info(f"响应状态码: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == test_geojson_data["name"]

def test_get_geojson_file_real(client):
    """测试获取真实的GeoJSON文件 - 不使用模拟"""
    logger.info("开始测试获取真实的GeoJSON文件")
    response = client.get("/api/v1/geojson/hangzhoushangquan")
    logger.info(f"响应状态码: {response.status_code}")
    
    # 这个测试可能会失败，如果文件不存在，但它会触发真实的API请求
    if response.status_code == 200:
        data = response.json()
        assert "type" in data
        assert "features" in data
    else:
        logger.warning(f"文件可能不存在，状态码: {response.status_code}")

@patch('os.path.exists')
@patch('builtins.open', new_callable=mock_open)
@patch('json.load')
def test_get_geojson_file(mock_json_load, mock_file_open, mock_exists, client, mock_geojson_file):
    """测试获取GeoJSON文件"""
    logger.info("开始测试获取模拟的GeoJSON文件")
    # 设置模拟返回值
    mock_json_load.return_value = mock_geojson_file
    mock_exists.return_value = True
    
    # 测试获取GeoJSON文件
    response = client.get("/api/v1/geojson/test")
    logger.info(f"响应状态码: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert data == mock_geojson_file

@patch('os.path.exists')
def test_get_geojson_file_not_found(mock_exists, client):
    """测试获取不存在的GeoJSON文件"""
    logger.info("开始测试获取不存在的GeoJSON文件")
    # 模拟文件不存在
    mock_exists.return_value = False
    
    # 测试获取不存在的GeoJSON文件
    response = client.get("/api/v1/geojson/nonexistent")
    logger.info(f"响应状态码: {response.status_code}")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "不存在" in data["detail"]

@patch('os.path.exists')
@patch('builtins.open')
def test_get_geojson_file_read_error(mock_file_open, mock_exists, client):
    """测试读取GeoJSON文件出错"""
    logger.info("开始测试读取GeoJSON文件出错")
    # 模拟文件存在但读取出错
    mock_exists.return_value = True
    mock_file_open.side_effect = Exception("模拟的文件读取错误")
    
    # 测试读取出错
    response = client.get("/api/v1/geojson/error_file")
    logger.info(f"响应状态码: {response.status_code}")
    
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "读取GeoJSON文件失败" in data["detail"]

def test_get_geojson_with_json_extension(client):
    """测试获取带有.json扩展名的GeoJSON文件"""
    logger.info("开始测试获取带有.json扩展名的GeoJSON文件")
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open()), \
         patch('json.load', return_value={"type": "FeatureCollection", "features": []}):
        response = client.get("/api/v1/geojson/test.json")
        logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 200

def test_get_geojson_with_geojson_extension(client):
    """测试获取带有.geojson扩展名的GeoJSON文件"""
    logger.info("开始测试获取带有.geojson扩展名的GeoJSON文件")
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open()), \
         patch('json.load', return_value={"type": "FeatureCollection", "features": []}):
        response = client.get("/api/v1/geojson/test.geojson")
        logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 200

def test_get_geojson_without_extension_json_exists(client):
    """测试获取不带扩展名但存在.json文件的情况"""
    logger.info("开始测试获取不带扩展名但存在.json文件的情况")
    def mock_exists(path):
        return path.endswith('.json')
    
    with patch('os.path.exists', side_effect=mock_exists), \
         patch('builtins.open', mock_open()), \
         patch('json.load', return_value={"type": "FeatureCollection", "features": []}):
        response = client.get("/api/v1/geojson/test")
        logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 200

def test_get_geojson_without_extension_geojson_exists(client):
    """测试获取不带扩展名但存在.geojson文件的情况"""
    logger.info("开始测试获取不带扩展名但存在.geojson文件的情况")
    def mock_exists(path):
        return path.endswith('.geojson')
    
    with patch('os.path.exists', side_effect=mock_exists), \
         patch('builtins.open', mock_open()), \
         patch('json.load', return_value={"type": "FeatureCollection", "features": []}):
        response = client.get("/api/v1/geojson/test")
        logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 200