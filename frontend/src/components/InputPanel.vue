<script setup>
const questionText = defineModel("questionText", { default: "" });

const emit = defineEmits(["submit", "sample", "imageChange"]);

function handleImageChange(event) {
  emit("imageChange", event.target.files?.[0] || null);
}
</script>

<template>
  <form class="panel form-panel" @submit.prevent="emit('submit')">
    <div class="panel-header">
      <h2>输入区</h2>
      <p>支持自然语言问题、纯公式、图形描述和题目图片输入，系统会自动判断当前请求类型。</p>
    </div>

    <label class="field">
      <span>问题 / 公式 / 图形描述</span>
      <textarea
        v-model="questionText"
        rows="8"
        placeholder="例如：判断曲面 z = x^2 - y^2 的类型；或直接输入 z = x^2 - y^2；或输入“画一个沿 z 轴开口向上的碗状曲面”。"
      />
    </label>

    <label class="field">
      <span>题目图片</span>
      <input type="file" accept="image/*" @change="handleImageChange" />
    </label>

    <div class="actions">
      <button type="submit" class="primary">开始解析</button>
      <button type="button" class="secondary" @click="emit('sample', 'math')">数学示例</button>
      <button type="button" class="secondary" @click="emit('sample', 'sea')">航运示例</button>
      <button type="button" class="secondary" @click="emit('sample', 'shape')">绘图示例</button>
    </div>
  </form>
</template>
