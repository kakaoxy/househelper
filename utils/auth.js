// 微信登录和授权工具类
import { API_CONFIG, request, getApiUrl } from '@/api/config.js';

// 存储Token的键名
const TOKEN_KEY = 'househelper_token';
const USER_INFO_KEY = 'househelper_user_info';

/**
 * 检查用户是否已登录
 * @returns {Boolean} 是否已登录
 */
export const isLoggedIn = () => {
  const token = uni.getStorageSync(TOKEN_KEY);
  return !!token;
};

/**
 * 获取存储的Token
 * @returns {String} token字符串
 */
export const getToken = () => {
  return uni.getStorageSync(TOKEN_KEY);
};

/**
 * 保存Token到本地存储
 * @param {String} token - 授权令牌
 * @param {String} tokenType - 令牌类型
 */
export const saveToken = (token, tokenType = 'bearer') => {
  uni.setStorageSync(TOKEN_KEY, token);
};

/**
 * 清除Token和用户信息
 */
export const clearAuth = () => {
  uni.removeStorageSync(TOKEN_KEY);
  uni.removeStorageSync(USER_INFO_KEY);
};

/**
 * 保存用户信息
 * @param {Object} userInfo - 用户信息对象
 */
export const saveUserInfo = (userInfo) => {
  uni.setStorageSync(USER_INFO_KEY, userInfo);
};

/**
 * 获取用户信息
 * @returns {Object} 用户信息对象
 */
export const getUserInfo = () => {
  return uni.getStorageSync(USER_INFO_KEY) || {};
};

/**
 * 获取微信登录code
 * @returns {Promise} 登录code的Promise
 */
export const getWxLoginCode = () => {
  console.log('正在获取微信登录code...');
  return new Promise((resolve, reject) => {
    uni.login({
      provider: 'weixin',
      success: (loginRes) => {
        console.log('获取微信登录code成功:', loginRes);
        if (loginRes.code) {
          resolve(loginRes.code);
        } else {
          console.error('获取微信登录code失败:', loginRes);
          reject(new Error('获取微信登录code失败'));
        }
      },
      fail: (err) => {
        console.error('微信登录失败:', err);
        reject(err);
      }
    });
  });
};

/**
 * 使用code和用户信息完成登录
 * @param {String} code - 微信登录code
 * @param {Object} userInfo - 用户信息
 * @returns {Promise} 登录结果Promise
 */
export const loginWithCodeAndUserInfo = async (code, userInfo) => {
  try {
    console.log('正在请求后端登录接口...');
    console.log('请求数据:', {
      code: code,
      user_info: userInfo
    });
    
    const response = await request({
      endpoint: '/users/wxlogin',
      method: 'POST',
      data: {
        code: code,
        user_info: userInfo
      }
    });
    
    console.log('后端登录接口响应:', response);
    
    if (response.statusCode === 200) {
      // 保存token和用户信息
      console.log('登录成功，保存token');
      saveToken(response.data.access_token);
      saveUserInfo(userInfo);
      return response.data;
    } else {
      // 获取详细错误信息
      const errorMsg = response.data && response.data.detail 
        ? response.data.detail 
        : '微信登录失败，请检查网络或联系管理员';
      console.error('微信登录错误:', errorMsg, '完整响应:', response);
      throw new Error(errorMsg);
    }
  } catch (error) {
    console.error('微信登录过程中发生异常:', error);
    throw error;
  }
};

/**
 * 微信登录流程
 * @returns {Promise} 登录结果Promise
 */
export const wxLogin = () => {
  console.log('开始微信登录流程');
  return new Promise((resolve, reject) => {
    // 先获取登录code
    getWxLoginCode()
      .then(code => {
        // 显示获取用户信息的提示，引导用户点击
        uni.showModal({
          title: '授权提示',
          content: '需要获取您的用户信息以完成登录',
          confirmText: '确认授权',
          cancelText: '取消',
          success: (res) => {
            if (res.confirm) {
              // 用户点击确认，此时调用getUserProfile
              getUserProfile()
                .then(userInfoRes => {
                  // 获取到用户信息后，完成登录流程
                  loginWithCodeAndUserInfo(code, userInfoRes.userInfo)
                    .then(data => resolve(data))
                    .catch(err => reject(err));
                })
                .catch(err => {
                  console.error('获取用户信息失败:', err);
                  reject(err);
                });
            } else {
              // 用户取消授权
              reject(new Error('用户取消授权'));
            }
          }
        });
      })
      .catch(err => reject(err));
  });
};

/**
 * 获取用户信息（头像、昵称等）
 * @returns {Promise} 用户信息Promise
 */
export const getUserProfile = () => {
  console.log('开始获取用户信息');
  return new Promise((resolve, reject) => {
    uni.getUserProfile({
      desc: '用于完善用户资料',
      success: (res) => {
        console.log('获取用户信息成功:', res);
        resolve(res);
      },
      fail: (err) => {
        console.error('获取用户信息失败:', err);
        reject(err);
      }
    });
  });
};

/**
 * 获取用户手机号
 * @returns {Promise} 手机号信息Promise
 */
export const getPhoneNumber = (e) => {
  return new Promise(async (resolve, reject) => {
    if (e.detail.errMsg === 'getPhoneNumber:ok') {
      try {
        // 获取登录code
        const loginRes = await new Promise((res, rej) => {
          uni.login({
            provider: 'weixin',
            success: res,
            fail: rej
          });
        });
        
        // 请求后端接口解密手机号
        const response = await request({
          endpoint: '/users/wxlogin',
          method: 'POST',
          data: {
            code: loginRes.code,
            encrypted_data: e.detail.encryptedData,
            iv: e.detail.iv
          }
        });
        
        if (response.statusCode === 200) {
          // 保存token
          saveToken(response.data.access_token);
          resolve(response.data);
        } else {
          reject(new Error('获取手机号失败'));
        }
      } catch (error) {
        reject(error);
      }
    } else {
      reject(new Error('用户拒绝授权手机号'));
    }
  });
};

/**
 * 检查登录状态并执行操作
 * @param {Function} callback - 登录成功后的回调函数
 * @param {Boolean} showToast - 是否显示提示
 * @returns {Promise}
 */
export const checkLogin = async (callback, showToast = true) => {
  if (isLoggedIn()) {
    // 已登录，直接执行回调
    if (typeof callback === 'function') {
      return callback();
    }
    return Promise.resolve();
  } else {
    // 未登录，提示用户登录
    if (showToast) {
      uni.showModal({
        title: '提示',
        content: '请先登录',
        confirmText: '去登录',
        success: (res) => {
          if (res.confirm) {
            // 执行微信登录
            wxLogin().then(() => {
              if (typeof callback === 'function') {
                callback();
              }
            }).catch(err => {
              uni.showToast({
                title: '登录失败',
                icon: 'none'
              });
            });
          }
        }
      });
    } else {
      try {
        await wxLogin();
        if (typeof callback === 'function') {
          return callback();
        }
        return Promise.resolve();
      } catch (error) {
        return Promise.reject(error);
      }
    }
  }
};