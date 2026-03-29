<script setup>
import { computed, ref } from "vue";
import TopNav from "./components/TopNav.vue";
import BerthScenarioView from "./components/demo/BerthScenarioView.vue";
import YardScenarioView from "./components/demo/YardScenarioView.vue";
import InventoryScenarioView from "./components/demo/InventoryScenarioView.vue";
import BulkPortScenarioView from "./components/demo/BulkPortScenarioView.vue";

const url = new URL(window.location.href);
const currentCategory = ref(url.searchParams.get("group") || "operations");
const currentScene = ref(url.searchParams.get("scene") || "berth");

const categories = [
  {
    key: "operations",
    title: "港口运营优化",
    description: "泊位、岸桥、场桥、堆场、车辆、卸船机等现场调度类场景。",
  },
  {
    key: "supply",
    title: "供应链与系统仿真",
    description: "库存、航线、供应链反馈与系统级动态仿真。",
  },
  {
    key: "resilience",
    title: "预测、监测与韧性",
    description: "预测、监控和韧性评估类入口，当前先保留扩展位。",
  },
];

const sceneOptions = [
  {
    key: "berth",
    eyebrow: "Scenario 01",
    title: "泊位分配与岸桥调度",
    description: "讲清泊位、岸桥、等待时间和吞吐量之间的双资源耦合。",
    category: "operations",
  },
  {
    key: "yard",
    eyebrow: "Scenario 02",
    title: "堆场重定位与场桥协同",
    description: "讲清栈阻塞、翻箱代价、启发式决策与未来成本之间的冲突。",
    category: "operations",
  },
  {
    key: "bulk",
    eyebrow: "Scenario 03",
    title: "干散货港口卸船全流程",
    description: "讲清泊位、卸船机、水平运输和堆场接卸的全流程协同。",
    category: "operations",
  },
  {
    key: "inventory",
    eyebrow: "Scenario 04",
    title: "海运库存与航线联合决策",
    description: "讲清库存动态、海上路径、补货时机和滚动优化之间的耦合。",
    category: "supply",
  },
];

const visibleScenes = computed(() => sceneOptions.filter((item) => item.category === currentCategory.value));

function setCategory(key) {
  currentCategory.value = key;
  const first = sceneOptions.find((item) => item.category === key);
  if (first) {
    currentScene.value = first.key;
  }
}

function setScene(key) {
  currentScene.value = key;
}
</script>

<template>
  <main class="page-shell">
    <TopNav current-page="demo" />

    <section class="panel scene-switch-panel">
      <div class="panel-header">
        <h2>教学场景库</h2>
        <p>先选三大类，再在弹出的子框里进入具体场景，避免重复主题铺成一整页。</p>
      </div>

      <div class="category-popup-grid">
        <article
          v-for="item in categories"
          :key="item.key"
          class="category-popup-card"
          :class="{ active: currentCategory === item.key }"
        >
          <button type="button" class="category-popup-trigger" @click="setCategory(item.key)">
            <span class="eyebrow">场景大类</span>
            <strong>{{ item.title }}</strong>
            <span>{{ item.description }}</span>
          </button>

          <transition name="category-pop">
            <div v-if="currentCategory === item.key" class="category-popup-menu">
              <template v-if="visibleScenes.length">
                <button
                  v-for="scene in visibleScenes"
                  :key="scene.key"
                  type="button"
                  class="category-popup-option"
                  :class="{ active: currentScene === scene.key }"
                  @click="setScene(scene.key)"
                >
                  <small>{{ scene.eyebrow }}</small>
                  <strong>{{ scene.title }}</strong>
                  <span>{{ scene.description }}</span>
                </button>
              </template>
              <div v-else class="category-popup-empty">
                <strong>内容待接入</strong>
                <span>这个大类先保留统一入口，后续再补具体场景。</span>
              </div>
            </div>
          </transition>
        </article>
      </div>
    </section>

    <BerthScenarioView v-if="currentScene === 'berth'" />
    <YardScenarioView v-else-if="currentScene === 'yard'" />
    <InventoryScenarioView v-else-if="currentScene === 'inventory'" />
    <BulkPortScenarioView v-else-if="currentScene === 'bulk'" />
    <section v-else class="panel scene-overview">
      <div class="scene-overview-copy">
        <p class="eyebrow">Coming Next</p>
        <h1>预测、监测与韧性</h1>
        <p class="scene-overview-text">
          这个分类先作为统一产品结构中的预留入口，后续接入吞吐量预测、交通流监测和港口韧性评估。
        </p>
      </div>
    </section>
  </main>
</template>
