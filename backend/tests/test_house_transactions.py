import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta

from core.database import Base, get_db
from main import app
from models.house_transaction import HouseTransaction
from models.base import *  # 导入所有基础模型

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 测试数据
test_date = date(2024, 1, 15)
test_transaction = {
    "city": "北京",
    "transaction_date": test_date.isoformat(),
    "new_house_count": 100,
    "new_house_area": 10000.0,
    "second_hand_count": 50,
    "second_hand_area": 5000.0
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
    yield TestClient(app)
    app.dependency_overrides = {}

def test_create_house_transaction(client):
    """测试创建房产成交量数据"""
    response = client.post("/api/v1/house-transactions/", json=test_transaction)
    assert response.status_code == 201
    data = response.json()
    assert data["city"] == test_transaction["city"]
    assert data["new_house_count"] == test_transaction["new_house_count"]
    assert data["new_house_area"] == test_transaction["new_house_area"]
    assert data["second_hand_count"] == test_transaction["second_hand_count"]
    assert data["second_hand_area"] == test_transaction["second_hand_area"]

def test_read_house_transactions(client):
    """测试获取房产成交量数据列表"""
    # 先创建一条数据
    client.post("/api/v1/house-transactions/", json=test_transaction)
    
    # 测试获取列表
    response = client.get("/api/v1/house-transactions/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) > 0

def test_read_house_transaction_by_id(client):
    """测试通过ID获取房产成交量数据"""
    # 先创建一条数据
    create_response = client.post("/api/v1/house-transactions/", json=test_transaction)
    transaction_id = create_response.json()["id"]
    
    # 测试获取详情
    response = client.get(f"/api/v1/house-transactions/{transaction_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == transaction_id
    assert data["city"] == test_transaction["city"]

def test_update_house_transaction(client):
    """测试更新房产成交量数据"""
    # 先创建一条数据
    create_response = client.post("/api/v1/house-transactions/", json=test_transaction)
    transaction_id = create_response.json()["id"]
    
    # 更新数据
    update_data = {
        "new_house_count": 150,
        "new_house_area": 15000.0,
        "second_hand_count": 75,
        "second_hand_area": 7500.0
    }
    response = client.put(f"/api/v1/house-transactions/{transaction_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["new_house_count"] == update_data["new_house_count"]
    assert data["new_house_area"] == update_data["new_house_area"]
    assert data["second_hand_count"] == update_data["second_hand_count"]
    assert data["second_hand_area"] == update_data["second_hand_area"]

def test_delete_house_transaction(client):
    """测试删除房产成交量数据"""
    # 先创建一条数据
    create_response = client.post("/api/v1/house-transactions/", json=test_transaction)
    transaction_id = create_response.json()["id"]
    
    # 测试删除
    response = client.delete(f"/api/v1/house-transactions/{transaction_id}")
    assert response.status_code == 200
    
    # 验证数据已被删除
    get_response = client.get(f"/api/v1/house-transactions/{transaction_id}")
    assert get_response.status_code == 404

def test_get_house_transactions_by_city(client):
    """测试按城市获取房产成交量数据"""
    # 创建测试数据
    client.post("/api/v1/house-transactions/", json=test_transaction)
    
    # 测试按城市筛选
    response = client.get(f"/api/v1/house-transactions/by-city/{test_transaction['city']}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) > 0
    assert all(item["city"] == test_transaction["city"] for item in data["items"])

def test_get_house_transactions_by_date_range(client):
    """测试按日期范围获取房产成交量数据"""
    # 创建测试数据
    client.post("/api/v1/house-transactions/", json=test_transaction)
    
    # 测试日期范围筛选
    start_date = (test_date - timedelta(days=1)).isoformat()
    end_date = (test_date + timedelta(days=1)).isoformat()
    response = client.get(f"/api/v1/house-transactions/?start_date={start_date}&end_date={end_date}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) > 0
    
    # 验证日期在范围内
    for item in data["items"]:
        transaction_date = date.fromisoformat(item["transaction_date"])
        assert date.fromisoformat(start_date) <= transaction_date <= date.fromisoformat(end_date)

def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_invalid_date_format(client):
    """测试无效的日期格式"""
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": "2024-13-45",  # 无效的日期格式
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

    invalid_data["transaction_date"] = "not-a-date"  # 非日期字符串
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422

def test_future_date(client):
    """测试未来日期"""
    future_data = {
        "city": test_transaction["city"],
        "transaction_date": "2025-12-31",  # 未来日期
        "new_house_count": test_transaction["new_house_count"],
        "new_house_area": test_transaction["new_house_area"],
        "second_hand_count": test_transaction["second_hand_count"],
        "second_hand_area": test_transaction["second_hand_area"]
    }
    response = client.post("/api/v1/house-transactions/", json=future_data)
    assert response.status_code == 422
def test_invalid_transaction_data(client):
    """测试无效的房产成交量数据"""
    # 测试缺少必要字段
    invalid_data = {"city": "北京"}
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422
    
    # 测试无效的数值
    invalid_data = {
        "city": test_transaction["city"],
        "transaction_date": test_transaction["transaction_date"],
        "new_house_count": -1,  # 新房成交量不能为负数
        "new_house_area": -100.0,  # 新房成交面积不能为负数
        "second_hand_count": -1,  # 二手房成交量不能为负数
        "second_hand_area": -100.0  # 二手房成交面积不能为负数
    }
    response = client.post("/api/v1/house-transactions/", json=invalid_data)
    assert response.status_code == 422