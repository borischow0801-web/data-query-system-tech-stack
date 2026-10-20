import http from "./http";

export function executeQuery(payload: { interfaceCode: string; params: any; envCode?: string }) {
  return http.post("/api/query/execute", payload);
}

export function listQueryHistory(params: {
  page?: number;
  pageSize?: number;
  interfaceCode?: string;
  successFlag?: number | null;
  startTime?: string;
  endTime?: string;
}) {
  return http.get("/api/query/history", {
    params: {
      page: params.page,
      page_size: params.pageSize,
      interface_code: params.interfaceCode,
      success_flag: params.successFlag,
      start_time: params.startTime,
      end_time: params.endTime
    }
  });
}

export function getQueryHistoryDetail(id: number) {
  return http.get(`/api/query/history/${id}`);
}

/** 按当前结果配置回放结构化视图（表格/统计/详情块），不调用远程接口 */
export function getQueryHistoryStructuredView(id: number) {
  return http.get(`/api/query/history/${id}/structured-view`);
}

