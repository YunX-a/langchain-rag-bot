// src/main.ts

import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

// --- 新增代码 ---
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// -----------------

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// --- 新增代码 ---
app.use(ElementPlus)
// -----------------

app.mount('#app')