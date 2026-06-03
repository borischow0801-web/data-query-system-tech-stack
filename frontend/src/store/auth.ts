import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { loginApi, getMeApi } from "@/api/auth";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("token"));
  const user = ref<any | null>(null);

  const isAuthenticated = computed(() => !!token.value);

  async function login(username: string, password: string) {
    const res = await loginApi({ username, password });
    token.value = res.access_token;
    localStorage.setItem("token", res.access_token);
    await fetchMe();
  }

  async function fetchMe() {
    if (!token.value) return;
    user.value = await getMeApi();
  }

  function logout() {
    token.value = null;
    user.value = null;
    localStorage.removeItem("token");
  }

  return { token, user, isAuthenticated, login, fetchMe, logout };
});

