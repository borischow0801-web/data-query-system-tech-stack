import http from "./http";

export function createExportTask(payload: { queryRecordId: number; exportType: "csv" | "xlsx" }) {
  return http.post("/api/export", payload);
}

export function getExportTask(taskId: string) {
  return http.get(`/api/export/${taskId}`);
}

export async function downloadExportFile(fileUrl: string, fileName: string) {
  const blob = await http.get(fileUrl, { responseType: "blob" }) as unknown as Blob;
  if (blob.type.includes("application/json")) {
    const result = JSON.parse(await blob.text());
    throw new Error(result.message || "下载失败");
  }
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  try {
    link.click();
  } finally {
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

