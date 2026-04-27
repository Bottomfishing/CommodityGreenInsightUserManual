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
  width: 100%;
  overflow-x: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #0a0f1a;
  color: #f1f5f9;
}
html,
body {
  scrollbar-gutter: stable;
}
html {
  height: 100%;
  overflow-y: auto;
}
body {
  min-height: 100%;
  height: auto;
  overflow-y: visible;
  overscroll-behavior-y: none;
}
#app {
  height: auto;
  min-height: 100vh;
  overflow: visible;
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
