import http from "./http";

export interface LoginPayload {
  username: string;
  password: string;
}

export function loginApi(payload: LoginPayload): Promise<{ access_token: string; token_type: string }> {
  return http.post("/api/login", payload);
}

export function getMeApi(): Promise<any> {
  return http.get("/api/me");
}

