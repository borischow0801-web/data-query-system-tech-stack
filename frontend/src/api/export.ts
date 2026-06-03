import http from "./http";

export function createExportTask(payload: { queryRecordId: number; exportType: "csv" | "xlsx" }) {
  return http.post("/api/export", payload);
}

export function getExportTask(taskId: string) {
  return http.get(`/api/export/${taskId}`);
}

