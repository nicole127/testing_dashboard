import request from "~/utils/request";

export interface TaskReq {
    group_id: number;
    plan_id: number;
    user: string;
    create_time__gte: number|null;
    create_time__lte: number|null;
    result: number;
    page: number;
    size: number;
}

export class Task {
    static get(query: TaskReq) {
        return request({
            url: '/planrecord/',
            method: 'get',
            params: query
        })
    }

    static put(id: number, is_disable: number) {
        return request({
            url: '/planrecord/' + id + "/",
            method: 'put',
            data: {"is_disable": is_disable}
        })
    }
}