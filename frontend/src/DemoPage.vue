<script setup>
import TopNav from "./components/TopNav.vue";

const nextIdeas = [
  "多课程页面入口",
  "教师管理台",
  "数据审核页",
  "模型与路由设置页",
];
</script>

<template>
  <main class="page-shell">
    <TopNav current-page="demo" />

    <section class="hero demo-hero">
      <article class="hero-copy">
        <p class="eyebrow">Page Placeholder / 页面占位</p>
        <h1>预留页面</h1>
        <p class="hero-text">
          主页面已经覆盖当前演示需求，这里先保留为后续扩展入口。后面如果新增课程页面、教师端或设置页，可以直接接在这个位置。
        </p>

        <div class="hero-tags">
          <span>已保留路由</span>
          <span>已保留顶部切换</span>
          <span>便于后续扩展</span>
        </div>
      </article>

      <aside class="hero-panel">
        <p class="eyebrow">后续可接</p>
        <h2>建议扩展方向</h2>
        <div class="example-list">
          <div v-for="item in nextIdeas" :key="item" class="example-item">
            <strong>{{ item }}</strong>
            <span>当前仅保留占位，后续可以直接扩成独立页面。</span>
          </div>
        </div>
      </aside>
    </section>
  </main>
</template>
