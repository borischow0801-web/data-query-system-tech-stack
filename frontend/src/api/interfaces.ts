import http from "./http";

export function listInterfaces(params: {
  page?: number;
  pageSize?: number;
  interfaceCode?: string;
  interfaceName?: string;
  status?: number | null;
}) {
  return http.get("/api/interfaces", { params });
}

export function getInterfaceDetail(id: number) {
  return http.get(`/api/interfaces/${id}`);
}

export function createInterface(data: any) {
  return http.post("/api/interfaces", data);
}

export function updateInterface(id: number, data: any) {
  return http.put(`/api/interfaces/${id}`, data);
}

export function deleteInterface(id: number) {
  return http.delete(`/api/interfaces/${id}`);
}

export function testInterface(id: number) {
  return http.post(`/api/interfaces/${id}/test`);
}

export function getResultConfig(id: number) {
  return http.get(`/api/interfaces/${id}/result-config`);
}

export function updateResultConfig(id: number, resultConfig: any) {
  return http.put(`/api/interfaces/${id}/result-config`, { resultConfig });
}

