<script setup>
defineProps({
  demoExamples: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(["pickExample"]);

const featureCards = [
  {
    title: "函数可视化",
    text: "把公式、题干和自然语言描述转换成二维函数或三维图形演示。",
  },
  {
    title: "航运知识问答",
    text: "课本知识点检索",
  },
  {
    title: "MATLAB 代码生成",
    text: "附上 MATLAB 代码方便复现与课堂演示",
  },
  {
    title: "结构化数据接入",
    text: "支持知识点表与题目 CSV 导入",
  },
];
</script>

<template>
  <section class="hero">
    <article class="hero-copy">
      <div class="hero-title-lockup">
        <div class="hero-title-row">
          <h1>智绘数航</h1>
          <span class="hero-method-tag">NavMath Vision</span>
        </div>
        <p class="hero-subtitle">数学可视化与航运知识融合学习辅助系统</p>
      </div>

      <div class="feature-grid">
        <article v-for="item in featureCards" :key="item.title" class="feature-card">
          <strong>{{ item.title }}</strong>
          <span>{{ item.text }}</span>
        </article>
      </div>
    </article>

    <aside class="hero-panel">
      <p class="eyebrow">快速开始</p>
      <h2>直接提问，或先点一条随机示例</h2>

      <div class="example-list">
        <button
          v-for="item in demoExamples"
          :key="item.key"
          type="button"
          class="example-item secondary"
          @click="emit('pickExample', item.key)"
        >
          <strong>{{ item.title }}</strong>
          <span>{{ item.text }}</span>
        </button>
      </div>
    </aside>
  </section>
</template>
