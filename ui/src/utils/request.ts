import axios, {CreateAxiosDefaults} from "axios";
import {useAuthStore} from "~/store";
import {User} from "~/api/user";
import { ElMessage } from 'element-plus';

const request = axios.create({
    baseURL: import.meta.env.VITE_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    }
} as CreateAxiosDefaults)

// 添加请求拦截器
request.interceptors.request.use(
    config => {
        const authStore = useAuthStore();
        if (authStore.user.token || config.url == '/login/') {
            config.headers['authorization'] = authStore.user.token
        } else {
            User.doLogin();
        }
        return config;
    },
    error => {
        console.log(error);
        return Promise.reject(error);
    });

// 添加响应拦截器
request.interceptors.response.use(
    response => {
        return response;
    },
    error => {
        if (error.response) {
            const status = error.response.status;
            if(status == 401 && error.response.url != '/login/') {
                User.doLogin();
            } else if (status == 404){

            } else {
                ElMessage.error('出错了')
            }
        }
        return Promise.reject(error)
    });

export default request