import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import './styles.css'

const app = createApp(App)

function showBootError(error: unknown) {
  const message = error instanceof Error ? error.stack || error.message : String(error)
  window.__showBootError?.(message)
}

app.config.errorHandler = (error) => {
  showBootError(error)
}

router.onError(showBootError)

window.addEventListener('unhandledrejection', (event) => {
  showBootError(event.reason)
})

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
document.documentElement.dataset.appMounted = 'true'
