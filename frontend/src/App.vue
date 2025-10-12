<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import ChatView from '@/views/ChatView.vue';
import LoginView from '@/views/LoginView.vue';

const authStore = useAuthStore();
</script>

<template>
  <div id="app-container">
    <ChatView v-if="authStore.isLoggedIn" />
    <LoginView v-else />
  </div>
</template>

<style>
/* 这里的样式是全局的，确保应用占满整个屏幕 */
html, body, #app, #app-container {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
</style>