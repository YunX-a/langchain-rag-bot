<script setup lang="ts">
import { ref, nextTick } from 'vue';
import { ElNotification } from 'element-plus';
import { Promotion, Loading, SwitchButton } from '@element-plus/icons-vue';
import { useAuthStore } from '@/stores/auth';

// --- 新增：获取 Auth Store ---
const authStore = useAuthStore();

// --- 接口和响应式变量 (与之前相同) ---
interface Source {
  metadata: Record<string, any>;
}
const chatHistory = ref<{ role: 'user' | 'assistant'; content: string; sources?: Source[] }[]>([]);
const userInput = ref('');
const isLoading = ref(false);
const chatBoxRef = ref<HTMLElement | null>(null);
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
chatHistory.value.push({ role: 'assistant', content: '你好！我是你的知识库问答助手，请直接输入问题开始对话。' });

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;

  const userMessage = userInput.value;
  chatHistory.value.push({ role: 'user', content: userMessage });
  userInput.value = '';
  isLoading.value = true;
  
  const assistantMessage = { role: 'assistant' as const, content: '', sources: [] as Source[] };
  chatHistory.value.push(assistantMessage);

  await nextTick();
  if (chatBoxRef.value) {
    chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;
  }

  try {
    // --- 核心修改：在请求头中加入 Authorization ---
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`;
    }
    // ------------------------------------------

    const response = await fetch(`${API_BASE_URL}/stream-query`, {
      method: 'POST',
      headers: headers, // 使用我们刚创建的带 token 的 headers
      body: JSON.stringify({ question: userMessage }),
    });

    if (!response.ok) {
      // 如果是因为 token 失效 (401), 提示并登出
      if (response.status === 401) {
        ElNotification({ title: '认证失败', message: '登录已过期，请重新登录。', type: 'error' });
        authStore.logout();
        return;
      }
      throw new Error(`网络响应错误: ${response.statusText}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let isReadingSources = false;
    
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      
      if (chunk.includes('---SOURCES---')) {
        isReadingSources = true;
        const parts = chunk.split('---SOURCES---');
        assistantMessage.content += parts[0];
        if (parts[1]) {
            try {
                const sourceData = JSON.parse(parts[1].trim());
                assistantMessage.sources.push({ metadata: sourceData });
            } catch (e) { /* 忽略 */ }
        }
        continue;
      }

      if (isReadingSources) {
        const lines = chunk.split('\n').filter(line => line.trim());
        for (const line of lines) {
            try {
                const sourceData = JSON.parse(line.trim());
                assistantMessage.sources.push({ metadata: sourceData });
            } catch (e) { /* 忽略 */ }
        }
      } else {
        assistantMessage.content += chunk;
      }

      await nextTick();
      if (chatBoxRef.value) {
        chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;
      }
    }

  } catch (error) {
    console.error('API 调用失败:', error);
    assistantMessage.content = '请求出错，请检查后端服务是否正常。';
    ElNotification({ title: '错误', message: '请求出错，请检查后端服务是否正常。', type: 'error' });
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <el-container class="main-container">
    <el-header class="header">
      <h1>🤖 全局知识库问答机器人</h1>
      <el-button 
        class="logout-button" 
        type="danger" 
        :icon="SwitchButton" 
        @click="authStore.logout" 
        circle 
      />
    </el-header>

    <el-main class="chat-box" ref="chatBoxRef">
      <div v-for="(message, index) in chatHistory" :key="index" :class="['message-row', message.role]">
        <div class="message-bubble">
          <p v-html="message.content.replace(/\n/g, '<br/>')"></p>
          <div v-if="message.sources && message.sources.length > 0" class="sources-container">
            <strong>来源:</strong>
            <ul>
              <li v-for="(source, sIndex) in message.sources" :key="sIndex">
                📄 {{ source.metadata.source || '未知来源' }} (页码: {{ source.metadata.page || 'N/A' }})
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div v-if="isLoading && chatHistory[chatHistory.length - 1]?.content === ''" class="message-row assistant">
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
  /* --- 样式基本都是从 App.vue 迁移过来的 --- */
  .main-container { height: 100vh; }
  .header { 
    display: flex;
    align-items: center;
    justify-content: center; /* 居中标题 */
    position: relative; /* 为了定位登出按钮 */
    background-color: #f5f7fa; 
    line-height: 60px; /* 调整高度 */
    border-bottom: 1px solid #e4e7ed; 
  }
  .header h1 { margin: 0; color: #303133; font-size: 1.5rem; }

  .logout-button {
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
  }
  
  .chat-box { background-color: #f0f2f5; padding: 20px; overflow-y: auto; scroll-behavior: smooth; }
  .message-row { display: flex; flex-direction: column; margin-bottom: 20px; }
  .message-bubble { padding: 12px 18px; border-radius: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); line-height: 1.6; max-width: 70%; }
  .message-row.user { align-items: flex-end; }
  .message-row.user .message-bubble { background: linear-gradient(135deg, #409eff, #79bbff); color: white; }
  .message-row.assistant { align-items: flex-start; }
  .message-row.assistant .message-bubble { background-color: #ffffff; color: #303133; }
  .message-row p { margin: 0; white-space: pre-wrap; word-wrap: break-word; }
  .input-area { padding: 20px; background-color: #ffffff; border-top: 1px solid #e4e7ed; display: flex; align-items: center; }
  .loading-bubble { display: flex; align-items: center; gap: 10px; }
  .sources-container {
    margin-top: 15px;
    padding-top: 10px;
    border-top: 1px solid #e4e7ed;
    font-size: 0.85rem;
    color: #555;
  }
  .sources-container strong { color: #333; }
  .sources-container ul { padding-left: 20px; margin: 5px 0 0; list-style-type: none; }
  .sources-container li { margin-bottom: 5px; position: relative; }
  .sources-container li::before { content: '📄'; position: absolute; left: -20px; }
</style>