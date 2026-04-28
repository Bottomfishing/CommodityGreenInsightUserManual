<template>
  <div ref="hostRef" class="react-globe-host"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import React from "react";
import { createRoot, type Root } from "react-dom/client";
import AceternityGlobeReact from "./AceternityGlobeReact";

const hostRef = ref<HTMLDivElement | null>(null);
let root: Root | null = null;

onMounted(() => {
  if (!hostRef.value) return;
  root = createRoot(hostRef.value);
  root.render(React.createElement(AceternityGlobeReact as any));
});

onBeforeUnmount(() => {
  root?.unmount();
  root = null;
});
</script>

<style scoped>
.react-globe-host {
  width: 100%;
  height: 100%;
}

.react-globe-host :deep(.react-globe-panel) {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px 10px 10px;
}

.react-globe-host :deep(.react-globe-head) {
  margin-bottom: 4px;
}

.react-globe-host :deep(.panel-title-row) {
  display: flex;
  align-items: center;
  gap: 10px;
}

.react-globe-host :deep(.panel-tag) {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.15em;
  padding: 3px 8px;
  border-radius: 5px;
  text-transform: uppercase;
  color: #c084fc;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.react-globe-host :deep(.panel-title) {
  font-size: 14px;
  font-weight: 600;
  color: #dbeafe;
}

.react-globe-host :deep(.panel-hint) {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.9);
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.react-globe-host :deep(.react-globe-canvas-wrap) {
  flex: 1;
  min-height: 180px;
  position: relative;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: 8px;
  background: radial-gradient(circle at 50% 50%, rgba(8, 47, 73, 0.2), rgba(2, 6, 23, 0.2));
  overflow: hidden;
}

.react-globe-host :deep(.react-globe-canvas) {
  position: absolute;
  inset: 0;
}

.react-globe-host :deep(.react-globe-canvas-wrap canvas) {
  width: 100% !important;
  height: 100% !important;
  display: block;
}

.react-globe-host :deep(.react-globe-tooltip) {
  padding: 3px 7px;
  border-radius: 6px;
  border: 1px solid rgba(56, 189, 248, 0.35);
  background: rgba(2, 6, 23, 0.82);
  color: #bae6fd;
  font-size: 11px;
  white-space: nowrap;
  pointer-events: none;
}

/* Tailwind utility compatibility for original Aceternity source */
.react-globe-host :deep(.overflow-hidden) { overflow: hidden; }
.react-globe-host :deep(.rounded-full) { border-radius: 9999px; }
.react-globe-host :deep(.cursor-pointer) { cursor: pointer; }
.react-globe-host :deep(.h-full) { height: 100%; }
.react-globe-host :deep(.w-full) { width: 100%; }
.react-globe-host :deep(.object-cover) { object-fit: cover; }
.react-globe-host :deep(.inline-block) { display: inline-block; }
.react-globe-host :deep(.text-sm) { font-size: 0.875rem; line-height: 1.25rem; }
.react-globe-host :deep(.text-neutral-400) { color: rgb(163 163 163); }
.react-globe-host :deep(.flex) { display: flex; }
.react-globe-host :deep(.flex-col) { flex-direction: column; }
.react-globe-host :deep(.items-center) { align-items: center; }
.react-globe-host :deep(.gap-3) { gap: 0.75rem; }

/* Ensure marker image never spills outside its tiny pin container */
.react-globe-host :deep(.cursor-pointer img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
</style>
