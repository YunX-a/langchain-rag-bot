<script setup>
import { ref, onMounted, nextTick } from 'vue';
import axios from 'axios';
import { ElNotification } from 'element-plus'; // 引入漂亮的通知组件
import { Promotion } from '@element-plus/icons-vue'; // 引入一个图标

// --- 响应式变量 ---
const userInput = ref('');
const chatHistory = ref([]);
const isLoading = ref(false);
const availableDocs = ref([]);
const selectedDoc = ref('');
const chatBoxRef = ref(null); // 用于控制滚动条

// --- API 地址配置 ---
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

// --- 生命周期钩子 ---
onMounted(async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/documents`);
    availableDocs.value = response.data.documents;
    if (availableDocs.value.length > 0) {
      selectedDoc.value = availableDocs.value[0];
    }
    chatHistory.value.push({ role: 'assistant', content: '你好！我是你的文档问答助手，请从下拉框选择一个文档开始提问吧！' });
  } catch (error) {
    ElNotification({ title: '错误', message: '无法连接到服务器获取文档列表。', type: 'error' });
  }
});

// --- 核心函数 ---
const sendMessage = async () => {
  if (!userInput.value.trim() || !selectedDoc.value) {
    ElNotification({ title: '提示', message: '请输入问题，并选择一个文档！', type: 'warning' });
    return;
  }

  const userMessage = userInput.value;
  chatHistory.value.push({ role: 'user', content: userMessage });
  userInput.value = '';
  isLoading.value = true;

  // 自动滚动到底部
  await nextTick();
  chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;

  try {
    const response = await axios.post(`${API_BASE_URL}/query`, {
      question: userMessage,
      file_path: `data/${selectedDoc.value}`
    });
    chatHistory.value.push({ role: 'assistant', content: response.data.answer });
  } catch (error) {
    ElNotification({ title: '错误', message: '请求出错，请检查后端服务是否正常。', type: 'error' });
  } finally {
    isLoading.value = false;
    // 再次自动滚动到底部
    await nextTick();
    chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;
  }
};
</script>

<template>
  <el-container class="main-container">
    <el-header class="header">
      <h1>🤖 文档问答机器人</h1>
      <div class="doc-selector">
        <el-select v-model="selectedDoc" placeholder="请选择知识库" size="large">
          <el-option
            v-for="doc in availableDocs"
            :key="doc"
            :label="doc"
            :value="doc"
          />
        </el-select>
      </div>
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
        placeholder="在这里输入你的问题..."
        size="large"
        :disabled="isLoading"
      >
        <template #append>
          <el-button @click="sendMessage" :icon="Promotion" :loading="isLoading" type="primary" />
        </template>
      </el-input>
    </el-footer>
  </el-container>
</template>

<style>
  /* Element Plus 会提供大部分样式，我们只需要做一些布局和微调 */
  html, body, #app { height: 100%; margin: 0; }
  .main-container { height: 100vh; }
  .header { text-align: center; background-color: #f5f7fa; line-height: 60px; padding-top:10px; }
  .header h1 { margin: 0; }
  .doc-selector { margin-top: 10px; }
  .chat-box { background-color: #f0f2f5; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; }
  .message-row { display: flex; margin-bottom: 20px; max-width: 70%; }
  .message-bubble { padding: 10px 15px; border-radius: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .message-row.user { align-self: flex-end; }
  .message-row.user .message-bubble { background-color: #409eff; color: white; }
  .message-row.assistant { align-self: flex-start; }
  .message-row.assistant .message-bubble { background-color: #ffffff; color: #303133; }
  .message-row p { margin: 0; white-space: pre-wrap; word-wrap: break-word; line-height: 1.6; }
  .input-area { padding: 20px; background-color: #ffffff; }
  .loading-bubble { display: flex; align-items: center; gap: 10px; }
</style>