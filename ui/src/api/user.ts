import request from "~/utils/request";
import {useAuthStore} from "~/store";

export interface UserResp {
    token: string;
    name: string;
}

export class User {
    static doLogin() {
        const authStore = useAuthStore();
        authStore.user.token = '';
        authStore.user.name = '';
        window.location.href = import.meta.env.VITE_LOGIN_URL + encodeURIComponent(import.meta.env.VITE_FRONTEND_URL)
    }

    static getUserInfo(authTicket: string) {
        return request({
            url: '/login/',
            method: 'post',
            data: {
                AUTH_TICKET: authTicket,
                AUTH_DOMAIN: import.meta.env.VITE_FRONTEND_DOMAIN,
            }
        })
    }

    static getUsers() {
        return request({
            url: '/users/',
            method: 'get',
        });
    }
}




