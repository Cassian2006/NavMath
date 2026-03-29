import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";

const BASE_PORTS = [
  { id: "P1", x: 12, y: 38, inventoryInit: 140, inventoryMin: 40, inventoryMax: 220, demandPerDay: 18, hubSupply: 34 },
  { id: "P2", x: 34, y: 16, inventoryInit: 90, inventoryMin: 30, inventoryMax: 160, demandPerDay: 12, hubSupply: 0 },
  { id: "P3", x: 58, y: 62, inventoryInit: 60, inventoryMin: 25, inventoryMax: 140, demandPerDay: 15, hubSupply: 0 },
  { id: "P4", x: 82, y: 30, inventoryInit: 130, inventoryMin: 35, inventoryMax: 220, demandPerDay: 20, hubSupply: 0 },
];

const TRAVEL_TIMES = {
  "P1-P2": 1.2,
  "P1-P3": 2.0,
  "P1-P4": 3.0,
  "P2-P3": 1.1,
  "P2-P4": 2.0,
  "P3-P4": 1.3,
};

const EQUATIONS = [
  "I_p(t+1) = I_p(t) - d_p(t) + deliver_p(t) - pickup_p(t)",
  "L_v(t+1) = L_v(t) + pickup_v(t) - deliver_v(t)",
  "Min: a·航行成本 + b·缺货罚金 + c·库存持有成本 + d·港口靠泊成本",
];

function formatDays(value) {
  return `${value.toFixed(1)} d`;
}

function routeKey(a, b) {
  return [a, b].sort().join("-");
}

function travelTime(a, b) {
  if (a === b) {
    return 0;
  }
  return TRAVEL_TIMES[routeKey(a, b)] || 1.6;
}

function clonePorts(ports) {
  return ports.map((port) => ({ ...port }));
}

function policyLabel(policy) {
  if (policy === "lowest_ratio") {
    return "最低库存率优先";
  }
  if (policy === "highest_demand") {
    return "最大需求优先";
  }
  if (policy === "shortest_sailing") {
    return "最短航程优先";
  }
  return "滚动时域贪心";
}

function scorePort(port, vessel, policy) {
  const ratio = port.inventory / port.inventoryMin;
  const shortageGap = Math.max(0, port.inventoryMin * 1.4 - port.inventory);
  const sailing = travelTime(vessel.location, port.id);
  if (policy === "lowest_ratio") {
    return ratio * 4 + sailing * 0.35;
  }
  if (policy === "highest_demand") {
    return -port.demandPerDay + sailing * 0.6 - shortageGap * 0.08;
  }
  if (policy === "shortest_sailing") {
    return sailing + ratio * 0.45;
  }
  return ratio * 3 + sailing * 0.45 - shortageGap * 0.1 - port.demandPerDay * 0.06;
}

function buildSimulation(settings, policy) {
  const ports = clonePorts(BASE_PORTS).map((port) => ({
    ...port,
    inventory: Math.min(port.inventoryMax, port.inventoryInit),
  }));
  const vessel = {
    id: "S1",
    capacity: settings.capacity,
    speed: settings.speed,
    location: "P1",
    load: Math.min(settings.capacity, 80),
    state: "berthed",
    target: null,
    travelRemaining: 0,
  };

  const snapshots = [];
  const actions = [];
  const portCalls = [];
  let sailingCost = 0;
  let stockoutPenalty = 0;
  let holdingCost = 0;
  let shortages = 0;
  let deliveredTotal = 0;
  let serviceLevelHits = 0;
  let day = 0;

  function pushSnapshot(decision, reason, altStrategy) {
    const constraints = ports.map((port) => ({
      id: port.id,
      stockoutRisk: port.inventory <= port.inventoryMin,
      stockout: port.inventory < 0,
      overMax: port.inventory > port.inventoryMax,
    }));
    snapshots.push({
      day,
      decision,
      reason,
      altStrategy,
      vessel: { ...vessel },
      ports: ports.map((port) => ({ ...port })),
      constraints,
    });
  }

  while (day < settings.horizonDays) {
    ports.forEach((port) => {
      port.inventory += port.hubSupply || 0;
      port.inventory = Math.min(port.inventoryMax, port.inventory);
    });

    ports.forEach((port) => {
      port.inventory -= port.demandPerDay * settings.demandScale;
      if (port.inventory < 0) {
        stockoutPenalty += Math.abs(port.inventory) * settings.stockoutPenalty;
        shortages += 1;
      } else if (port.inventory >= port.inventoryMin) {
        serviceLevelHits += 1;
      }
      holdingCost += Math.max(0, port.inventory) * settings.holdingCost;
    });

    let decision = "监测库存变化";
    let reason = "系统先推进一天需求消耗，再决定是否需要改派船舶。";
    let altStrategy = `若改用“${policyLabel(settings.comparePolicy)}”，优先序会重新按库存风险和航程组合排序。`;

    if (vessel.state === "sailing") {
      vessel.travelRemaining -= vessel.speed;
      sailingCost += settings.sailingCost * vessel.speed;
      decision = `船舶继续驶向 ${vessel.target}`;
      reason = `当前航程尚未完成，还需 ${Math.max(0, vessel.travelRemaining).toFixed(1)} 天。`;
      if (vessel.travelRemaining <= 0) {
        vessel.location = vessel.target;
        vessel.state = "berthed";
        vessel.target = null;
      }
    }

    const currentPort = ports.find((port) => port.id === vessel.location);
    if (vessel.state === "berthed" && currentPort) {
      if (currentPort.id === "P1") {
        const pickup = Math.min(vessel.capacity - vessel.load, 52);
        vessel.load += pickup;
        currentPort.inventory = Math.max(currentPort.inventoryMin, currentPort.inventory - pickup * 0.35);
        decision = pickup > 0 ? `在 ${currentPort.id} 补货 ${pickup.toFixed(0)} 单位` : `在 ${currentPort.id} 待命`;
        reason = pickup > 0 ? "补货港承担上游供给，装货后再前往风险港口。" : "当前已接近满载，无需继续补货。";
      } else {
        const deficit = Math.max(0, currentPort.inventoryMax * 0.78 - currentPort.inventory);
        const deliver = Math.min(vessel.load, deficit, 58);
        if (deliver > 0) {
          vessel.load -= deliver;
          currentPort.inventory += deliver;
          deliveredTotal += deliver;
          decision = `在 ${currentPort.id} 卸货 ${deliver.toFixed(0)} 单位`;
          reason = `${currentPort.id} 库存已接近安全线以下，当前优先补给可降低断供罚金。`;
          portCalls.push({ portId: currentPort.id, day, quantity: deliver });
        }
      }

      const candidates = ports
        .filter((port) => port.id !== vessel.location)
        .map((port) => ({ ...port, score: scorePort(port, vessel, policy) }))
        .sort((a, b) => a.score - b.score);
      const chosen = candidates[0];
      const altCandidates = ports
        .filter((port) => port.id !== vessel.location)
        .map((port) => ({ ...port, score: scorePort(port, vessel, settings.comparePolicy) }))
        .sort((a, b) => a.score - b.score);

      if (chosen && (chosen.inventory < chosen.inventoryMin * 1.6 || vessel.location === "P1")) {
        vessel.target = chosen.id;
        vessel.state = "sailing";
        vessel.travelRemaining = travelTime(vessel.location, chosen.id);
        decision = `${decision}，随后驶往 ${chosen.id}`;
        reason = `${chosen.id} 当前库存率为 ${(chosen.inventory / chosen.inventoryMin).toFixed(2)}，是本策略下最紧急的补给对象。`;
      }

      if (altCandidates[0]) {
        altStrategy = `若切到“${policyLabel(settings.comparePolicy)}”，下一站更可能选 ${altCandidates[0].id}。`;
      }
    }

    pushSnapshot(decision, reason, altStrategy);
    day += 1;
  }

  const averageLoad = deliveredTotal > 0 ? portCalls.reduce((sum, call) => sum + call.quantity, 0) / Math.max(1, portCalls.length) : 0;
  const serviceLevel = (serviceLevelHits / (ports.length * settings.horizonDays)) * 100;

  return {
    snapshots,
    duration: Math.max(1, settings.horizonDays),
    metrics: {
      sailingCost,
      stockoutPenalty,
      holdingCost,
      averageLoad,
      shortages,
      serviceLevel,
      portCalls: portCalls.length,
    },
  };
}

export function useInventoryRoutingDemo() {
  const settings = reactive({
    capacity: 120,
    speed: 1,
    safetyFactor: 1,
    demandScale: 1,
    stockoutPenalty: 3,
    sailingCost: 8,
    holdingCost: 0.1,
    portCallCost: 5,
    horizonDays: 14,
    policy: "rolling_horizon_greedy",
    comparePolicy: "lowest_ratio",
  });

  const playing = ref(true);
  const playbackSpeed = ref(1);
  const simulationTime = ref(0);
  const runtime = reactive({ frameId: 0, lastTick: 0 });

  const plan = computed(() => buildSimulation(settings, settings.policy));
  const comparePlan = computed(() => buildSimulation(settings, settings.comparePolicy));

  const currentIndex = computed(() => {
    const day = Math.min(Math.floor(simulationTime.value), plan.value.snapshots.length - 1);
    return Math.max(0, day);
  });
  const currentSnapshot = computed(() => plan.value.snapshots[currentIndex.value] || plan.value.snapshots[0]);
  const compareSnapshot = computed(() => comparePlan.value.snapshots[currentIndex.value] || comparePlan.value.snapshots[0]);

  const currentConstraints = computed(() => currentSnapshot.value?.constraints || []);

  const stageNarrative = computed(() => [
    {
      title: "当前状态",
      body: `第 ${currentSnapshot.value?.day ?? 0} 天，船舶位于 ${currentSnapshot.value?.vessel.location ?? "P1"}，载货量 ${currentSnapshot.value?.vessel.load?.toFixed(0) ?? 0}。`,
    },
    {
      title: "当前决策",
      body: currentSnapshot.value?.decision || "等待启动仿真。",
    },
    {
      title: "为何这样决策",
      body: currentSnapshot.value?.reason || "系统会同时看库存风险、航程和运力约束。",
    },
  ]);

  const explanationItems = computed(() => [
    { label: "当前状态", value: stageNarrative.value[0].body },
    { label: "当前决策", value: stageNarrative.value[1].body },
    { label: "若换另一策略", value: currentSnapshot.value?.altStrategy || "等待策略比较结果。" },
    { label: "对应模型", value: EQUATIONS[0] },
  ]);

  function singleStep() {
    simulationTime.value = Math.min(settings.horizonDays - 1, Math.floor(simulationTime.value) + 1);
    playing.value = false;
  }

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
      simulationTime.value += delta * playbackSpeed.value;
      if (simulationTime.value >= settings.horizonDays) {
        simulationTime.value = 0;
      }
    }
    runtime.frameId = window.requestAnimationFrame(tick);
  }

  watch(
    [
      () => settings.capacity,
      () => settings.speed,
      () => settings.demandScale,
      () => settings.stockoutPenalty,
      () => settings.policy,
      () => settings.comparePolicy,
    ],
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
    comparePlan,
    currentSnapshot,
    compareSnapshot,
    currentConstraints,
    stageNarrative,
    explanationItems,
    equations: EQUATIONS,
    playing,
    playbackSpeed,
    simulationTime,
    togglePlayback,
    resetPlayback,
    singleStep,
    formatDays,
    policyLabel,
  };
}
