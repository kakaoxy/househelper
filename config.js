// API配置
export const API_CONFIG = {
    // 替换为实际的服务器IP地址
    BASE_URL: 'http://192.168.1.100:8000',
    API_PREFIX: '/api/v1',
    
    // API端点
    ENDPOINTS: {
        HOUSE_TRANSACTIONS: '/house-transactions/',
        // 在这里添加其他API端点
    }
};

// 获取完整的API URL
export const getApiUrl = (endpoint) => {
    return `${API_CONFIG.BASE_URL}${API_CONFIG.API_PREFIX}${endpoint}`;
};