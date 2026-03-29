<script setup>
import { computed, ref } from "vue";
import { useBulkPortDemo } from "../../composables/useBulkPortDemo";

const {
  settings,
  plan,
  currentJob,
  activeStage,
  playing,
  playbackSpeed,
  simulationTime,
  togglePlayback,
  resetPlayback,
  formatHours,
  strategyLabel,
} = useBulkPortDemo();

const advancedOpen = ref(false);

const stageKeyMap = {
  berth: "泊位",
  unloader: "卸船机",
  transport: "水平运输",
  yard: "堆场接卸",
};

const bottleneckLabel = computed(() => currentJob.value?.bottleneck || plan.value.metrics.dominantBottleneck);

const mainMetric = computed(() => ({
  label: "Makespan",
  value: formatHours(plan.value.metrics.makespan),
}));

const secondaryMetrics = computed(() => [
  { label: "总成本", value: `${plan.value.metrics.totalCost.toFixed(0)}` },
  { label: "总作业时间", value: formatHours(plan.value.metrics.totalTime) },
]);

const flowStages = computed(() => {
  const job = currentJob.value;
  const bottleneck = bottleneckLabel.value;
  const makeStage = (id, label, duration, utilization, resourceText) => {
    const isBottleneck = label === bottleneck;
    const isActive = activeStage.value === id;
    const state = isBottleneck ? "堵" : utilization > 0.74 || isActive ? "忙" : "稳";
    const throughput = duration > 0 ? (1 / duration) * 10 : 0;
    return {
      id,
      label,
      duration,
      utilization,
      resourceText,
      isBottleneck,
      isActive,
      state,
      stateText: `${state} / ${Math.round(utilization * 100)}%`,
      throughputText: throughput ? `${throughput.toFixed(1)} u/h` : "待命",
      particles: isBottleneck ? 4 : isActive ? 6 : 5,
      congestion: isBottleneck ? 4 : 0,
    };
  };

  if (!job) {
    return [
      makeStage("berth", "泊位", 0.8, 0.42, "1 个靠泊窗口"),
      makeStage("unloader", "卸船机", 2.4, plan.value.metrics.avgUnloaderUtilization, `${settings.unloaders} 台`),
      makeStage("transport", "水平运输", 2.0, plan.value.metrics.avgTruckUtilization, `${settings.trucks} 辆`),
      makeStage("yard", "堆场接卸", 3.2, plan.value.metrics.avgYardUtilization, `${settings.yardLines} 条线`),
    ];
  }

  return [
    makeStage("berth", "泊位", Math.max(0.3, job.stageDurations.berth || 0.4), 0.6, `${job.id} 靠泊中`),
    makeStage("unloader", "卸船机", job.stageDurations.unloader, job.unloaderUtilization, `${settings.unloaders} 台卸船机`),
    makeStage(
      "transport",
      "水平运输",
      job.stageDurations.transport + job.stageDurations.transferQueue,
      job.truckUtilization,
      `${settings.trucks} 辆运输车`
    ),
    makeStage("yard", "堆场接卸", job.stageDurations.yard, job.yardUtilization, `${settings.yardLines} 条接卸线`),
  ];
});

const focusConclusion = computed(() => `当前全局瓶颈是${bottleneckLabel.value}。`);

const explanationItems = computed(() => {
  if (!currentJob.value) {
    return [
      "这是一条从泊位到堆场接卸的连续生产链，最慢的一段决定全链路节奏。",
      "即使前段更快，只要最慢段不变，瓶颈就不会消失。",
    ];
  }
  return [
    `前段卸船和运输能力高于${bottleneckLabel.value}能力，货流会在这一段前持续堆积。`,
    `若只加快前段，瓶颈不会消失，只会让拥堵更集中到${bottleneckLabel.value}。`,
  ];
});

const briefMetrics = computed(() => [
  { label: "Makespan", value: formatHours(plan.value.metrics.makespan) },
  { label: "总成本", value: `${plan.value.metrics.totalCost.toFixed(0)}` },
]);

const stageMapping = computed(() => {
  const job = currentJob.value;
  const yardStage = flowStages.value.find((item) => item.id === "yard");
  const bottleneckStage = flowStages.value.find((item) => item.label === bottleneckLabel.value);
  return [
    {
      label: "FLOW",
      formula: "T_total = T_berth + T_unloader + T_transport + T_yard",
      plain: "全链路总时长由四段串联决定。",
      live: job
        ? `${job.id} 当前总链路时长约 ${(job.yardEnd - job.berthStart).toFixed(1)} h。`
        : "当前处于待命阶段，系统等待下一条散货作业进入链路。",
    },
    {
      label: "BOTTLENECK",
      formula: "bottleneck = argmax(stageDuration)",
      plain: "瓶颈段就是最慢段。",
      live: bottleneckStage
        ? `当前 ${bottleneckStage.label} 为最慢段，约 ${bottleneckStage.duration.toFixed(1)} h。`
        : "当前瓶颈尚未形成。",
    },
    {
      label: "COST",
      formula: "Min: time + cost + energy",
      plain: "时间、成本、能耗共同影响方案优劣。",
      live: yardStage
        ? `若增加 1 条接卸线，瓶颈最可能从 ${bottleneckLabel.value} 转移。`
        : `当前策略是 ${strategyLabel(settings.strategy)}。`,
    },
  ];
});

const teachingClock = computed(() => (simulationTime.value % plan.value.duration).toFixed(1));
</script>

<template>
  <section class="panel bulk-action-panel">
    <div class="bulk-action-header">
      <div>
        <p class="eyebrow">Scenario 04</p>
        <h1>干散货港口卸船全流程</h1>
        <p class="scene-overview-text">这页只讲一件事：这条货流现在卡在哪，为什么卡，改哪里最有效。</p>
      </div>

      <div class="bulk-action-kpis">
        <article class="bulk-action-kpi-main">
          <span>{{ mainMetric.label }}</span>
          <strong>{{ mainMetric.value }}</strong>
          <small>当前最慢段：{{ bottleneckLabel }}</small>
        </article>
        <article v-for="item in secondaryMetrics" :key="item.label" class="bulk-action-kpi-sub">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </div>
    </div>

    <section class="bulk-action-grid">
      <article class="bulk-action-stage">
        <div class="panel-header">
          <h2>货流主画面</h2>
          <p>先看到一条从泊位到堆场接卸的连续生产链，再去判断哪一段拖慢了全局。</p>
        </div>

        <div class="bulk-flow-statusbar">
          <article class="bulk-flow-statuscard">
            <span>当前船次</span>
            <strong>{{ currentJob ? currentJob.id : "等待下一船" }}</strong>
          </article>
          <article class="bulk-flow-statuscard">
            <span>教学时钟</span>
            <strong>{{ teachingClock }} h</strong>
          </article>
          <article class="bulk-flow-statuscard emphasis">
            <span>当前瓶颈</span>
            <strong>{{ bottleneckLabel }}</strong>
          </article>
        </div>

        <div class="bulk-chain-board" :class="{ paused: !playing }">
          <div
            v-for="(stage, index) in flowStages"
            :key="stage.id"
            class="bulk-chain-node"
            :class="{ bottleneck: stage.isBottleneck, active: stage.isActive, muted: !stage.isBottleneck && !stage.isActive }"
          >
            <div class="bulk-chain-nodehead">
              <span>{{ stage.label }}</span>
              <strong>{{ stage.state }}</strong>
            </div>

            <div class="bulk-chain-machine">
              <div class="bulk-machine-body"></div>
              <div class="bulk-machine-badge">{{ stage.resourceText }}</div>
            </div>

            <div class="bulk-chain-readout">
              <strong>{{ formatHours(stage.duration) }}</strong>
              <span>{{ stage.stateText }}</span>
              <small>吞吐 {{ stage.throughputText }}</small>
            </div>

            <div class="bulk-congestion-pile" v-if="stage.congestion">
              <i v-for="n in stage.congestion" :key="`${stage.id}-pile-${n}`"></i>
            </div>

            <template v-if="index < flowStages.length - 1">
              <div class="bulk-chain-stream" :class="{ bottleneck: stage.isBottleneck || flowStages[index + 1].isBottleneck }">
                <span
                  v-for="n in Math.max(stage.particles, flowStages[index + 1].particles)"
                  :key="`${stage.id}-particle-${n}`"
                  class="bulk-stream-particle"
                  :style="{ animationDelay: `${n * 0.18}s` }"
                ></span>
              </div>
            </template>
          </div>
        </div>

        <div class="bulk-chain-caption">
          <strong>{{ focusConclusion }}</strong>
          <span>前段再快，只要最慢段不变，全局节奏就不会变。</span>
        </div>
      </article>

      <aside class="bulk-action-brief">
        <p class="eyebrow">Current Finding</p>
        <h2>{{ focusConclusion }}</h2>
        <div class="bulk-action-brief-list">
          <p v-for="item in explanationItems" :key="item">{{ item }}</p>
        </div>
        <div class="bulk-action-brief-metrics">
          <article v-for="item in briefMetrics" :key="item.label" class="bulk-action-brief-metric">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </article>
        </div>
      </aside>
    </section>

    <section class="bulk-action-support">
      <article class="bulk-action-controls">
        <div class="panel-header">
          <h2>实验面板</h2>
          <p>先理解瓶颈，再去调整资源和策略。</p>
        </div>

        <div class="bulk-action-toolbar">
          <button type="button" class="primary" @click="togglePlayback">
            {{ playing ? "暂停" : "播放" }}
          </button>
          <button type="button" class="secondary" @click="resetPlayback">重置</button>
          <label class="bulk-action-inline">
            <span>协同策略</span>
            <select v-model="settings.strategy">
              <option value="time_first">时间优先</option>
              <option value="cost_first">成本优先</option>
              <option value="energy_saving">能耗优先</option>
            </select>
          </label>
        </div>

        <div class="bulk-action-grid-controls">
          <label class="bulk-action-slider">
            <span>卸船机数量</span>
            <input v-model="settings.unloaders" type="range" min="1" max="3" step="1" />
            <strong>{{ settings.unloaders }}</strong>
          </label>
          <label class="bulk-action-slider">
            <span>运输车辆</span>
            <input v-model="settings.trucks" type="range" min="3" max="8" step="1" />
            <strong>{{ settings.trucks }}</strong>
          </label>
          <label class="bulk-action-slider">
            <span>堆场接卸线</span>
            <input v-model="settings.yardLines" type="range" min="1" max="3" step="1" />
            <strong>{{ settings.yardLines }}</strong>
          </label>
          <label class="bulk-action-slider">
            <span>播放速度</span>
            <input v-model="playbackSpeed" type="range" min="0.6" max="2" step="0.1" />
            <strong>{{ playbackSpeed.toFixed(1) }}x</strong>
          </label>
        </div>

        <button type="button" class="berth-advanced-toggle" @click="advancedOpen = !advancedOpen">
          {{ advancedOpen ? "收起高级实验参数" : "展开高级实验参数" }}
        </button>

        <div v-if="advancedOpen" class="berth-advanced-panel">
          <label class="bulk-action-slider">
            <span>作业量倍率</span>
            <input v-model="settings.workloadScale" type="range" min="0.8" max="1.4" step="0.1" />
            <strong>{{ settings.workloadScale.toFixed(1) }}</strong>
          </label>
        </div>
      </article>

      <article class="bulk-action-explain">
        <div class="panel-header">
          <h2>为什么当前瓶颈成立</h2>
          <p>不是贴公式，而是把当前货流映射回 explainability。</p>
        </div>

        <div class="bulk-explain-grid">
          <article v-for="item in stageMapping" :key="item.label" class="bulk-explain-item">
            <span>{{ item.label }}</span>
            <strong class="mono">{{ item.formula }}</strong>
            <p>{{ item.plain }}</p>
            <small>{{ item.live }}</small>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>
