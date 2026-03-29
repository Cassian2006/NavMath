import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";

const BASE_JOBS = [
  { id: "BULK-01", eta: 0.8, tonnage: 42, moisture: 0.12, priority: 1.1, color: "#2563eb" },
  { id: "BULK-02", eta: 2.4, tonnage: 58, moisture: 0.18, priority: 1.3, color: "#d97706" },
  { id: "BULK-03", eta: 4.1, tonnage: 36, moisture: 0.1, priority: 0.9, color: "#14b8a6" },
];

function formatHours(value) {
  return `${value.toFixed(1)} h`;
}

function strategyLabel(strategy) {
  if (strategy === "cost_first") {
    return "成本优先";
  }
  if (strategy === "energy_saving") {
    return "能耗优先";
  }
  return "时间优先";
}

function getStageRates(settings) {
  const unloaderRate =
    settings.unloaders *
    (settings.strategy === "time_first" ? 9.2 : settings.strategy === "energy_saving" ? 7.1 : 8.0);
  const transportRate =
    settings.trucks *
    (settings.strategy === "cost_first" ? 4.8 : settings.strategy === "energy_saving" ? 4.4 : 5.4);
  const yardRate =
    settings.yardLines *
    (settings.strategy === "energy_saving" ? 5.0 : settings.strategy === "time_first" ? 5.8 : 5.4);

  return { unloaderRate, transportRate, yardRate };
}

function stageUtilization(load, rate, duration) {
  if (!rate || !duration) {
    return 0;
  }
  return Math.min(0.98, load / (rate * duration));
}

function buildPlan(settings) {
  const jobs = BASE_JOBS.map((job) => ({
    ...job,
    tonnage: job.tonnage * settings.workloadScale,
  }));

  const resources = {
    berthReady: 0,
    unloaderReady: 0,
    truckReady: 0,
    yardReady: 0,
  };
  const assignments = [];

  jobs.forEach((job) => {
    const { unloaderRate, transportRate, yardRate } = getStageRates(settings);
    const weatherFactor = job.moisture > 0.15 ? 0.92 : 1;
    const berthStart = Math.max(job.eta, resources.berthReady);
    const unloadStart = Math.max(berthStart, resources.unloaderReady);
    const unloadDuration = job.tonnage / (unloaderRate * weatherFactor);
    const unloadEnd = unloadStart + unloadDuration;

    const transferStart = Math.max(unloadEnd, resources.truckReady);
    const transferDuration = job.tonnage / transportRate;
    const transferEnd = transferStart + transferDuration;

    const yardStart = Math.max(transferEnd, resources.yardReady);
    const yardDuration = job.tonnage / yardRate;
    const yardEnd = yardStart + yardDuration;

    const stageDurations = {
      berth: unloadStart - berthStart,
      unloader: unloadDuration,
      transport: transferDuration,
      yard: yardDuration,
      transferQueue: yardStart - transferEnd,
    };

    const bottleneck = Object.entries({
      卸船机: unloadDuration,
      水平运输: transferDuration + stageDurations.transferQueue,
      堆场接卸: yardDuration,
    }).sort((a, b) => b[1] - a[1])[0][0];

    const sailingCost = job.tonnage * (settings.strategy === "cost_first" ? 2.2 : 2.7);
    const handlingCost = job.tonnage * (settings.unloaders * 0.9 + settings.trucks * 0.38 + settings.yardLines * 0.55);
    const energy = job.tonnage * (settings.strategy === "energy_saving" ? 1.7 : 2.35);

    assignments.push({
      ...job,
      berthStart,
      unloadStart,
      unloadEnd,
      transferStart,
      transferEnd,
      yardStart,
      yardEnd,
      wait: berthStart - job.eta,
      stageDurations,
      bottleneck,
      sailingCost,
      handlingCost,
      energy,
      unloaderUtilization: stageUtilization(job.tonnage, unloaderRate, unloadDuration),
      truckUtilization: stageUtilization(job.tonnage, transportRate, transferDuration),
      yardUtilization: stageUtilization(job.tonnage, yardRate, yardDuration),
    });

    resources.berthReady = yardEnd;
    resources.unloaderReady = unloadEnd;
    resources.truckReady = transferEnd;
    resources.yardReady = yardEnd;
  });

  const duration = Math.max(14, assignments[assignments.length - 1]?.yardEnd + 1.4 || 14);
  const totalWait = assignments.reduce((sum, item) => sum + item.wait, 0);
  const totalTime = assignments.reduce((sum, item) => sum + (item.yardEnd - item.berthStart), 0);
  const totalCost = assignments.reduce((sum, item) => sum + item.sailingCost + item.handlingCost, 0);
  const energy = assignments.reduce((sum, item) => sum + item.energy, 0);
  const throughput = assignments.reduce((sum, item) => sum + item.tonnage, 0);
  const makespan = assignments.length ? assignments[assignments.length - 1].yardEnd : 0;
  const serviceLevel = assignments.length ? Math.max(0, 100 - totalWait * 2.1) : 100;
  const bottleneckLoads = {
    卸船机: assignments.reduce((sum, item) => sum + item.stageDurations.unloader, 0),
    水平运输: assignments.reduce((sum, item) => sum + item.stageDurations.transport + item.stageDurations.transferQueue, 0),
    堆场接卸: assignments.reduce((sum, item) => sum + item.stageDurations.yard, 0),
  };
  const dominantBottleneck = Object.entries(bottleneckLoads).sort((a, b) => b[1] - a[1])[0][0];

  return {
    assignments,
    duration,
    metrics: {
      totalWait,
      totalTime,
      totalCost,
      energy,
      throughput,
      serviceLevel,
      makespan,
      dominantBottleneck,
      avgUnloaderUtilization: assignments.length
        ? assignments.reduce((sum, item) => sum + item.unloaderUtilization, 0) / assignments.length
        : 0,
      avgTruckUtilization: assignments.length
        ? assignments.reduce((sum, item) => sum + item.truckUtilization, 0) / assignments.length
        : 0,
      avgYardUtilization: assignments.length
        ? assignments.reduce((sum, item) => sum + item.yardUtilization, 0) / assignments.length
        : 0,
    },
  };
}

export function useBulkPortDemo() {
  const settings = reactive({
    unloaders: 2,
    trucks: 5,
    yardLines: 2,
    workloadScale: 1,
    strategy: "time_first",
  });

  const playing = ref(false);
  const playbackSpeed = ref(1);
  const simulationTime = ref(0);
  const runtime = reactive({ frameId: 0, lastTick: 0 });

  const plan = computed(() => buildPlan(settings));
  const currentJob = computed(() => {
    const clock = simulationTime.value % plan.value.duration;
    return plan.value.assignments.find((item) => clock >= item.berthStart && clock <= item.yardEnd) || null;
  });

  const activeStage = computed(() => {
    if (!currentJob.value) {
      return null;
    }
    const clock = simulationTime.value % plan.value.duration;
    if (clock <= currentJob.value.unloadEnd) {
      return "unloader";
    }
    if (clock <= currentJob.value.transferEnd) {
      return "transport";
    }
    if (clock <= currentJob.value.yardEnd) {
      return "yard";
    }
    return "berth";
  });

  const stageNarrative = computed(() => [
    {
      title: "当前流程瓶颈",
      body: currentJob.value
        ? `${currentJob.value.id} 当前最慢环节是 ${currentJob.value.bottleneck}，这会直接拉长整船完工时间。`
        : "当前没有活跃船次，系统准备进入下一艘干散货船。",
    },
    {
      title: "为什么要看全流程",
      body: "泊位、卸船机、水平运输和堆场接卸是同一条链路，前段提速但后段堵塞，并不会真正缩短 makespan。",
    },
    {
      title: "当前策略重点",
      body: `${strategyLabel(settings.strategy)}下，系统在时间、成本和能耗之间做平衡，并持续观察主瓶颈是否转移。`,
    },
  ]);

  const processCards = computed(() => {
    if (!currentJob.value) {
      return [
        { label: "泊位", value: "待命" },
        { label: "卸船机", value: "待命" },
        { label: "水平运输", value: "待命" },
        { label: "堆场接卸", value: "待命" },
      ];
    }
    return [
      { label: "泊位", value: `${currentJob.value.id} 靠泊中` },
      { label: "卸船机", value: `${settings.unloaders} 台 · ${formatHours(currentJob.value.stageDurations.unloader)}` },
      { label: "水平运输", value: `${settings.trucks} 辆 · ${formatHours(currentJob.value.stageDurations.transport)}` },
      { label: "堆场接卸", value: `${settings.yardLines} 线 · ${formatHours(currentJob.value.stageDurations.yard)}` },
    ];
  });

  const resourceCards = computed(() => [
    { label: "卸船机利用率", value: `${Math.round(plan.value.metrics.avgUnloaderUtilization * 100)}%` },
    { label: "车辆利用率", value: `${Math.round(plan.value.metrics.avgTruckUtilization * 100)}%` },
    { label: "堆场利用率", value: `${Math.round(plan.value.metrics.avgYardUtilization * 100)}%` },
    { label: "全局瓶颈", value: plan.value.metrics.dominantBottleneck },
  ]);

  function resetPlayback() {
    simulationTime.value = 0;
  }

  function togglePlayback() {
    playing.value = !playing.value;
  }

  function tick(now) {
    if (!runtime.lastTick) {
      runtime.lastTick = now;
    }
    const delta = (now - runtime.lastTick) / 1000;
    runtime.lastTick = now;
    if (playing.value) {
      simulationTime.value += delta * playbackSpeed.value * 1.2;
      if (simulationTime.value >= plan.value.duration) {
        simulationTime.value = 0;
      }
    }
    runtime.frameId = window.requestAnimationFrame(tick);
  }

  watch(
    [() => settings.unloaders, () => settings.trucks, () => settings.yardLines, () => settings.workloadScale, () => settings.strategy],
    () => {
      resetPlayback();
    }
  );

  function startLoop() {
    if (runtime.frameId) {
      window.cancelAnimationFrame(runtime.frameId);
    }
    runtime.lastTick = 0;
    runtime.frameId = window.requestAnimationFrame(tick);
  }

  onBeforeUnmount(() => {
    if (runtime.frameId) {
      window.cancelAnimationFrame(runtime.frameId);
    }
  });

  startLoop();

  return {
    settings,
    plan,
    currentJob,
    activeStage,
    stageNarrative,
    processCards,
    resourceCards,
    playing,
    playbackSpeed,
    simulationTime,
    togglePlayback,
    resetPlayback,
    formatHours,
    strategyLabel,
  };
}
