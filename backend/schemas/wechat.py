from pydantic import BaseModel
from typing import Optional, Dict

# 微信登录请求模型
class WechatLogin(BaseModel):
    code: str
    encrypted_data: Optional[str] = None
    iv: Optional[str] = None
    user_info: Optional[Dict] = None

# 微信用户创建模型
class WechatUserCreate(BaseModel):
    openid: str
    session_key: str
    phone: Optional[str] = None
    wechat_nickname: Optional[str] = None