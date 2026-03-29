<script setup>
import { computed, onMounted, ref } from "vue";

const props = defineProps({
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
  plotLayers: {
    type: Array,
    default: () => [],
  },
  plotMeta: {
    type: Object,
    default: () => ({}),
  },
});

const editText = defineModel("editText", { default: "" });
const emit = defineEmits(["ready", "submitEdit", "toggleLayer"]);
const localTarget = ref(null);

const rangeEntries = computed(() => Object.entries(props.plotMeta.parameterRanges || {}));

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

    <div v-if="plotLayers.length" class="plot-layer-panel">
      <div class="plot-layer-header">
        <strong>PlotSpec 元信息</strong>
        <span>{{ plotMeta.expressionType || "unknown" }} / {{ plotMeta.dimension || "2d" }} / {{ plotMeta.traceCount }} traces</span>
      </div>

      <div class="plot-meta-grid">
        <article class="plot-meta-card">
          <strong>表达式类型</strong>
          <span>{{ plotMeta.expressionType || "未识别" }}</span>
        </article>
        <article class="plot-meta-card">
          <strong>维度</strong>
          <span>{{ plotMeta.dimension || "未识别" }}</span>
        </article>
        <article class="plot-meta-card">
          <strong>图层数</strong>
          <span>{{ plotMeta.traceCount }}</span>
        </article>
      </div>

      <div v-if="plotMeta.formulas?.length" class="plot-formula-list">
        <strong>当前公式</strong>
        <span v-for="formula in plotMeta.formulas" :key="formula" class="plot-formula-chip">{{ formula }}</span>
      </div>

      <div v-if="rangeEntries.length" class="plot-formula-list">
        <strong>参数范围</strong>
        <span
          v-for="[name, bounds] in rangeEntries"
          :key="name"
          class="plot-formula-chip"
        >
          {{ name }} ∈ [{{ Number(bounds[0]).toFixed(2) }}, {{ Number(bounds[1]).toFixed(2) }}]
        </span>
      </div>

      <div class="plot-layer-list">
        <button
          v-for="layer in plotLayers"
          :key="layer.index"
          type="button"
          class="secondary plot-layer-chip"
          :class="{ inactive: !layer.visible }"
          @click="emit('toggleLayer', layer.index)"
        >
          {{ layer.visible ? "隐藏" : "显示" }} / {{ layer.name }} / {{ layer.kind }}
        </button>
      </div>
    </div>

    <form class="plot-edit-panel" @submit.prevent="emit('submitEdit')">
      <label class="field">
        <span>基于当前图像修改</span>
        <textarea
          v-model="editText"
          rows="3"
          :disabled="!plot"
          placeholder="例如：只保留这张图的 x 正半轴部分。"
        />
      </label>
      <div class="plot-edit-actions">
        <button type="submit" class="primary" :disabled="!plot">修改当前图像</button>
        <p>这里只会修改上方当前图像；如果要新建一张图，请使用原本的主输入框。</p>
      </div>
    </form>

    <div class="code-panel">
      <h3>MATLAB 示例代码</h3>
      <pre class="code-block">{{ matlabCode }}</pre>
      <p class="tip-text">{{ teachingTip }}</p>
    </div>
  </section>
</template>
