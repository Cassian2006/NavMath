<script setup>
import { onMounted, ref } from "vue";

defineProps({
  plotSummary: {
    type: String,
    required: true,
  },
  matlabCode: {
    type: String,
    required: true,
  },
  teachingTip: {
    type: String,
    required: true,
  },
  plot: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["ready"]);
const localTarget = ref(null);

onMounted(() => {
  emit("ready", localTarget.value);
});
</script>

<template>
  <section class="panel chart-panel">
    <div class="panel-header">
      <h2>图形可视化</h2>
      <p>{{ plotSummary }}</p>
    </div>
    <div ref="localTarget" class="plot"></div>
    <div class="code-panel">
      <h3>MATLAB 示例代码</h3>
      <pre class="code-block">{{ matlabCode }}</pre>
      <p class="tip-text">{{ teachingTip }}</p>
    </div>
  </section>
</template>
