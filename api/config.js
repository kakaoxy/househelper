// API基础配置
export const API_CONFIG = {
    // API服务器基础URL
    BASE_URL: 'http://192.168.100.198:8000',
    API_PREFIX: '/api/v1',
    
    // API端点
    ENDPOINTS: {
        // 房产交易相关
        HOUSE_TRANSACTIONS: '/house-transactions',
        
        // 用户相关
        USER_LOGIN: '/users/login',
        USER_REGISTER: '/users/register',
        USER_INFO: '/users/me',
        WECHAT_LOGIN: '/users/wxlogin',
        
        // 系统相关
        HEALTH_CHECK: '/health',
        SYSTEM_INFO: '/info'
    }
};

// 获取完整的API URL
export const getApiUrl = (endpoint) => {
    return `${API_CONFIG.BASE_URL}${API_CONFIG.API_PREFIX}${endpoint}`;
};

// 统一的请求方法
export const request = async ({
    endpoint,
    method = 'GET',
    data = null,
    params = null,
    headers = {}
}) => {
    try {
        const url = getApiUrl(endpoint);
        console.log(`[API请求] 开始请求: ${method} ${url}`);
        console.log('[API请求] 请求数据:', data);
        
        // 获取存储的token
        const token = uni.getStorageSync('househelper_token');
        
        const requestConfig = {
            url,
            method,
            header: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                ...headers
            }
        };
        
        // 添加请求体
        if (data) {
            requestConfig.data = data;
        }
        
        // 添加URL参数
        if (params) {
            const queryString = Object.keys(params)
                .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
                .join('&');
            requestConfig.url = `${url}?${queryString}`;
        }
        
        console.log('[API请求] 完整请求配置:', requestConfig);
        
        // 发送请求
        return new Promise((resolve, reject) => {
            uni.request({
                ...requestConfig,
                success: (res) => {
                    console.log(`[API响应] ${method} ${url} 状态码:`, res.statusCode);
                    console.log('[API响应] 响应数据:', res.data);
                    resolve(res);
                },
                fail: (err) => {
                    console.error(`[API错误] ${method} ${url} 请求失败:`, err);
                    reject(err);
                }
            });
        });
    } catch (error) {
        console.error('[API异常] 请求过程中发生异常:', error);
        return Promise.reject(error);
    }
};