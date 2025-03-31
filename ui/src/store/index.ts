import {createPinia, defineStore} from "pinia";
import piniaPluginPersistedState from 'pinia-plugin-persistedstate';
import {UserResp} from "~/api/user";
import {reactive, ref} from "vue";

const pinia = createPinia()
pinia.use(piniaPluginPersistedState)

export const useAppStore = defineStore('app',
    () => {
        const collapse = ref(false);
        const search_form = reactive({
            clicked: false,
            person_in_charge: '',
            plan_id: '',
            group_id: '',
            create_time: [],
            fail_type: 1,
            fail_reason: '',
        })

        function handleCollapse() {
            collapse.value = !collapse.value;
        }

        return {collapse, handleCollapse, search_form};
    },
    {
        persist: true,
    }
);

export const useAuthStore = defineStore('auth',
    () => {
        const user = reactive<UserResp>({
            token: '',
            name: ''
        } as UserResp);
        return {user};
    },
    {
        persist: true,
    }
);

export default pinia