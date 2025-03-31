import request from "~/utils/request";

export class Group {
    static getGroupNames() {
        return request({
            url: '/groupnames/',
            method: 'get',
        });
    }
}