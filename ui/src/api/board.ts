import request from "~/utils/request";

export interface BoardReq {
    plan_ids: number[];
    start_time: number;
    end_time: number;
    group_ids: number[];
}

export interface BoardResp {
    summary: BoardSummary;
    x_data: string[];
    y_data: BoardData[];
}

export interface BoardSummary {
    total_bug_quantity: number;
    total_case_pass_percent: number;
    total_case_records_count: number;
    total_plan_records_duration: number;
}

export interface BoardData {
    id: number;
    name: string;
    bug_quantity: number[];
    code_bug_quantity: number[];
    environment_bug_quantity: number[];
    case_bug_quantity: number[];
    platform_bug_quantity: number[];
    default_bug_quantity: number[];
    plan_records_duration: number[];
    case_records_count: number[];
    case_pass_percent: number[];
    plan_execution_count: number[];
}

export class Board {
    static get(query: BoardReq) {
        return request({
            url: '/board/',
            method: 'get',
            params: query
        })
    }
}