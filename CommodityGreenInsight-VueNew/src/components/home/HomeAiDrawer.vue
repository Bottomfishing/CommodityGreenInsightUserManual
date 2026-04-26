<template>
  <Teleport to="body">
    <div v-if="open" class="ai-chat-overlay" @click.self="emit('update:open', false)">
      <aside class="ai-chat-drawer">
        <div class="ai-chat-inner">
          <div class="ai-chat-head">
            <div>
              <h3>新手助手小绿</h3>
              <p>可结合当前 Run 上下文进行问答与分析</p>
            </div>
            <button class="feature-btn" @click="emit('update:open', false)">关闭</button>
          </div>
          <div ref="messagesRef" class="ai-chat-messages">
            <div
              v-for="(msg, idx) in messages"
              :key="idx"
              class="ai-msg"
              :class="msg.role === 'user' ? 'ai-msg--user' : 'ai-msg--bot'"
            >
              {{ msg.content }}
            </div>
            <div v-if="loading" class="ai-msg ai-msg--bot">思考中...</div>
          </div>
          <div class="ai-chat-input-row">
            <input
              :value="input"
              type="text"
              placeholder="例如：请总结本次训练的主要结论"
              @input="onInput"
              @keydown.enter="emit('send')"
            />
            <button
              class="feature-btn feature-btn--primary"
              :disabled="loading || !input.trim()"
              @click="emit('send')"
            >
              发送
            </button>
          </div>
        </div>
      </aside>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";

type Message = { role: "user" | "bot"; content: string };

const props = defineProps<{
  open: boolean;
  loading: boolean;
  input: string;
  messages: Message[];
}>();

const emit = defineEmits<{
  (e: "update:open", value: boolean): void;
  (e: "update:input", value: string): void;
  (e: "send"): void;
}>();

const messagesRef = ref<HTMLDivElement | null>(null);

function onInput(event: Event) {
  const target = event.target as HTMLInputElement;
  emit("update:input", target.value);
}

async function scrollToBottom() {
  await nextTick();
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
  }
}

watch(
  () => [props.messages.length, props.loading, props.open],
  () => {
    if (props.open) scrollToBottom();
  },
);
</script>

<style scoped>
.ai-chat-overlay {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.45);
  backdrop-filter: blur(2px);
  z-index: 1200;
  display: flex;
  justify-content: flex-end;
}
.ai-chat-drawer {
  width: min(460px, 92vw);
  height: 100%;
  border-left: 1px solid rgba(56, 189, 248, 0.24);
  background:
    linear-gradient(180deg, rgba(3, 10, 24, 0.96), rgba(2, 8, 20, 0.98)),
    radial-gradient(circle at 80% 10%, rgba(56, 189, 248, 0.12), transparent 40%);
  box-shadow: -10px 0 30px rgba(2, 6, 23, 0.55);
}
.ai-chat-inner {
  height: 100%;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ai-chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.ai-chat-head h3 {
  margin: 0;
  font-size: 16px;
  color: #e2e8f0;
}
.ai-chat-head p {
  margin: 2px 0 0;
  font-size: 12px;
  color: rgba(148, 163, 184, 0.8);
}
.ai-chat-messages {
  flex: 1;
  min-height: 220px;
  max-height: none;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 2px;
}
.ai-msg {
  max-width: 85%;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
}
.ai-msg--bot {
  align-self: flex-start;
  background: rgba(30, 41, 59, 0.75);
  border: 1px solid rgba(56, 189, 248, 0.24);
  color: #dbeafe;
}
.ai-msg--user {
  align-self: flex-end;
  background: rgba(59, 130, 246, 0.24);
  border: 1px solid rgba(96, 165, 250, 0.4);
  color: #eff6ff;
}
.ai-chat-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ai-chat-input-row input {
  flex: 1;
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 8px;
  background: rgba(4, 16, 38, 0.72);
  color: #e0f2fe;
  padding: 9px 10px;
  min-width: 0;
  transition: all 0.2s;
}
.ai-chat-input-row input:focus {
  outline: none;
  border-color: rgba(34, 211, 238, 0.7);
  box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.12);
}
.feature-btn {
  border: 1px solid rgba(56, 189, 248, 0.28);
  background: rgba(7, 25, 52, 0.68);
  color: #bae6fd;
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.feature-btn:hover {
  border-color: rgba(34, 211, 238, 0.55);
  color: #e0f2fe;
}
.feature-btn--primary {
  border-color: rgba(34, 211, 238, 0.55);
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.62), rgba(37, 99, 235, 0.55));
  color: #ecfeff;
}
.feature-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
