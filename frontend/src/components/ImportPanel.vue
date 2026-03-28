<script setup>
import { ref } from "vue";

defineProps({
  summary: {
    type: String,
    required: true,
  },
  compact: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["uploadKnowledge", "uploadProblems"]);

const knowledgeFile = ref(null);
const problemsFile = ref(null);

function onKnowledgeChange(event) {
  knowledgeFile.value = event.target.files?.[0] || null;
}

function onProblemsChange(event) {
  problemsFile.value = event.target.files?.[0] || null;
}
</script>

<template>
  <section class="panel import-panel" :class="{ compact }">
    <div class="panel-header">
      <h2>CSV 导入</h2>
      <p>等队友整理完表格后，可以直接把知识点表和题目表上传到当前项目的数据目录。</p>
      <p>{{ summary }}</p>
    </div>
    <div class="import-grid">
      <form class="import-form" @submit.prevent="emit('uploadKnowledge', knowledgeFile)">
        <h3>知识点表</h3>
        <input type="file" accept=".csv" @change="onKnowledgeChange" />
        <button type="submit" class="secondary">上传 knowledge_points.csv</button>
      </form>
      <form class="import-form" @submit.prevent="emit('uploadProblems', problemsFile)">
        <h3>题目表</h3>
        <input type="file" accept=".csv" @change="onProblemsChange" />
        <button type="submit" class="secondary">上传 problems.csv</button>
      </form>
    </div>
  </section>
</template>
