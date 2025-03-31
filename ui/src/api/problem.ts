import request from "~/utils/request";

export interface ProblemReq {
    group_id: number;
    plan_id: number;
    person_in_charge: string;
    fail_type: number;
    fail_reason: string;
    create_time__gte: number|null;
    create_time__lte: number|null;
    result: number;
    page: number;
    size: number;
}

export class Problem {
    static get(query: ProblemReq) {
        return request({
            url: '/problem/',
            method: 'get',
            params: query
        })
    }

    static put(id: number|string, bug_link: string) {
        return request({
            url: '/problem/' + id + "/",
            method: 'put',
            data: {"bug_link": bug_link}
        })
    }
}