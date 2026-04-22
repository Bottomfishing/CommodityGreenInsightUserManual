import { createApp } from 'vue'
import router from './router'
import App from './App.vue'
import DataV from '@kjgl77/datav-vue3'

const app = createApp(App)
app.use(router)
app.use(DataV)
app.mount('#app')
