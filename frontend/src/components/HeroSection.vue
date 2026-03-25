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
    title: "高数可视化",
    text: "把公式、题干和自然语言描述转换成二维函数或三维曲面演示。",
  },
  {
    title: "航运知识问答",
    text: "优先检索本地题库和知识点，未命中时再进行模型补答。",
  },
  {
    title: "MATLAB 代码生成",
    text: "每次绘图都会同步给出 MATLAB 示例代码，方便课堂演示和课后复现。",
  },
  {
    title: "结构化数据接入",
    text: "支持知识点表和题目表导入，后续可以直接接入队友整理的课程数据。",
  },
];

const architectureNodes = ["用户输入", "本地知识匹配", "智能补答", "结果与图形展示"];
</script>

<template>
  <section class="hero">
    <article class="hero-copy">
      <p class="eyebrow">NavMath Vision / 智绘数航</p>
      <h1>数学可视化与航运知识融合学习辅助系统</h1>
      <p class="hero-text">
        当前 MVP 聚焦高等数学与远洋运输业务两门课程，支持知识问答、公式绘图、自然语言绘图和 MATLAB
        代码生成。
      </p>

      <div class="feature-grid">
        <article v-for="item in featureCards" :key="item.title" class="feature-card">
          <strong>{{ item.title }}</strong>
          <span>{{ item.text }}</span>
        </article>
      </div>

      <div class="architecture-board">
        <p>系统流程</p>
        <div class="architecture-flow">
          <span v-for="item in architectureNodes" :key="item">{{ item }}</span>
        </div>
      </div>
    </article>

    <aside class="hero-panel">
      <p class="eyebrow">快速开始</p>
      <h2>直接提问或快速试样例</h2>
      <p>主页面保留正常交互视角。你可以自由输入题目、公式或图形描述，也可以先点一个样例快速测试。</p>

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
