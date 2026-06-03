import http from "./http";

export function listParams(interfaceId: number) {
  return http.get(`/api/interfaces/${interfaceId}/params`);
}

export function saveParamsBatch(interfaceId: number, items: any[]) {
  return http.post(`/api/interfaces/${interfaceId}/params`, { items });
}

export function updateParam(paramId: number, data: any) {
  return http.put(`/api/params/${paramId}`, data);
}

export function deleteParam(paramId: number) {
  return http.delete(`/api/params/${paramId}`);
}

export function getQueryFormSchema(interfaceId: number) {
  return http.get(`/api/interfaces/${interfaceId}/query-form-schema`);
}

