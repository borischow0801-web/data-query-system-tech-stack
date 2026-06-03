import axios from "axios";
import { useAuthStore } from "@/store/auth";

const apiBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || "";

const instance = axios.create({
  baseURL: apiBase,
  timeout: 10000
});

instance.interceptors.request.use((config) => {
  const auth = useAuthStore();
  if (auth.token) {
    config.headers = config.headers || {};
    (config.headers as any).Authorization = `Bearer ${auth.token}`;
  }
  return config;
});

instance.interceptors.response.use(
  (response) => {
    // 后端统一结构：{ success, code, message, traceId, data }
    const data = response.data;
    if (typeof data === "object" && data && "success" in data && data.success === false) {
      return Promise.reject(data);
    }
    const url = response.config.url || "";
    // 查询执行接口需要原始结构（包含 rawData、durationMs 等）
    if (url.endsWith("/api/query/execute")) {
      return data;
    }
    return data.data !== undefined ? data.data : data;
  },
  (error) => {
    // 让页面能看到“真实错误信息”，避免点了没反应
    const respData = error?.response?.data;
    if (respData && typeof respData === "object") {
      // 后端统一结构：{ success:false, code, message, traceId, data }
      if ("message" in respData) {
        return Promise.reject(respData);
      }
      return Promise.reject({ message: JSON.stringify(respData) });
    }
    if (error?.message) return Promise.reject({ message: error.message });
    return Promise.reject({ message: "网络或服务异常" });
  }
);

export default instance;

