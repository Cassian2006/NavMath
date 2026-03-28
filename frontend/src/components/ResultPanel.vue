<script setup>
defineProps({
  statusText: {
    type: String,
    required: true,
  },
  result: {
    type: Object,
    required: true,
  },
  modeItems: {
    type: Array,
    required: true,
  },
  modeText: {
    type: String,
    required: true,
  },
  sourceText: {
    type: String,
    required: true,
  },
  sourceDetail: {
    type: String,
    required: true,
  },
  matchTypeText: {
    type: String,
    required: true,
  },
  confidenceText: {
    type: String,
    required: true,
  },
  knowledgeDefinition: {
    type: String,
    required: true,
  },
  ocrText: {
    type: String,
    required: true,
  },
  importState: {
    type: Object,
    required: true,
  },
  processSteps: {
    type: Array,
    required: true,
  },
  courseBadgeClass: {
    type: String,
    required: true,
  },
});
</script>

<template>
  <section class="panel result-panel">
    <div class="panel-header panel-header-row">
      <div>
        <h2>结果区</h2>
        <p>{{ statusText }}</p>
      </div>
      <div class="mode-pills">
        <span
          v-for="item in modeItems"
          :key="item.key"
          class="mode-pill"
          :class="{ active: item.active }"
        >
          {{ item.label }}
        </span>
      </div>
    </div>

    <div class="result-grid">
      <article class="card card-wide">
        <h3>识别文本</h3>
        <p class="mono">{{ result.input_text || "暂无内容" }}</p>
      </article>

      <article class="card">
        <h3>课程与来源</h3>
        <div class="course-row">
          <span class="course-badge" :class="courseBadgeClass">
            {{ result.detected_course || "未识别课程" }}
          </span>
          <span class="mode-caption">{{ modeText }}</span>
        </div>
        <div class="tag-list">
          <span>{{ sourceText }}</span>
          <span>{{ matchTypeText }}</span>
          <span>{{ confidenceText }}</span>
        </div>
        <p>{{ sourceDetail }}</p>
      </article>

      <article class="card">
        <h3>题目解析</h3>
        <ol class="step-list">
          <li v-for="item in result.matched_problem.analysis_steps || []" :key="item">{{ item }}</li>
        </ol>
        <p>{{ result.matched_problem.solution || "暂无解析结果" }}</p>
      </article>

      <article class="card card-wide">
        <h3>处理进程</h3>
        <div class="process-list">
          <div v-for="item in processSteps" :key="item.key" class="process-item" :data-status="item.status">
            <strong>{{ item.label }}</strong>
            <span>{{ item.detail }}</span>
          </div>
        </div>
      </article>

      <article class="card">
        <h3>知识点问答</h3>
        <p>{{ result.matched_knowledge_point?.knowledge_point || "暂无匹配" }}</p>
        <p>{{ knowledgeDefinition }}</p>
      </article>

      <article class="card">
        <h3>OCR 状态</h3>
        <p>{{ ocrText }}</p>
      </article>

      <article class="card card-wide card-soft">
        <div class="panel-meta">
          <strong>数据已接入</strong>
          <span>{{ importState.summary }}</span>
        </div>
      </article>
    </div>
  </section>
</template>
