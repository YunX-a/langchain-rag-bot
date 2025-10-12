import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';
import { ElNotification } from 'element-plus';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export const useAuthStore = defineStore('auth', () => {
    // 从 localStorage 初始化 token，实现持久化登录
    const token = ref<string | null>(localStorage.getItem('access_token'));

    // 计算属性，判断用户是否已登录
    const isLoggedIn = computed(() => !!token.value);

    // Action: 登录
    async function login(username: string, password: string): Promise<boolean> {
        // FastAPI 的 OAuth2PasswordRequestForm 需要 form-data 格式
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);

        try {
            const response = await axios.post(`${API_BASE_URL}/token`, params, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            });

            token.value = response.data.access_token;
            localStorage.setItem('access_token', token.value!);
            ElNotification({ title: '成功', message: '登录成功！', type: 'success' });
            return true;
        } catch (error) {
            console.error('登录失败:', error);
            ElNotification({ title: '错误', message: '用户名或密码不正确。', type: 'error' });
            return false;
        }
    }

    // Action: 登出
    function logout() {
        token.value = null;
        localStorage.removeItem('access_token');
        // 可以选择性地跳转到登录页
        // router.push('/login'); 
    }

    // Action: 注册
    async function register(username: string, password: string): Promise<boolean> {
        try {
            await axios.post(`${API_BASE_URL}/users/`, { username, password });
            ElNotification({ title: '成功', message: '注册成功，请登录！', type: 'success' });
            return true;
        } catch (error: any) {
            console.error('注册失败:', error);
            const detail = error.response?.data?.detail || '注册过程中发生未知错误。';
            ElNotification({ title: '错误', message: detail, type: 'error' });
            return false;
        }
    }

    return { token, isLoggedIn, login, logout, register };
});