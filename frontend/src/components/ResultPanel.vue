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

      <!-- 跨学科案例卡片 -->
      <article v-if="result.matched_case" class="card card-wide card-interdisciplinary">
        <div class="inter-header">
          <span class="inter-badge">🔗 跨学科案例</span>
          <span class="inter-difficulty">难度：{{ result.matched_case.difficulty || '中' }}</span>
        </div>
        <h3>{{ result.matched_case.title }}</h3>
        <div class="inter-meta">
          <span class="inter-tag math">📐 {{ result.matched_case.math_concept }}</span>
          <span class="inter-tag ship">⚓ {{ result.matched_case.shipping_scenario }}</span>
        </div>
        <p class="inter-question">{{ result.matched_case.core_question }}</p>
        <p class="inter-insight">
          <strong>核心洞察：</strong>{{ result.matched_case.key_insight }}
        </p>
        <div v-if="result.matched_case.real_world_numbers" class="inter-numbers">
          <strong>实际数据：</strong>{{ result.matched_case.real_world_numbers }}
        </div>
        <div v-if="result.matched_case.teaching_note" class="inter-note">
          💡 {{ result.matched_case.teaching_note }}
        </div>
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

<style scoped>
.card-interdisciplinary {
  border-left: 4px solid #a78bfa;
  background: linear-gradient(135deg, #1e293b 0%, #1a1f35 100%);
}
.inter-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.inter-badge {
  background: #312e81;
  color: #a5b4fc;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}
.inter-difficulty {
  font-size: 12px;
  color: #94a3b8;
}
.card-interdisciplinary h3 {
  color: #c4b5fd;
  font-size: 15px;
  margin-bottom: 10px;
}
.inter-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.inter-tag {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}
.inter-tag.math {
  background: #1e3a5f;
  color: #7dd3fc;
}
.inter-tag.ship {
  background: #1a3a2a;
  color: #6ee7b7;
}
.inter-question {
  font-size: 13px;
  color: #e2e8f0;
  margin-bottom: 8px;
  line-height: 1.6;
}
.inter-insight {
  font-size: 13px;
  color: #cbd5e1;
  margin-bottom: 8px;
  line-height: 1.6;
}
.inter-insight strong {
  color: #a78bfa;
}
.inter-numbers {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 6px;
  padding: 8px;
  background: #0f172a;
  border-radius: 6px;
}
.inter-note {
  font-size: 12px;
  color: #64748b;
  font-style: italic;
  margin-top: 6px;
}
</style>
