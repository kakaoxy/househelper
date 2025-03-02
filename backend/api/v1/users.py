from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
import bcrypt
from wechatpy.client import WeChatClient
from wechatpy.exceptions import WeChatClientException

from core.database import get_db
from core.config import settings
from models.base import User
from schemas.user import UserCreate, UserUpdate, UserResponse, Token, UserLogin
from schemas.wechat import WechatLogin, WechatUserCreate
from core.logging import logger

router = APIRouter(prefix="/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/login")

# 密码哈希处理
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

# 创建访问令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# 获取当前用户
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的身份验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# 获取当前活跃用户
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user

# 用户注册
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已被注册")
    
    # 检查邮箱是否已存在
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        role_id=user.role_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 用户登录
@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 微信登录
@router.post("/wxlogin", response_model=Token)
async def wechat_login(
    wechat_data: WechatLogin,
    db: Session = Depends(get_db)
):
    # 检查微信配置是否有效
    logger.info(f"微信登录请求开始处理，接收到的数据: {wechat_data}")
    if not settings.WECHAT_APPID or settings.WECHAT_APPID == "your_appid_here" or \
       not settings.WECHAT_SECRET or settings.WECHAT_SECRET == "your_secret_here":
        logger.error("微信小程序配置无效，WECHAT_APPID或WECHAT_SECRET未正确设置")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="微信小程序配置无效，请检查WECHAT_APPID和WECHAT_SECRET环境变量"
        )
        
    try:
        # 1. 获取session_key和openid
        logger.info(f"开始调用微信API获取session_key和openid，code: {wechat_data.code}")
        client = WeChatClient(settings.WECHAT_APPID, settings.WECHAT_SECRET)
        session_info = client.wxa.code_to_session(wechat_data.code)
        logger.info(f"微信API返回session信息: {session_info}")
        
        # 2. 解密手机号（如果提供了加密数据）
        phone_info = None
        if wechat_data.encrypted_data and wechat_data.iv:
            logger.info("尝试解密手机号信息")
            try:
                phone_info = client.wxa.decrypt_encrypted_data(
                    session_info['session_key'],
                    wechat_data.encrypted_data,
                    wechat_data.iv
                )
                logger.info(f"手机号解密成功: {phone_info}")
            except Exception as e:
                # 解密失败不阻止登录流程，但记录错误
                logger.error(f"手机号解密失败: {str(e)}")
        
        # 3. 创建/更新用户
        user = db.query(User).filter(User.openid == session_info['openid']).first()
        if not user:
            # 创建新用户
            logger.info(f"未找到现有用户，创建新用户，openid: {session_info['openid']}")
            user = User(
                openid=session_info['openid'],
                session_key=session_info['session_key'],
                phone=phone_info['purePhoneNumber'] if phone_info else None,
                wechat_nickname=wechat_data.user_info.get('nickName') if wechat_data.user_info else None
            )
            db.add(user)
        else:
            # 更新现有用户
            logger.info(f"找到现有用户，更新用户信息，用户ID: {user.id}")
            user.session_key = session_info['session_key']
            if phone_info:
                user.phone = phone_info['purePhoneNumber']
            if wechat_data.user_info and wechat_data.user_info.get('nickName'):
                user.wechat_nickname = wechat_data.user_info.get('nickName')
        
        db.commit()
        db.refresh(user)
        logger.info(f"用户数据保存成功，用户ID: {user.id}")
        
        # 4. 生成令牌
        access_token = create_access_token(
            data={"sub": user.openid, "user_id": user.id}
        )
        logger.info("令牌生成成功，登录完成")
        
        return {"access_token": access_token, "token_type": "bearer"}
    except WeChatClientException as e:
        logger.error(f"微信API调用失败: {str(e)}，错误详情: {e.__dict__}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"微信API调用失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"微信登录过程中发生异常: {str(e)}，异常类型: {type(e).__name__}")
        import traceback
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"微信登录失败: {str(e)}"
        )

# 获取当前用户信息
@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# 获取所有用户
@router.get("/", response_model=List[UserResponse])
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # 检查是否为超级用户
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="没有足够的权限")
    
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# 获取指定用户
@router.get("/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # 检查是否为超级用户或者是用户本人
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="没有足够的权限")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

# 更新用户
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # 检查是否为超级用户或者是用户本人
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="没有足够的权限")
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户信息
    update_data = user_update.dict(exclude_unset=True)
    
    # 如果更新密码，需要哈希处理
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # 非超级用户不能修改自己的超级用户状态
    if not current_user.is_superuser and "is_superuser" in update_data:
        del update_data["is_superuser"]
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

# 删除用户
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # 只有超级用户可以删除用户
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="没有足够的权限")
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    db.delete(db_user)
    db.commit()
    return None