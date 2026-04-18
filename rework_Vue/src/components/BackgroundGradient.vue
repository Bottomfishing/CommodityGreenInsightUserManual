<template>
  <div class="bg-page">
    <div class="bg-gradient" />
    <slot />
  </div>
</template>

<style scoped>
.bg-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  position: relative;
  overflow: hidden;
  background: #060b18;
}

.bg-gradient {
  position: absolute;
  inset: -20%;
  z-index: 0;
  pointer-events: none;
  filter: blur(46px) saturate(125%);
  opacity: 0.75;
  background:
    radial-gradient(circle at 14% 22%, rgba(56, 189, 248, 0.6), transparent 35%),
    radial-gradient(circle at 82% 20%, rgba(14, 165, 233, 0.5), transparent 38%),
    radial-gradient(circle at 24% 84%, rgba(34, 197, 94, 0.38), transparent 35%),
    radial-gradient(circle at 80% 76%, rgba(99, 102, 241, 0.35), transparent 36%);
  animation: gradient-flow 15s ease-in-out infinite alternate;
  transform-origin: center;
}

@keyframes gradient-flow {
  0%   { transform: scale(1) translate3d(0, 0, 0) rotate(0deg); }
  50%  { transform: scale(1.08) translate3d(-2%, 1.5%, 0) rotate(2deg); }
  100% { transform: scale(1.12) translate3d(2%, -1.5%, 0) rotate(-2deg); }
}
</style>
