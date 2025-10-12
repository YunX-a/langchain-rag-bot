<script setup lang="ts">
import { ref, nextTick } from 'vue';
import { ElNotification } from 'element-plus';
import { Promotion, Loading } from '@element-plus/icons-vue';

interface Source {
  metadata: Record<string, any>;
}
const chatHistory = ref<{ role: 'user' | 'assistant'; content: string; sources?: Source[] }[]>([]);
const userInput = ref('');
const isLoading = ref(false);
const chatBoxRef = ref<HTMLElement | null>(null);
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
chatHistory.value.push({ role: 'assistant', content: '你好！我是你的知识库问答助手，请直接输入问题开始对话。' });

/**
 * 发送消息并处理流式响应的核心函数
 */
const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;

  const userMessage = userInput.value;
  chatHistory.value.push({ role: 'user', content: userMessage });
  userInput.value = '';
  isLoading.value = true;
  
  // --- 核心修改点 1：先创建对象，再 push ---
  // 创建一个对助手消息的直接引用，而不是通过索引
  const assistantMessage = { role: 'assistant' as const, content: '', sources: [] as Source[] };
  chatHistory.value.push(assistantMessage);
  // ------------------------------------

  await nextTick();
  if (chatBoxRef.value) {
    chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/stream-query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: userMessage }),
    });

    if (!response.body) {
      throw new Error('响应体为空');
    }
    const reader = response.body.getReader();
    // --- 核心修改点 2：我们已经在上面检查了 response.body，所以 reader 不会是 undefined ---

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
        // --- 核心修改点 3：直接操作 assistantMessage 对象 ---
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
                 // --- 核心修改点 3：直接操作 assistantMessage 对象 ---
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
    // --- 核心修改点 3：直接操作 assistantMessage 对象 ---
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
  /* 全局样式 */
  html, body, #app { height: 100%; margin: 0; }
  .main-container { height: 100vh; }
  .header { text-align: center; background-color: #f5f7fa; line-height: 80px; border-bottom: 1px solid #e4e7ed; }
  .header h1 { margin: 0; color: #303133; }
  
  /* 聊天框样式 */
  .chat-box { background-color: #f0f2f5; padding: 20px; overflow-y: auto; scroll-behavior: smooth; }
  
  /* 消息行样式 */
  .message-row { display: flex; flex-direction: column; margin-bottom: 20px; }
  .message-bubble { padding: 12px 18px; border-radius: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); line-height: 1.6; max-width: 70%; }
  
  /* 用户消息样式 */
  .message-row.user { align-items: flex-end; }
  .message-row.user .message-bubble { background: linear-gradient(135deg, #409eff, #79bbff); color: white; }
  
  /* 助手消息样式 */
  .message-row.assistant { align-items: flex-start; }
  .message-row.assistant .message-bubble { background-color: #ffffff; color: #303133; }
  .message-row p { margin: 0; white-space: pre-wrap; word-wrap: break-word; }
  
  /* 输入区域样式 */
  .input-area { padding: 20px; background-color: #ffffff; border-top: 1px solid #e4e7ed; display: flex; align-items: center; }

  /* 加载中气泡样式 */
  .loading-bubble { display: flex; align-items: center; gap: 10px; }

  /* 来源信息样式 */
  .sources-container {
    margin-top: 15px;
    padding-top: 10px;
    border-top: 1px solid #e4e7ed;
    font-size: 0.85rem;
    color: #555;
  }
  .sources-container strong {
    color: #333;
  }
  .sources-container ul {
    padding-left: 20px;
    margin: 5px 0 0;
    list-style-type: none; /* 移除默认的点 */
  }
  .sources-container li {
    margin-bottom: 5px;
    position: relative;
  }
  /* 自定义列表符号 */
  .sources-container li::before {
    content: '📄';
    position: absolute;
    left: -20px;
  }

</style>