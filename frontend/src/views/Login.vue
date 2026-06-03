<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2 class="title">数据查询系统</h2>
      <el-form :model="form" @submit.prevent="onSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="current-password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit" style="width: 100%">登录</el-button>
        </el-form-item>
      </el-form>
      <div class="hint">默认账号需在数据库 dq_user 表中预置。</div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/store/auth";

const router = useRouter();
const auth = useAuthStore();

const form = reactive({
  username: "",
  password: ""
});
const loading = ref(false);

async function onSubmit() {
  if (!form.username || !form.password) {
    ElMessage.error("请输入用户名和密码");
    return;
  }
  loading.value = true;
  try {
    await auth.login(form.username, form.password);
    ElMessage.success("登录成功");
    router.push({ name: "dashboard" });
  } catch (e: any) {
    ElMessage.error(e?.message || "登录失败");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}
.login-card {
  width: 360px;
}
.title {
  text-align: center;
  margin-bottom: 16px;
}
.hint {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}
</style>

