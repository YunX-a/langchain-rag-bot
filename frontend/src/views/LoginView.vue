<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { User, Lock } from '@element-plus/icons-vue';

const authStore = useAuthStore();

const activeTab = ref('login'); // 控制当前是登录还是注册
const form = ref({
  username: '',
  password: '',
});
const isLoading = ref(false);

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) return;
  isLoading.value = true;
  await authStore.login(form.value.username, form.value.password);
  isLoading.value = false;
};

const handleRegister = async () => {
  if (!form.value.username || !form.value.password) return;
  isLoading.value = true;
  const success = await authStore.register(form.value.username, form.value.password);
  if (success) {
    // 注册成功后自动切换到登录标签页
    activeTab.value = 'login';
  }
  isLoading.value = false;
};
</script>

<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <span>欢迎使用 RAG 问答平台</span>
        </div>
      </template>
      <el-tabs v-model="activeTab" class="login-tabs" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form :model="form" @submit.prevent="handleLogin">
            <el-form-item>
              <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password size="large" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleLogin" :loading="isLoading" style="width: 100%;" size="large">登 录</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="form" @submit.prevent="handleRegister">
            <el-form-item>
              <el-input v-model="form.username" placeholder="设置用户名 (至少3位)" :prefix-icon="User" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="form.password" type="password" placeholder="设置密码 (至少6位)" :prefix-icon="Lock" show-password size="large" />
            </el-form-item>
            <el-form-item>
              <el-button type="success" @click="handleRegister" :loading="isLoading" style="width: 100%;" size="large">注 册</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  background-color: #f0f2f5;
}

.login-card {
  width: 400px;
}

.card-header {
  text-align: center;
  font-size: 1.5rem;
  color: #303133;
}

.login-tabs {
  margin-top: 20px;
}
</style>