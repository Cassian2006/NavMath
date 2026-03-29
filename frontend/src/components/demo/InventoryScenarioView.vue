<script setup>
import { computed } from "vue";
import { useInventoryRoutingDemo } from "../../composables/useInventoryRoutingDemo";

const {
  settings,
  plan,
  comparePlan,
  currentSnapshot,
  compareSnapshot,
  currentConstraints,
  equations,
  playing,
  playbackSpeed,
  simulationTime,
  togglePlayback,
  resetPlayback,
  singleStep,
  formatDays,
  policyLabel,
} = useInventoryRoutingDemo();

const metrics = computed(() => [
  { label: "总航行成本", value: `${plan.value.metrics.sailingCost.toFixed(1)}` },
  { label: "缺货罚金", value: `${plan.value.metrics.stockoutPenalty.toFixed(1)}` },
  { label: "库存持有成本", value: `${plan.value.metrics.holdingCost.toFixed(1)}` },
  { label: "平均装载率", value: `${((plan.value.metrics.averageLoad / settings.capacity) * 100).toFixed(0)}%` },
  { label: "缺货次数", value: `${plan.value.metrics.shortages}` },
  { label: "服务水平", value: `${plan.value.metrics.serviceLevel.toFixed(0)}%` },
]);

const compareMetrics = computed(() => [
  {
    label: "当前策略",
    value: policyLabel(settings.policy),
    cost: `总代价 ${(
      plan.value.metrics.sailingCost +
      plan.value.metrics.stockoutPenalty +
      plan.value.metrics.holdingCost
    ).toFixed(1)}`,
  },
  {
    label: "对比策略",
    value: policyLabel(settings.comparePolicy),
    cost: `总代价 ${(
      comparePlan.value.metrics.sailingCost +
      comparePlan.value.metrics.stockoutPenalty +
      comparePlan.value.metrics.holdingCost
    ).toFixed(1)}`,
  },
]);

const routeSegments = computed(() => {
  const ports = currentSnapshot.value?.ports || [];
  return ports.flatMap((port, index) =>
    ports.slice(index + 1).map((target) => ({
      key: `${port.id}-${target.id}`,
      x1: `${port.x}%`,
      y1: `${port.y}%`,
      x2: `${target.x}%`,
      y2: `${target.y}%`,
      active:
        (currentSnapshot.value?.vessel.location === port.id && currentSnapshot.value?.vessel.target === target.id) ||
        (currentSnapshot.value?.vessel.location === target.id && currentSnapshot.value?.vessel.target === port.id),
    }))
  );
});

const highestRiskPort = computed(() => {
  const ports = currentSnapshot.value?.ports || [];
  return [...ports].sort((a, b) => a.inventory / a.inventoryMin - b.inventory / b.inventoryMin)[0] || null;
});

const focusConclusion = computed(() => {
  if (!highestRiskPort.value) {
    return "当前没有明显的高风险港口。";
  }
  return `${highestRiskPort.value.id} 是当前最危险的港口，库存已经最接近安全线。`;
});

const focusReasons = computed(() => {
  return [
    `当前船舶位置：${currentSnapshot.value.vessel.location}${currentSnapshot.value.vessel.target ? `，下一站是 ${currentSnapshot.value.vessel.target}` : "，正在待命"}。`,
    highestRiskPort.value
      ? `${highestRiskPort.value.id} 当前库存 ${Math.max(0, highestRiskPort.value.inventory).toFixed(0)} / ${highestRiskPort.value.inventoryMax}。`
      : "当前所有港口都还处在安全区间。",
    `如果改用 ${policyLabel(settings.comparePolicy)}，下一站会优先考虑 ${compareSnapshot.value?.vessel.target || compareSnapshot.value?.vessel.location || "当前港口"}。`,
  ];
});

const focusForecast = computed(() => {
  return currentSnapshot.value.decision || "继续推进后，最先变黄的港口会决定下一次航线调整。";
});

function inventoryPercent(port) {
  return `${Math.max(0, Math.min(100, (port.inventory / port.inventoryMax) * 100))}%`;
}

function inventoryState(port) {
  if (port.inventory < 0 || port.inventory < port.inventoryMin * settings.safetyFactor) return "danger";
  if (port.inventory < port.inventoryMin * settings.safetyFactor * 1.4) return "warning";
  return "safe";
}

function vesselStyle(snapshot) {
  const vessel = snapshot.vessel;
  const currentPort = snapshot.ports.find((port) => port.id === vessel.location) || snapshot.ports[0];
  if (vessel.state !== "sailing" || !vessel.target) {
    return { left: `${currentPort.x}%`, top: `${currentPort.y}%` };
  }
  const targetPort = snapshot.ports.find((port) => port.id === vessel.target) || currentPort;
  const ratio = Math.max(0, Math.min(1, 1 - vessel.travelRemaining / 3));
  return {
    left: `${currentPort.x + (targetPort.x - currentPort.x) * ratio}%`,
    top: `${currentPort.y + (targetPort.y - currentPort.y) * ratio}%`,
  };
}
</script>

<template>
  <section class="panel scene-overview compact-overview">
    <div class="scene-overview-copy">
      <p class="eyebrow">Scenario 03</p>
      <h1>海运库存与航线联合决策</h1>
      <p class="scene-overview-text">只看一件事：哪个港口快缺货了，船该去哪。</p>
    </div>
  </section>

  <section class="scenario-focus-grid">
    <article class="panel scene-focus-panel">
      <div class="panel-header">
        <h2>海上网络主画面</h2>
        <p>把库存风险做得更夸张，让下一条航线一眼可见。</p>
      </div>

      <div class="inventory-status-strip">
        <article class="inventory-status-card">
          <span>当前天数</span>
          <strong>{{ formatDays(simulationTime) }}</strong>
        </article>
        <article class="inventory-status-card">
          <span>当前航线</span>
          <strong>{{ currentSnapshot.vessel.target ? `${currentSnapshot.vessel.location} -> ${currentSnapshot.vessel.target}` : `${currentSnapshot.vessel.location} 待命` }}</strong>
        </article>
        <article class="inventory-status-card inventory-status-focus">
          <span>最高风险港口</span>
          <strong>{{ highestRiskPort ? highestRiskPort.id : "无" }}</strong>
        </article>
      </div>

      <div class="inventory-map">
        <svg class="inventory-route-layer" viewBox="0 0 100 100" preserveAspectRatio="none">
          <line
            v-for="segment in routeSegments"
            :key="segment.key"
            :x1="segment.x1"
            :y1="segment.y1"
            :x2="segment.x2"
            :y2="segment.y2"
            class="inventory-route-line"
            :class="{ active: segment.active }"
          />
        </svg>

        <div
          v-for="port in currentSnapshot.ports"
          :key="port.id"
          class="inventory-port"
          :data-state="inventoryState(port)"
          :class="{ focus: highestRiskPort && highestRiskPort.id === port.id }"
          :style="{ left: `${port.x}%`, top: `${port.y}%` }"
        >
          <strong>{{ port.id }}</strong>
          <div class="inventory-bar dramatic-bar">
            <i :style="{ height: inventoryPercent(port) }"></i>
          </div>
          <span>{{ Math.max(0, port.inventory).toFixed(0) }}/{{ port.inventoryMax }}</span>
        </div>

        <div class="inventory-vessel" :style="vesselStyle(currentSnapshot)">
          <span>S1</span>
        </div>
      </div>

      <div class="inventory-route-banner">
        <strong>{{ policyLabel(settings.policy) }}</strong>
        <span>{{ currentSnapshot.decision }}</span>
        <span>对比策略下一站：{{ compareSnapshot.vessel.target || compareSnapshot.vessel.location || "待命" }}</span>
      </div>
    </article>

    <aside class="panel scene-insight-panel">
      <div class="panel-header">
        <h2>当前结论</h2>
        <p>这里只解释风险、下一步和策略差异。</p>
      </div>

      <article class="insight-summary-card">
        <strong>{{ focusConclusion }}</strong>
        <span>{{ focusForecast }}</span>
      </article>

      <div class="scene-note-list compact-note-list">
        <article v-for="item in focusReasons" :key="item" class="scene-note-card">
          <span>{{ item }}</span>
        </article>
      </div>

      <div class="scenario-divider"></div>

      <div class="scenario-metric-grid compact-metric-grid">
        <section v-for="item in metrics.slice(0, 4)" :key="item.label" class="card scenario-metric-card">
          <h3>{{ item.label }}</h3>
          <p class="scenario-metric-value">{{ item.value }}</p>
        </section>
      </div>
    </aside>
  </section>

  <section class="scenario-support-grid">
    <article class="panel control-dock-panel">
      <div class="panel-header">
        <h2>操作区</h2>
        <p>先看风险，再切策略、调容量和惩罚。</p>
      </div>

      <div class="scenario-toolbar dock-toolbar">
        <button type="button" class="primary" @click="togglePlayback">
          {{ playing ? "暂停动画" : "继续动画" }}
        </button>
        <button type="button" class="secondary" @click="singleStep">单步</button>
        <button type="button" class="secondary" @click="resetPlayback">重置</button>
        <label class="scenario-speed">
          <span>播放速度</span>
          <input v-model="playbackSpeed" type="range" min="0.5" max="4" step="0.5" />
        </label>
      </div>

      <div class="scenario-control-grid">
        <label class="field">
          <span>主策略</span>
          <select v-model="settings.policy">
            <option value="rolling_horizon_greedy">滚动时域贪心</option>
            <option value="lowest_ratio">最低库存率优先</option>
            <option value="highest_demand">最大需求优先</option>
            <option value="shortest_sailing">最短航程优先</option>
          </select>
        </label>
        <label class="field">
          <span>对比策略</span>
          <select v-model="settings.comparePolicy">
            <option value="rolling_horizon_greedy">滚动时域贪心</option>
            <option value="lowest_ratio">最低库存率优先</option>
            <option value="highest_demand">最大需求优先</option>
            <option value="shortest_sailing">最短航程优先</option>
          </select>
        </label>
        <label class="field">
          <span>船舶容量</span>
          <input v-model="settings.capacity" type="range" min="80" max="180" step="10" />
          <small>{{ settings.capacity }}</small>
        </label>
        <label class="field">
          <span>航速</span>
          <input v-model="settings.speed" type="range" min="0.8" max="1.6" step="0.1" />
          <small>{{ settings.speed.toFixed(1) }}</small>
        </label>
        <label class="field">
          <span>需求倍率</span>
          <input v-model="settings.demandScale" type="range" min="0.8" max="1.5" step="0.1" />
          <small>{{ settings.demandScale.toFixed(1) }}</small>
        </label>
        <label class="field">
          <span>缺货罚金</span>
          <input v-model="settings.stockoutPenalty" type="range" min="1" max="6" step="0.5" />
          <small>{{ settings.stockoutPenalty.toFixed(1) }}</small>
        </label>
      </div>
    </article>

    <article class="panel scene-results-panel">
      <div class="panel-header">
        <h2>约束与策略对比</h2>
        <p>保持最少信息量，只回答有没有缺货、下一步是否合理。</p>
      </div>

      <div class="scenario-compare-grid">
        <article v-for="item in compareMetrics" :key="item.label" class="scenario-insight-card">
          <strong>{{ item.label }}</strong>
          <span>{{ item.value }}</span>
          <span>{{ item.cost }}</span>
        </article>
      </div>

      <div class="equation-list">
        <article v-for="equation in equations" :key="equation" class="equation-item mono">
          {{ equation }}
        </article>
      </div>

      <div class="scenario-log-list">
        <article
          v-for="item in currentConstraints"
          :key="item.id"
          class="scenario-log-item"
          :data-status="item.stockout || item.overMax ? 'error' : item.stockoutRisk ? 'active' : 'done'"
        >
          <strong>{{ item.id }}</strong>
          <span v-if="item.stockout">库存已经跌破 0，当前存在缺货。</span>
          <span v-else-if="item.stockoutRisk">库存接近安全线，需要尽快补给。</span>
          <span v-else-if="item.overMax">库存超过上限，当前不满足容量约束。</span>
          <span v-else>库存约束正常。</span>
        </article>
      </div>
    </article>
  </section>
</template>
