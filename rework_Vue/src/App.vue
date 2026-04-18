<script setup>
import BackgroundGradient from './components/BackgroundGradient.vue'
</script>

<template>
  <BackgroundGradient>
    <main class="home-layout">
      <section class="title-area">
        <h1 class="home-title">
          大宗绿测
          <small> - 基于机器学习的油价预测与绿色金融平台</small>
        </h1>
      </section>

      <section class="actions-area">
        <div class="actions">
          <a class="btn btn-primary" href="#" @click.prevent>立即开始</a>
          <a class="btn btn-outline" href="/大宗绿测用户手册.pdf" target="_blank" rel="noopener">
            用户手册
          </a>
        </div>
      </section>
    </main>
  </BackgroundGradient>
</template>
