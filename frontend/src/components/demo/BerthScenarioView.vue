<script setup>
import { computed, ref } from "vue";
import { useBerthSchedulingDemo } from "../../composables/useBerthSchedulingDemo";

const {
  settings,
  selectedVesselId,
  selectedVessel,
  berths,
  schedule,
  simulationTime,
  playing,
  playbackSpeed,
  setCanvas,
  resetPlayback,
  togglePlayback,
  updateSelectedVessel,
  formatHours,
} = useBerthSchedulingDemo();

const advancedOpen = ref(false);
const clock = computed(() => simulationTime.value % schedule.value.maxEnd);

const activeAssignment = computed(
  () => schedule.value.assignments.find((item) => clock.value >= item.start && clock.value <= item.end) || null
);

const waitingAssignment = computed(
  () =>
    schedule.value.assignments
      .filter((item) => item.start > clock.value)
      .sort((a, b) => (b.start - b.eta) - (a.start - a.eta))[0] || null
);

const focusAssignment = computed(() => waitingAssignment.value || activeAssignment.value || null);

const blockingAssignment = computed(() => {
  if (!waitingAssignment.value) {
    return null;
  }
  return (
    schedule.value.assignments.find(
      (item) =>
        item.berthId === waitingAssignment.value.berthId &&
        item.id !== waitingAssignment.value.id &&
        item.start <= waitingAssignment.value.start &&
        item.end >= waitingAssignment.value.start
    ) || null
  );
});

const mainMetric = computed(() => {
  if (!waitingAssignment.value) {
    return "0.0h";
  }
  return `${Math.max(0, waitingAssignment.value.start - waitingAssignment.value.eta).toFixed(1)}h`;
});

const secondaryMetrics = computed(() => [
  { label: "总等待时间", value: formatHours(schedule.value.metrics.totalWaiting) },
  { label: "泊位利用率", value: `${Math.round(schedule.value.metrics.berthUtilization * 100)}%` },
]);

const conclusionTitle = computed(() => {
  if (waitingAssignment.value) {
    return `${waitingAssignment.value.id} 在等，不是因为到得晚，而是因为 ${waitingAssignment.value.berthId} 还没释放。`;
  }
  if (activeAssignment.value) {
    return `${activeAssignment.value.id} 正在被优先服务，系统当前优先压低整体等待链。`;
  }
  return "当前没有明显排队冲突，泊位窗口处于可消化状态。";
});

const explanationItems = computed(() => {
  if (waitingAssignment.value) {
    return [
      `${waitingAssignment.value.berthId} 前序作业未结束，${waitingAssignment.value.id} 还不能提前靠泊。`,
      settings.optimizationMode === "advanced"
        ? "当前规则同时检查泊位占用、岸桥窗口和安全距离。"
        : "当前规则优先压低整体等待，而不是先满足单船等待。",
    ];
  }
  if (activeAssignment.value) {
    return [
      `${activeAssignment.value.id} 正在 ${activeAssignment.value.berthId} 作业，当前分配 ${activeAssignment.value.cranes} 台岸桥。`,
      "当前没有形成新的等待链，重点是持续释放泊位窗口。",
    ];
  }
  return [
    "当前没有船在等待，主画面重点是观察泊位如何逐步释放。",
    "提高到港强度后，等待链会重新出现。",
  ];
});

const suggestionText = computed(() => {
  if (!waitingAssignment.value) {
    return "继续提高到港强度，最忙的泊位会最先重新形成等待链。";
  }
  return `若释放 1 个额外泊位窗口，${waitingAssignment.value.id} 等待会立即下降。`;
});

const ganttRows = computed(() =>
  berths.value.map((berth) => ({
    berth,
    assignments: schedule.value.assignments.filter((item) => item.berthId === berth.id),
  }))
);

const equations = computed(() => [
  {
    label: "ETA 约束",
    formula: "start_i >= ETA_i",
    plain: "船的实际开始时刻不能早于到港时刻。",
    live: focusAssignment.value
      ? `${focusAssignment.value.id}: ${focusAssignment.value.start.toFixed(1)}h >= ${focusAssignment.value.eta.toFixed(1)}h`
      : "当前无焦点船次。",
  },
  {
    label: "泊位约束",
    formula: "One berth, one vessel",
    plain: "同一泊位同一时段只能服务一条船。",
    live: focusAssignment.value ? `${focusAssignment.value.berthId} 当前只允许一条作业链占用。` : "等待下一次靠泊。",
  },
  {
    label: "岸桥资源约束",
    formula: "Σ crane_i(t) <= Q",
    plain: "任一时刻分配出去的岸桥总数不能超过系统上限。",
    live: `当前岸桥上限 ${settings.cranes}，模式为${settings.optimizationMode === "advanced" ? "高级联合调度" : "基础模式"}。`,
  },
]);

const vesselOptions = computed(() => schedule.value.assignments.map((item) => item.id));

function widthPercent(start, end) {
  return `${((end - start) / schedule.value.maxEnd) * 100}%`;
}

function leftPercent(start) {
  return `${(start / schedule.value.maxEnd) * 100}%`;
}
</script>

<template>
  <section class="panel berth-sandbox-panel">
    <div class="berth-sandbox-header">
      <div>
        <p class="eyebrow">Scenario 01</p>
        <h1>泊位分配与岸桥调度</h1>
        <p class="scene-overview-text">这不是港口总览，而是一张等待诊断图。</p>
      </div>

      <div class="berth-kpi-cluster refined-kpi-cluster">
        <article class="berth-kpi-main refined-kpi-main">
          <span>当前焦点等待</span>
          <strong>{{ mainMetric }}</strong>
        </article>
        <article v-for="item in secondaryMetrics" :key="item.label" class="berth-kpi-sub refined-kpi-sub">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </div>
    </div>

    <section class="berth-stage-grid refined-berth-stage-grid">
      <article class="berth-stage-card refined-berth-stage-card">
        <div class="panel-header berth-stage-copy">
          <h2>等待诊断图</h2>
          <p>只围绕焦点船、目标泊位和阻塞船展开。</p>
        </div>

        <div class="berth-canvas-shell refined-berth-canvas-shell">
          <canvas :ref="setCanvas" class="scenario-canvas berth-canvas"></canvas>

          <div class="berth-diagnostic-overlay" v-if="waitingAssignment">
            <div class="berth-node waiting-node">
              <span>焦点船</span>
              <strong>{{ waitingAssignment.id }}</strong>
              <small>WAITING · {{ mainMetric }}</small>
            </div>
            <div class="berth-link-arrow"></div>
            <div class="berth-node target-node">
              <span>目标泊位</span>
              <strong>{{ waitingAssignment.berthId }}</strong>
              <small>TARGET</small>
            </div>
            <div class="berth-link-arrow danger"></div>
            <div class="berth-node blocking-node">
              <span>阻塞船</span>
              <strong>{{ blockingAssignment?.id || "Occupied" }}</strong>
              <small>OCCUPIED</small>
            </div>
          </div>
        </div>
      </article>

      <aside class="berth-brief-card refined-brief-card">
        <p class="eyebrow">结论卡</p>
        <h2>{{ conclusionTitle }}</h2>

        <div class="berth-brief-list refined-brief-list">
          <p v-for="item in explanationItems" :key="item">{{ item }}</p>
        </div>

        <div class="berth-brief-suggestion refined-brief-suggestion">
          <span>建议</span>
          <strong>{{ suggestionText }}</strong>
        </div>
      </aside>
    </section>

    <section class="berth-secondary-grid refined-berth-secondary-grid">
      <article class="berth-timeline-card refined-timeline-card">
        <div class="panel-header">
          <h2>时间推演</h2>
          <p>只强调目标泊位这一行和等待空窗。</p>
        </div>

        <div class="gantt-axis berth-gantt-axis">
          <span
            v-for="mark in 9"
            :key="mark"
            class="gantt-tick"
            :style="{ left: `${((mark - 1) / 8) * 100}%` }"
          >
            {{ ((schedule.maxEnd / 8) * (mark - 1)).toFixed(0) }}h
          </span>
        </div>

        <div class="gantt-board">
          <div
            v-for="row in ganttRows"
            :key="row.berth.id"
            class="gantt-row"
            :class="{
              'berth-row-focus': waitingAssignment && waitingAssignment.berthId === row.berth.id,
              'berth-row-muted': waitingAssignment && waitingAssignment.berthId !== row.berth.id,
            }"
          >
            <strong>{{ row.berth.id }}</strong>
            <div class="gantt-track berth-gantt-track">
              <div
                v-if="waitingAssignment && waitingAssignment.berthId === row.berth.id"
                class="berth-wait-window refined-wait-window"
                :style="{
                  left: leftPercent(waitingAssignment.eta),
                  width: widthPercent(waitingAssignment.eta, waitingAssignment.start),
                }"
              >
                <span>Wait {{ Math.max(0, waitingAssignment.start - waitingAssignment.eta).toFixed(1) }}h</span>
              </div>
              <div
                v-for="item in row.assignments"
                :key="item.id"
                class="gantt-bar"
                :class="{ active: focusAssignment && focusAssignment.id === item.id, muted: focusAssignment && focusAssignment.id !== item.id }"
                :style="{ left: leftPercent(item.start), width: widthPercent(item.start, item.end), background: item.color }"
              >
                <span>{{ item.id }}</span>
              </div>
            </div>
          </div>
        </div>
      </article>

      <article class="berth-controls-card refined-controls-card">
        <div class="panel-header">
          <h2>实验控制</h2>
          <p>控制区保持次要，只露出最常用控制。</p>
        </div>

        <div class="berth-control-toolbar refined-control-toolbar">
          <button type="button" class="primary" @click="togglePlayback">
            {{ playing ? "暂停" : "播放" }}
          </button>
          <label class="berth-inline-control">
            <span>速度</span>
            <input v-model="playbackSpeed" type="range" min="0.6" max="2" step="0.1" />
            <strong>{{ playbackSpeed.toFixed(1) }}x</strong>
          </label>
          <label class="berth-inline-control">
            <span>规则</span>
            <select v-model="settings.rule">
              <option value="greedy">加权贪心</option>
              <option value="fcfs">先来先服务</option>
              <option value="shortest">最短作业优先</option>
              <option value="priority">高优先级优先</option>
            </select>
          </label>
        </div>

        <div class="berth-basic-controls">
          <label class="berth-slider-row">
            <span>泊位数量</span>
            <input v-model="settings.berthCount" type="range" min="2" max="3" step="1" />
            <strong>{{ settings.berthCount }}</strong>
          </label>
          <label class="berth-slider-row">
            <span>岸桥数量</span>
            <input v-model="settings.cranes" type="range" min="4" max="8" step="1" />
            <strong>{{ settings.cranes }}</strong>
          </label>
          <label class="berth-slider-row">
            <span>到港强度</span>
            <input v-model="settings.arrivalScale" type="range" min="0.8" max="1.3" step="0.05" />
            <strong>{{ settings.arrivalScale.toFixed(2) }}</strong>
          </label>
        </div>

        <button type="button" class="berth-advanced-toggle" @click="advancedOpen = !advancedOpen">
          {{ advancedOpen ? "收起高级参数" : "展开高级参数" }}
        </button>

        <div v-if="advancedOpen" class="berth-advanced-panel">
          <div class="berth-basic-controls">
            <label class="berth-slider-row">
              <span>等待权重</span>
              <input v-model="settings.weights.waiting" type="range" min="0.2" max="1.6" step="0.1" />
              <strong>{{ settings.weights.waiting.toFixed(1) }}</strong>
            </label>
            <label class="berth-slider-row">
              <span>Makespan 权重</span>
              <input v-model="settings.weights.makespan" type="range" min="0.1" max="1.2" step="0.1" />
              <strong>{{ settings.weights.makespan.toFixed(1) }}</strong>
            </label>
            <label class="berth-slider-row">
              <span>安全距离</span>
              <input v-model="settings.safetyDistance" type="range" min="1" max="2" step="1" />
              <strong>{{ settings.safetyDistance }}</strong>
            </label>
          </div>

          <div class="berth-advanced-grid">
            <label class="field">
              <span>目标船</span>
              <select v-model="selectedVesselId">
                <option v-for="id in vesselOptions" :key="id" :value="id">{{ id }}</option>
              </select>
            </label>
            <label class="berth-slider-row">
              <span>该船 ETA</span>
              <input
                :value="selectedVessel.eta"
                type="range"
                min="1"
                max="12"
                step="0.1"
                @input="updateSelectedVessel({ eta: Number($event.target.value) })"
              />
              <strong>{{ selectedVessel.eta.toFixed(1) }}</strong>
            </label>
            <label class="berth-slider-row">
              <span>岸桥上限</span>
              <input
                :value="selectedVessel.maxCranes"
                type="range"
                min="1"
                max="4"
                step="1"
                @input="updateSelectedVessel({ maxCranes: Number($event.target.value) })"
              />
              <strong>{{ selectedVessel.maxCranes }}</strong>
            </label>
          </div>
        </div>
      </article>
    </section>

    <section class="berth-explain-card refined-explain-card">
      <div class="panel-header">
        <h2>为什么这个方案成立</h2>
        <p>这里只保留三条 explainability 约束。</p>
      </div>

      <div class="berth-equation-grid">
        <article v-for="item in equations" :key="item.label" class="berth-equation-card">
          <span>{{ item.label }}</span>
          <strong class="mono">{{ item.formula }}</strong>
          <p>{{ item.plain }}</p>
          <small>{{ item.live }}</small>
        </article>
      </div>
    </section>
  </section>
</template>
