<template>
  <router-view />
</template>

<script setup lang="ts">
// 根组件 - 仅渲染路由视图
</script>

<style>
/* 全局重置 */
*, *::before, *::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
html, body, #app {
  height: 100%;
  width: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #0a0f1a;
  color: #f1f5f9;
}

/* 滚动条美化 */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }
</style>
