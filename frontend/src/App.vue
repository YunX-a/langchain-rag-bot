<script setup lang="ts">
import { ref, nextTick } from 'vue';
import axios from 'axios';
import { ElNotification } from 'element-plus';
import { Promotion, Loading } from '@element-plus/icons-vue';

// --- 响应式变量 ---
const userInput = ref('');
// 简化：不再需要 availableDocs 和 selectedDoc
const chatHistory = ref<{ role: 'user' | 'assistant'; content: string }[]>([]); 
const isLoading = ref(false);
const chatBoxRef = ref<HTMLElement | null>(null);

// --- API 地址配置 ---
// API 地址保持不变
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

// --- 删除了 onMounted，因为不再需要加载文档列表 ---
// 初始欢迎消息可以直接设置
chatHistory.value.push({ role: 'assistant', content: '你好！我是你的知识库问答助手，请直接输入问题开始对话。' });


// --- 核心函数：简化 sendMessage ---
const sendMessage = async () => {
  if (!userInput.value.trim()) {
    ElNotification({ title: '提示', message: '请输入问题！', type: 'warning' });
    return;
  }

  const userMessage = userInput.value;
  chatHistory.value.push({ role: 'user', content: userMessage });
  userInput.value = '';
  isLoading.value = true;
  
  await nextTick();
  if (chatBoxRef.value) {
    chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;
  }

  try {
    // --- 核心修改：请求体中只发送 question ---
    const response = await axios.post(`${API_BASE_URL}/query`, {
      question: userMessage, 
    });
    // -----------------------------------------

    chatHistory.value.push({ role: 'assistant', content: response.data.answer });
  } catch (error) {
    console.error('API call failed:', error);
    ElNotification({ title: '错误', message: '请求出错，请检查后端服务是否正常。', type: 'error' });
  } finally {
    isLoading.value = false;
    await nextTick();
    if (chatBoxRef.value) {
      chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;
    }
  }
};
</script>

<template>
  <el-container class="main-container">
    <el-header class="header">
      <h1>🤖 全局知识库问答机器人</h1>
    </el-header>

    <el-main class="chat-box" ref="chatBoxRef">
      <div v-for="(message, index) in chatHistory" :key="index" :class="['message-row', message.role]">
        <div class="message-bubble">
          <p v-html="message.content.replace(/\n/g, '<br/>')"></p>
        </div>
      </div>
      <div v-if="isLoading" class="message-row assistant">
         <div class="message-bubble loading-bubble">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在思考中...</span>
        </div>
      </div>
    </el-main>

    <el-footer class="input-area">
      <el-input
        v-model="userInput"
        @keyup.enter="sendMessage"
        placeholder="向全部已索引的文档提问..."
        size="large"
        :disabled="isLoading"
        clearable
      >
        <template #append>
          <el-button @click="sendMessage" :icon="Promotion" :loading="isLoading" type="primary" />
        </template>
      </el-input>
    </el-footer>
  </el-container>
</template>

<style>
  /* 样式可以保持不变 */
  html, body, #app { height: 100%; margin: 0; }
  .main-container { height: 100vh; }
  .header { text-align: center; background-color: #f5f7fa; line-height: 80px; border-bottom: 1px solid #e4e7ed; }
  .header h1 { margin: 0; color: #303133; }
  .chat-box { background-color: #f0f2f5; padding: 20px; overflow-y: auto; scroll-behavior: smooth; }
  .message-row { display: flex; margin-bottom: 20px; max-width: 70%; }
  .message-bubble { padding: 12px 18px; border-radius: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); line-height: 1.6; }
  .message-row.user { align-self: flex-end; }
  .message-row.user .message-bubble { background: linear-gradient(135deg, #409eff, #79bbff); color: white; }
  .message-row.assistant { align-self: flex-start; }
  .message-row.assistant .message-bubble { background-color: #ffffff; color: #303133; }
  .message-row p { margin: 0; white-space: pre-wrap; word-wrap: break-word; }
  .input-area { padding: 20px; background-color: #ffffff; border-top: 1px solid #e4e7ed; }
  .loading-bubble { display: flex; align-items: center; gap: 10px; }
</style>