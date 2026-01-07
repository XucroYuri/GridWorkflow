import axios from 'axios';
import { supabase } from '../lib/supabase';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1', // 默认指向 /api/v1，通过 Vite 代理转发到后端
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// 请求拦截器
apiClient.interceptors.request.use(
  async (config) => {
    // 获取 Supabase session token
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data; // 直接返回 data 部分
  },
  (error) => {
    // 统一错误处理
    console.error('API Error:', error);
    if (error.response) {
      // 服务器返回了错误状态码
      switch (error.response.status) {
        case 401:
          // 未授权，重定向到登录页
          console.warn('Unauthorized, please login.');
          break;
        case 403:
          console.warn('Forbidden.');
          break;
        case 404:
          console.warn('Resource not found.');
          break;
        case 500:
          console.error('Server error.');
          break;
        default:
          console.error(`Error: ${error.response.status}`);
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('No response received:', error.request);
    } else {
      // 发送请求时出错
      console.error('Request setup error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;

