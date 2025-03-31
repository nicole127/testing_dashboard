import request from "~/utils/request";

export interface PlanReq {
    group_id: number;
    id: number;
    person_in_charge: string;
    page: number;
    size: number;
}

export class Plan {
    static get(query: PlanReq) {
        return request({
            url: '/plan/',
            method: 'get',
            params: query
        });
    }

    static post(data: object) {
        return request({
            url: '/plan/',
            method: 'post',
            data: data
        });
    }

    static getPlanNames() {
        return request({
            url: '/plannames/',
            method: 'get',
        });
    }
}