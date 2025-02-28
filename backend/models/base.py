from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

# 角色-菜单关联表（多对多）
role_menu = Table(
    'role_menu',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('menu_id', Integer, ForeignKey('menus.id'), primary_key=True)
)

# 角色-API关联表（多对多）
role_api = Table(
    'role_api',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('api_id', Integer, ForeignKey('apis.id'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联角色（多对一）
    role_id = Column(Integer, ForeignKey('roles.id'))
    role = relationship("Role", back_populates="users")

class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联用户（一对多）
    users = relationship("User", back_populates="role")
    
    # 关联菜单（多对多）
    menus = relationship("Menu", secondary=role_menu, back_populates="roles")
    
    # 关联API（多对多）
    apis = relationship("API", secondary=role_api, back_populates="roles")

class Menu(Base):
    __tablename__ = 'menus'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    path = Column(String(100))
    component = Column(String(100))
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey('menus.id'), nullable=True)
    is_hidden = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 自引用关系（树形结构）
    parent = relationship("Menu", remote_side=[id], backref="children")
    
    # 关联角色（多对多）
    roles = relationship("Role", secondary=role_menu, back_populates="menus")

class API(Base):
    __tablename__ = 'apis'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    path = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE等
    description = Column(String(200))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联角色（多对多）
    roles = relationship("Role", secondary=role_api, back_populates="apis")