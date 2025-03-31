import {createRouter, createWebHistory, RouterOptions} from "vue-router";
import Board from "~/views/Board.vue";
import Plan from "~/views/Plan.vue";
import Task from "~/views/Task.vue";
import Problem from "~/views/Problem.vue";
import {useAuthStore} from "~/store";
import {User} from "~/api/user";

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {path: '/board', component: Board},
        {path: '/plan', component: Plan},
        {path: '/task', component: Task},
        {path: '/problem', component: Problem},
        {path: '/:pathMatch(.*)*', component: Board},
    ]
} as RouterOptions);


router.beforeEach((to, from) => {
    const authStore = useAuthStore();
    if (authStore.user.token && authStore.user.name) {
        return true;
    } else {
        const authTicket = new URLSearchParams(location.search).get('AUTH_TICKET')
        if (authTicket) {
            //todo fake token
            // authStore.user.token = 'aaa';
            // authStore.user.name = 'nicolecheng';
            User.getUserInfo(authTicket)
                .then(resp => {
                    authStore.user.token = resp.data.password;
                    authStore.user.name = resp.data.username;
                    router.push('/')
                });
            return false;
        } else {
            User.doLogin();
            return false;
        }
    }
})

export default router;