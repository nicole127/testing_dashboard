import request from "~/utils/request";

export interface CaseReq {
    plan_record_id: number;
    fail_type: number;
    person_in_charge: string;
    page: number;
    size: number;
}

export interface CaseResp {
    id: number;
    fail_type: number;
    bug_link: string;
    fail_reason: string;
}

export class Case {
    static get(query: CaseReq) {
        return request({
            url: '/caserecord/',
            method: 'get',
            params: query
        })
    }

    static update(data: CaseResp) {
        return request({
            url: '/caserecord/' + data.id + "/",
            method: 'put',
            data: data
        })
    }
}