// API基础配置
export const API_CONFIG = {
    // API服务器基础URL
    BASE_URL: 'http://localhost:8000',
    API_PREFIX: '/api/v1',
    
    // API端点
    ENDPOINTS: {
        // 房产交易相关
        HOUSE_TRANSACTIONS: '/house-transactions',
        
        // 用户相关
        USER_LOGIN: '/users/login',
        USER_REGISTER: '/users/register',
        USER_INFO: '/users/me',
        
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
        const requestConfig = {
            url,
            method,
            header: {
                'Content-Type': 'application/json',
                ...headers
            }
        };

        // 添加请求体
        if (data) {
            requestConfig.data = data;
        }

        // 添加查询参数
        if (params) {
            const queryString = Object.entries(params)
                .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
                .join('&');
            requestConfig.url += `?${queryString}`;
        }

        const response = await uni.request(requestConfig);
        return response;
    } catch (error) {
        console.error('API请求错误:', error);
        throw error;
    }
};